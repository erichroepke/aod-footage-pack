#!/usr/bin/env python3
"""
analyze_footage.py
Transcribes video, clusters faces, runs speaker diarization,
and generates a self-contained HTML report.
"""

import argparse
import base64
import html as html_lib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

# ── helpers ──────────────────────────────────────────────────────────────────

def fmt_time(seconds):
    """Format seconds as HH:MM:SS or MM:SS."""
    td = timedelta(seconds=int(seconds))
    h, rem = divmod(int(td.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def run(cmd, desc=""):
    """Run a command without shell interpolation, print progress, raise on failure."""
    print(f"  ▸ {desc or ' '.join(str(part) for part in cmd[:4])}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ERROR: {result.stderr[:300]}")
        raise RuntimeError(f"Command failed: {cmd}")
    return result.stdout.strip()

def img_to_b64(path):
    """Read an image file and return a base64 data URI."""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lstrip(".").lower()
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png"}.get(ext, "jpeg")
    return f"data:image/{mime};base64,{data}"

CARD_MARKERS = {'DCIM', 'PRIVATE', 'CONTENTS', 'CLIPS', 'XDROOT', 'M4ROOT',
                'AVCHD', 'BDMV'}

def output_path_is_unsafe(output_dir):
    parts = [p.upper() for p in output_dir.resolve().parts]
    if '01_FOOTAGE' in parts:
        return True
    for i, part in enumerate(parts):
        # macOS temp paths resolve under /private/var; that is not a camera card.
        if part == 'PRIVATE' and i == 1:
            continue
        if part in CARD_MARKERS:
            return True
    return False

# ── 1. extract audio ─────────────────────────────────────────────────────────

def extract_audio(video_path, work_dir):
    audio_path = work_dir / "audio.wav"
    run(
        ['ffmpeg', '-y', '-i', str(video_path), '-ac', '1', '-ar', '16000',
         '-vn', str(audio_path)],
        "Extracting audio"
    )
    return audio_path

def get_duration(video_path):
    out = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(video_path)],
        capture_output=True, text=True
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0

# ── 2. transcription ─────────────────────────────────────────────────────────

def transcribe(audio_path, model_name="base"):
    print(f"  ▸ Transcribing with Whisper ({model_name})...")
    try:
        import whisper
    except ImportError:
        print("    whisper not installed. Run: pip install openai-whisper")
        sys.exit(1)

    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_path), verbose=False, word_timestamps=True)

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
            "speaker": None,  # filled in by diarization
        })
    return segments

# ── 3. speaker diarization ───────────────────────────────────────────────────

def diarize(audio_path, hf_token):
    print("  ▸ Running speaker diarization (pyannote)...")
    try:
        from pyannote.audio import Pipeline
    except ImportError:
        print("    pyannote.audio not installed — skipping diarization.")
        return []

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token
    )
    diarization = pipeline(str(audio_path))
    turns = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        })
    return turns

def assign_speakers(segments, turns):
    """Assign speaker labels to transcript segments by overlap."""
    if not turns:
        return segments
    for seg in segments:
        mid = (seg["start"] + seg["end"]) / 2
        best = None
        best_overlap = 0
        for turn in turns:
            overlap = min(seg["end"], turn["end"]) - max(seg["start"], turn["start"])
            if overlap > best_overlap:
                best_overlap = overlap
                best = turn["speaker"]
        seg["speaker"] = best or "Unknown"
    return segments

# ── 4. face detection + clustering ───────────────────────────────────────────

def extract_frames(video_path, work_dir, interval=2):
    frames_dir = work_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    run(
        ['ffmpeg', '-y', '-i', str(video_path), '-vf', f'fps=1/{interval}',
         str(frames_dir / 'frame_%06d.jpg')],
        f"Extracting frames (every {interval}s)"
    )
    frames = sorted(frames_dir.glob("frame_*.jpg"))
    return frames, frames_dir

def detect_and_cluster_faces(frames, interval, face_threshold=0.55):
    """
    Detect faces in each frame, get 128-d embeddings,
    cluster with DBSCAN into person identities.
    Returns list of dicts: {person_id, timecode, frame_path, face_crop_path, encoding}
    """
    print("  ▸ Detecting faces...")
    try:
        import face_recognition
        import numpy as np
        from sklearn.cluster import DBSCAN
        from PIL import Image
    except ImportError as e:
        print(f"    Missing package: {e}. Skipping face analysis.")
        return {}, {}

    all_encodings = []
    all_meta = []  # (timecode, frame_path, top, right, bottom, left)

    for i, frame_path in enumerate(frames):
        timecode = i * interval
        img = face_recognition.load_image_file(str(frame_path))
        locations = face_recognition.face_locations(img, model="hog")
        encodings = face_recognition.face_encodings(img, locations)
        for (top, right, bottom, left), enc in zip(locations, encodings):
            all_encodings.append(enc)
            all_meta.append((timecode, frame_path, top, right, bottom, left))

    if not all_encodings:
        print("    No faces detected.")
        return {}, {}

    print(f"    Detected {len(all_encodings)} face instances across {len(frames)} frames")
    print("  ▸ Clustering faces...")

    import numpy as np
    X = np.array(all_encodings)
    clustering = DBSCAN(eps=face_threshold, min_samples=2, metric="euclidean").fit(X)
    labels = clustering.labels_

    # Group by cluster label
    clusters = defaultdict(list)
    for label, meta in zip(labels, all_meta):
        if label == -1:
            continue  # noise / one-off face
        clusters[label].append(meta)

    # For each cluster, pick the best crop (largest face area) as the thumbnail
    persons = {}
    faces_dir = frames[0].parent.parent / "faces"
    faces_dir.mkdir(exist_ok=True)

    for label, appearances in clusters.items():
        person_id = f"person_{chr(65 + label)}"  # Person_A, Person_B, ...
        # Sort by face area descending, pick best
        best = max(appearances, key=lambda m: (m[4] - m[2]) * (m[3] - m[5]))
        t, fpath, top, right, bottom, left = best

        # Crop and save face thumbnail
        from PIL import Image
        img = Image.open(str(fpath))
        pad = 20
        crop = img.crop((
            max(0, left - pad), max(0, top - pad),
            min(img.width, right + pad), min(img.height, bottom + pad)
        ))
        thumb_path = faces_dir / f"{person_id}.jpg"
        crop.save(str(thumb_path))

        timecodes = sorted(set(m[0] for m in appearances))
        persons[person_id] = {
            "id": person_id,
            "label": person_id.replace("_", " ").title(),
            "timecodes": timecodes,
            "thumb_path": str(thumb_path),
            "count": len(appearances),
        }

    print(f"    Found {len(persons)} distinct person(s)")
    return persons, faces_dir

# ── 5. HTML generation ────────────────────────────────────────────────────────

SPEAKER_COLORS = [
    "#4fc3f7", "#81c784", "#ffb74d", "#f06292",
    "#ce93d8", "#80cbc4", "#fff176", "#ff8a65",
]

def esc(value):
    return html_lib.escape(str(value), quote=True)

def build_html(video_name, duration, segments, persons, labels, output_path):
    print("  ▸ Building HTML report...")

    # Speaker color map
    all_speakers = sorted(set(s["speaker"] for s in segments if s["speaker"]))
    speaker_color = {sp: SPEAKER_COLORS[i % len(SPEAKER_COLORS)]
                     for i, sp in enumerate(all_speakers)}

    # Speaking time per speaker
    speaker_time = defaultdict(float)
    for seg in segments:
        sp = seg["speaker"] or "Unknown"
        speaker_time[sp] += seg["end"] - seg["start"]

    # Embed face thumbnails as base64
    person_thumbs = {}
    for pid, p in persons.items():
        if os.path.exists(p["thumb_path"]):
            person_thumbs[pid] = img_to_b64(p["thumb_path"])

    # Build transcript HTML
    transcript_html = ""
    for seg in segments:
        sp = seg["speaker"] or ""
        color = speaker_color.get(sp, "#aaa")
        label = labels.get(sp, sp) if sp else ""
        label_html = esc(label)
        text_html = esc(seg['text'])
        ts = fmt_time(seg["start"])
        transcript_html += f"""
        <div class="seg" data-start="{seg['start']:.1f}">
          <span class="ts" onclick="copyTS('{ts}')" title="Copy timecode">{ts}</span>
          {f'<span class="spk" style="color:{color}">{label_html}</span>' if label else ""}
          <span class="txt">{text_html}</span>
        </div>"""

    # Build face cards HTML
    face_cards_html = ""
    for pid, p in sorted(persons.items()):
        name = labels.get(pid, p["label"])
        name_html = esc(name)
        pid_html = esc(pid)
        thumb = person_thumbs.get(pid, "")
        tc_list = " · ".join(fmt_time(t) for t in p["timecodes"][:12])
        if len(p["timecodes"]) > 12:
            tc_list += f" … +{len(p['timecodes']) - 12} more"
        screen_time = fmt_time(len(p["timecodes"]) * 2)  # approx
        img_tag = f'<img src="{thumb}" alt="{name_html}">' if thumb else '<div class="no-thumb">?</div>'
        face_cards_html += f"""
        <div class="face-card" id="card-{pid_html}">
          <div class="face-thumb">{img_tag}</div>
          <div class="face-info">
            <input class="face-name" value="{name_html}" data-pid="{pid_html}"
                   onchange="updateLabel(this)" />
            <div class="face-time">~{screen_time} on screen · {p['count']} detections</div>
            <div class="face-tcs">{tc_list}</div>
          </div>
        </div>"""

    # Build face timeline HTML
    timeline_html = ""
    for pid, p in sorted(persons.items()):
        name = labels.get(pid, p["label"])
        name_html = esc(name)
        pid_html = esc(pid)
        color = SPEAKER_COLORS[list(persons.keys()).index(pid) % len(SPEAKER_COLORS)]
        blocks = ""
        for tc in p["timecodes"]:
            pct = (tc / duration * 100) if duration > 0 else 0
            blocks += f'<div class="tl-block" style="left:{pct:.2f}%;width:0.8%" title="{fmt_time(tc)}"></div>'
        timeline_html += f"""
        <div class="tl-row">
          <div class="tl-label" id="tl-{pid_html}">{name_html}</div>
          <div class="tl-track" style="--color:{color}">{blocks}</div>
        </div>"""

    # Speaker breakdown bars
    spk_bars_html = ""
    total_time = sum(speaker_time.values()) or 1
    for sp, t in sorted(speaker_time.items(), key=lambda x: -x[1]):
        pct = t / total_time * 100
        color = speaker_color.get(sp, "#aaa")
        name = labels.get(sp, sp)
        name_html = esc(name)
        spk_bars_html += f"""
        <div class="spk-bar-row">
          <div class="spk-bar-label" style="color:{color}">{name_html}</div>
          <div class="spk-bar-track">
            <div class="spk-bar-fill" style="width:{pct:.1f}%;background:{color}"></div>
          </div>
          <div class="spk-bar-pct">{pct:.0f}% · {fmt_time(t)}</div>
        </div>"""

    word_count = sum(len(s["text"].split()) for s in segments)
    n_speakers = len(all_speakers)
    n_faces = len(persons)
    video_name_html = esc(video_name)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Footage Analysis — {video_name_html}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #111; color: #e0e0e0; font-family: -apple-system, "Helvetica Neue", sans-serif;
         font-size: 14px; line-height: 1.5; }}
  a {{ color: #4fc3f7; }}
  h2 {{ font-size: 13px; text-transform: uppercase; letter-spacing: .08em;
       color: #888; margin-bottom: 12px; }}
  .header {{ background: #1a1a1a; border-bottom: 1px solid #2a2a2a; padding: 16px 24px;
             display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }}
  .header h1 {{ font-size: 16px; font-weight: 600; color: #fff; }}
  .stat {{ background: #222; border-radius: 6px; padding: 6px 12px; font-size: 12px; color: #aaa; }}
  .stat strong {{ color: #fff; display: block; font-size: 18px; }}
  .main {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; height: calc(100vh - 64px); }}
  .panel {{ padding: 20px 24px; overflow-y: auto; border-right: 1px solid #1e1e1e; }}
  .panel:last-child {{ border-right: none; }}
  /* transcript */
  .seg {{ display: flex; gap: 10px; padding: 5px 0; border-bottom: 1px solid #1a1a1a;
          align-items: baseline; }}
  .ts {{ color: #4fc3f7; font-family: monospace; font-size: 12px; white-space: nowrap;
         cursor: pointer; min-width: 44px; }}
  .ts:hover {{ color: #81d4fa; text-decoration: underline; }}
  .spk {{ font-size: 11px; font-weight: 600; min-width: 70px; white-space: nowrap; }}
  .txt {{ color: #ddd; flex: 1; }}
  /* face cards */
  .face-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 12px; margin-bottom: 24px; }}
  .face-card {{ background: #1a1a1a; border-radius: 8px; padding: 12px;
                display: flex; gap: 12px; align-items: flex-start; }}
  .face-thumb img, .no-thumb {{ width: 60px; height: 60px; border-radius: 50%;
                                object-fit: cover; background: #333; display: flex;
                                align-items: center; justify-content: center;
                                font-size: 24px; color: #666; flex-shrink: 0; }}
  .face-name {{ background: transparent; border: none; border-bottom: 1px solid #333;
                color: #fff; font-size: 13px; font-weight: 600; width: 100%; padding: 2px 0;
                outline: none; }}
  .face-name:focus {{ border-bottom-color: #4fc3f7; }}
  .face-time {{ color: #888; font-size: 11px; margin-top: 4px; }}
  .face-tcs {{ color: #555; font-size: 11px; margin-top: 4px; font-family: monospace;
               line-height: 1.6; }}
  /* timeline */
  .tl-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
  .tl-label {{ width: 100px; font-size: 12px; color: #aaa; text-align: right;
               white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .tl-track {{ flex: 1; height: 16px; background: #1e1e1e; border-radius: 4px;
               position: relative; }}
  .tl-block {{ position: absolute; height: 100%; background: var(--color, #4fc3f7);
               border-radius: 2px; opacity: 0.85; }}
  /* speaker bars */
  .spk-bar-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
  .spk-bar-label {{ width: 90px; font-size: 12px; white-space: nowrap;
                    overflow: hidden; text-overflow: ellipsis; }}
  .spk-bar-track {{ flex: 1; height: 10px; background: #1e1e1e; border-radius: 5px; overflow: hidden; }}
  .spk-bar-fill {{ height: 100%; border-radius: 5px; transition: width .3s; }}
  .spk-bar-pct {{ font-size: 11px; color: #888; white-space: nowrap; }}
  /* section */
  .section {{ margin-bottom: 28px; }}
  .section-header {{ cursor: pointer; display: flex; align-items: center; gap: 8px;
                     padding: 8px 0; border-bottom: 1px solid #222; margin-bottom: 12px; }}
  .section-header:hover h2 {{ color: #ccc; }}
  .chevron {{ color: #555; transition: transform .2s; }}
  .collapsed .chevron {{ transform: rotate(-90deg); }}
  .section-body.hidden {{ display: none; }}
  /* toast */
  #toast {{ position: fixed; bottom: 20px; right: 20px; background: #333;
            color: #fff; padding: 8px 16px; border-radius: 6px; font-size: 12px;
            opacity: 0; transition: opacity .2s; pointer-events: none; z-index: 999; }}
  #toast.show {{ opacity: 1; }}
  @media (max-width: 800px) {{ .main {{ grid-template-columns: 1fr; height: auto; }} }}
</style>
</head>
<body>

<div class="header">
  <h1>📹 {video_name_html}</h1>
  <div class="stat"><strong>{fmt_time(duration)}</strong>Duration</div>
  <div class="stat"><strong>{word_count:,}</strong>Words</div>
  <div class="stat"><strong>{n_speakers}</strong>Speaker{'' if n_speakers==1 else 's'}</div>
  <div class="stat"><strong>{n_faces}</strong>Face{'' if n_faces==1 else 's'} detected</div>
  <div class="stat"><strong>{len(segments)}</strong>Segments</div>
</div>

<div class="main">

  <!-- LEFT: transcript + speaker breakdown -->
  <div class="panel">

    <div class="section" id="sec-transcript">
      <div class="section-header" onclick="toggle('sec-transcript')">
        <h2>📝 Transcript</h2><span class="chevron">▾</span>
      </div>
      <div class="section-body" id="body-sec-transcript">
        {transcript_html if transcript_html else '<p style="color:#666">No transcript generated.</p>'}
      </div>
    </div>

    <div class="section" id="sec-speakers">
      <div class="section-header" onclick="toggle('sec-speakers')">
        <h2>🎙 Speaker breakdown</h2><span class="chevron">▾</span>
      </div>
      <div class="section-body" id="body-sec-speakers">
        {spk_bars_html if spk_bars_html else '<p style="color:#666">No speaker data (diarization not run).</p>'}
      </div>
    </div>

  </div>

  <!-- RIGHT: face thumbnails + timeline -->
  <div class="panel">

    <div class="section" id="sec-faces">
      <div class="section-header" onclick="toggle('sec-faces')">
        <h2>👤 People detected</h2><span class="chevron">▾</span>
      </div>
      <div class="section-body" id="body-sec-faces">
        {'<div class="face-grid">' + face_cards_html + '</div>' if face_cards_html
         else '<p style="color:#666">No faces detected.</p>'}
      </div>
    </div>

    <div class="section" id="sec-timeline">
      <div class="section-header" onclick="toggle('sec-timeline')">
        <h2>📊 Appearance timeline</h2><span class="chevron">▾</span>
      </div>
      <div class="section-body" id="body-sec-timeline">
        {timeline_html if timeline_html
         else '<p style="color:#666">No face timeline data.</p>'}
      </div>
    </div>

  </div>

</div>

<div id="toast"></div>

<script>
function toggle(id) {{
  const sec = document.getElementById(id);
  const body = document.getElementById('body-' + id);
  sec.classList.toggle('collapsed');
  body.classList.toggle('hidden');
}}

function copyTS(ts) {{
  navigator.clipboard.writeText(ts).catch(() => {{}});
  const t = document.getElementById('toast');
  t.textContent = 'Copied ' + ts;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 1500);
}}

function updateLabel(input) {{
  const pid = input.dataset.pid;
  const val = input.value;
  // Update face timeline label if present
  const tlLabel = document.getElementById('tl-' + pid);
  if (tlLabel) tlLabel.textContent = val;
}}
</script>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ▸ HTML report saved to: {output_path}")

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Analyze footage: transcribe, face cluster, HTML report")
    parser.add_argument("--input", required=True, help="Path to video file")
    parser.add_argument("--output", required=True, help="Output directory for results")
    parser.add_argument("--hf-token", default=None, help="HuggingFace token for pyannote diarization")
    parser.add_argument("--frame-interval", type=int, default=2, help="Seconds between frame samples (default: 2)")
    parser.add_argument("--whisper-model", default="base", help="Whisper model size: tiny/base/small/medium/large")
    parser.add_argument("--face-threshold", type=float, default=0.55, help="DBSCAN distance threshold for face clustering")
    parser.add_argument("--labels", default="{}", help='JSON string mapping person_id/speaker to display name')
    args = parser.parse_args()

    video_path = Path(args.input)
    output_dir = Path(args.output)

    # SAFETY FENCE: outputs must never land inside footage or card structures.
    # This script writes a run-specific temp dir and runs ffmpeg with -y;
    # pointing it at camera originals must be impossible.
    if output_path_is_unsafe(output_dir):
        print("❌ Refusing: --output points inside a footage/card folder "
              f"({args.output}).")
        print("   Choose an output OUTSIDE your footage — e.g. the project's "
              "09_exports/ folder or a separate analysis folder.")
        sys.exit(2)

    labels = json.loads(args.labels)
    video_name = video_path.name
    duration = get_duration(video_path)

    print(f"\n🎬 Analyzing: {video_name} ({fmt_time(duration)})\n")

    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = Path(tempfile.mkdtemp(prefix="_work-", dir=output_dir))
    try:
        # 1. Audio extraction + transcription
        print("── Transcription ──────────────────────────────")
        audio_path = extract_audio(video_path, work_dir)
        segments = transcribe(audio_path, args.whisper_model)
        print(f"  ✓ {len(segments)} segments, ~{sum(len(s['text'].split()) for s in segments):,} words")

        # 2. Speaker diarization
        print("\n── Speaker diarization ────────────────────────")
        if args.hf_token:
            turns = diarize(audio_path, args.hf_token)
            segments = assign_speakers(segments, turns)
            n_speakers = len(set(t["speaker"] for t in turns))
            print(f"  ✓ {n_speakers} speaker(s) detected")
        else:
            print("  ℹ  No HF token provided — skipping diarization")

        # 3. Face analysis
        print("\n── Face detection & clustering ────────────────")
        frames, frames_dir = extract_frames(video_path, work_dir, args.frame_interval)
        print(f"  ✓ {len(frames)} frames extracted")
        persons, _ = detect_and_cluster_faces(frames, args.frame_interval, args.face_threshold)

        # 4. Save transcript JSON (for reference)
        with open(output_dir / "transcript.json", "w") as f:
            json.dump(segments, f, indent=2)

        # 5. Generate HTML
        print("\n── Generating HTML report ─────────────────────")
        html_path = output_dir / "report.html"
        build_html(video_name, duration, segments, persons, labels, html_path)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    print(f"\n✅ Done!\n")
    print(f"   HTML report:  {html_path}")
    print(f"   Transcript:   {output_dir / 'transcript.json'}")
    print(f"   Faces found:  {len(persons)}")
    print(f"   Segments:     {len(segments)}")

if __name__ == "__main__":
    main()
