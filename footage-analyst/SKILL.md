---
name: footage-analyst
description: >
  Transcribes video footage, identifies and clusters faces with interactive labeling,
  performs speaker diarization, and generates a self-contained HTML report. Uses a
  two-phase workflow: Phase 1 extracts faces fast so the user can label them in an
  interactive Cowork artifact; Phase 2 runs the full transcription + analysis with
  named faces applied. Use this skill whenever the user wants to transcribe a video,
  identify who appears in footage, see when people appear on screen, get a speaker
  breakdown, analyze interview footage, or produce a visual HTML summary of a clip.
  Trigger on phrases like "transcribe this footage", "who's in this video", "face ID",
  "identify people in this clip", "get a transcript", "speaker breakdown", "when does
  person X appear", "analyze this interview", or any request to extract text or identity
  information from a video file.
---

# Footage Analyst

<!-- Version 2.0.6 — hardened installer, MLX fast path, bundle index feed -->

You analyze video files using a two-phase workflow:
- **Phase 1**: Fast face extraction → interactive labeling artifact → user names each person
- **Phase 2**: Full transcription + diarization + analysis with named faces → HTML report

For transcription-ONLY requests there is a lighter fast path (see "Quick transcribe"
below) that skips the heavy face-recognition stack entirely.

Prefer files that live inside the user's project folder or connected drive. Do not ask
the user to drag footage into the chat. If they want to analyze a new clip, tell them
to place it in the project folder/drive first, then point Claude at that file path so
the transcript can feed the final footage index cleanly.

---

## ⚠️ Safety and privacy

- Never upload footage to any external service — all processing runs locally
- Face clustering groups faces by visual similarity only — it does not identify who anyone is
- The user can optionally label clusters in the HTML output after the fact
- Do not store or log face embeddings beyond the current session

---

## Step 0: Pre-flight (run BEFORE any installing)

```bash
echo "=== chip ===" && uname -m
echo "=== free disk ===" && df -h / | tail -1
echo "=== memory ===" && sysctl -n hw.memsize 2>/dev/null | awk '{print $1/1073741824 " GB"}'
```

- **Disk:** the full stack needs ~6 GB free (PyTorch ~2 GB + models). Under 10 GB free →
  warn the user before starting.
- **Chip:** `arm64` = Apple Silicon (everything fast); `x86_64` = Intel (everything works,
  2–4× slower — set expectations).
- **Set time expectations up front, in plain English:** "First-time setup downloads about
  4 GB and takes 10–20 minutes. You only ever do this once. After that, analyzing a clip
  takes a few minutes."

**This installer is resume-safe.** If the session dies or an install fails mid-way,
just run the Step 1 check again — everything already installed shows "ok" and you skip
straight to whatever's missing. Nothing is ever installed twice. Tell the user this if
anything crashes: no harm done, we pick up where we left off.

---

## Step 1: Dependency check and setup

Run the full check first so you know exactly what's missing before touching anything else:

```bash
echo "=== ffmpeg ===" && ffmpeg -version 2>&1 | head -1 || echo "MISSING"
echo "=== brew ===" && brew --version 2>&1 | head -1 || echo "MISSING"
echo "=== python3 ===" && python3 --version 2>&1
echo "=== whisper ===" && python3 -c "import whisper; print('ok')" 2>&1
echo "=== face_recognition ===" && python3 -c "import face_recognition; print('ok')" 2>&1
echo "=== sklearn ===" && python3 -c "from sklearn.cluster import DBSCAN; print('ok')" 2>&1
echo "=== PIL ===" && python3 -c "import PIL; print('ok')" 2>&1
echo "=== pyannote ===" && python3 -c "import pyannote.audio; print('ok')" 2>&1
echo "=== cmake ===" && cmake --version 2>&1 | head -1 || echo "MISSING (needed for dlib)"
```

Read the output carefully. Then follow the install path below for whatever is missing.

---

## Installing missing dependencies (Cowork/macOS)

**In Cowork mode, attempt each install via bash automatically.** After each install,
re-run the check command to confirm success before moving to the next step.
If a command fails, show the exact error to the user and offer the manual fallback.

---

### A. Homebrew (required first if missing)

Homebrew is the macOS package manager. Check if it's installed:

```bash
brew --version 2>&1
```

If missing, **in Cowork run**:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Manual fallback** (if bash install fails or user prefers):
1. Open Safari or Chrome
2. Go to **https://brew.sh**
3. Copy the install command shown on the page (starts with `/bin/bash -c ...`)
4. Open Terminal (Cmd+Space → type "Terminal" → press Enter)
5. Paste the command and press Enter
6. Follow the prompts — it will ask for your Mac password

---

### B. ffmpeg (video processing)

**In Cowork run**:
```bash
brew install ffmpeg
```

This takes 1–3 minutes. Verify after:
```bash
ffmpeg -version 2>&1 | head -1
```

**Manual fallback**:
1. Open Terminal
2. Paste: `brew install ffmpeg`
3. Press Enter and wait

---

### C. cmake (required to build dlib, which face_recognition needs)

**In Cowork run**:
```bash
brew install cmake
```

Verify: `cmake --version 2>&1 | head -1`

---

### D. Core Python packages

**In Cowork run** (install one at a time so failures are isolated):

```bash
pip3 install numpy --break-system-packages
```
```bash
pip3 install Pillow --break-system-packages
```
```bash
pip3 install scikit-learn --break-system-packages
```
```bash
pip3 install openai-whisper --break-system-packages
```

Note: `openai-whisper` will pull in PyTorch (~2GB download). This is normal and expected.
It may take 5–10 minutes on a typical connection. Let the user know before starting.

```bash
pip3 install face-recognition --break-system-packages
```

Note: `face-recognition` compiles `dlib` from source — takes 3–5 minutes the first time.
cmake must be installed first (Step C).

Verify all at once:
```bash
python3 -c "import whisper, face_recognition, sklearn, PIL, numpy; print('all ok')"
```

**Manual fallback** (if pip3 fails):
1. Open Terminal
2. Run each pip3 command above one at a time
3. If you get a "externally-managed-environment" error, add `--break-system-packages` to the end

---

### E. pyannote.audio (speaker diarization — optional)

This requires a free HuggingFace account. Skip it if the user only wants transcription.

**Explain it to the user in plain English first:** "Speaker separation (figuring out
who's talking when) uses a free AI model from HuggingFace — think of it as a public
library for AI tools. You'll make a free account and click 'agree' on the tool's usage
page — it's a usage agreement, not legal paperwork. Takes about 2 minutes, and you only
ever do it once." Avoid the word "diarization" with users — say "speaker separation."

**Step E1 — Install the package**:
```bash
pip3 install pyannote.audio --break-system-packages
```

**Step E2 — Create a HuggingFace account** (if they don't have one):
1. Go to **https://huggingface.co/join**
2. Sign up with email (free)
3. Verify your email

**Step E3 — Accept the model license**:
1. Go to **https://huggingface.co/pyannote/speaker-diarization-3.1**
2. Log in if prompted
3. Scroll to the model card and click **"Agree and access repository"**
4. Also accept: **https://huggingface.co/pyannote/segmentation-3.0** (same steps)

**Step E4 — Get your access token**:
1. Go to **https://huggingface.co/settings/tokens**
2. Click **"New token"**
3. Name it anything (e.g. "footage-analyst"), role: **Read**
4. Click **Generate** and copy the token (starts with `hf_`)
5. Paste it here — you'll pass it to the script as `--hf-token "hf_xxxx"`

---

### Troubleshooting common errors

| Error | Fix |
|-------|-----|
| `command not found: brew` | Homebrew not installed — see Step A |
| `cmake not found` | Run `brew install cmake` before installing face-recognition |
| `externally-managed-environment` | Add `--break-system-packages` to pip3 command |
| `ERROR: Could not install packages due to an OSError: No space left on device` | Free up disk space — you need ~4GB free. Check with `df -h /` |
| `dlib build fails` | Make sure cmake is installed. Try `pip3 install dlib --break-system-packages` first, then retry face-recognition |
| HF token error in pyannote | Make sure you accepted BOTH model licenses (Step E3) |
| `torch` install hangs | It's downloading ~2GB — just wait. Normal. |

---

## Quick transcribe (fast path — no faces, no heavy stack)

When the user ONLY wants a transcript ("just transcribe this", "get me the text",
no face/speaker asks), skip the full pipeline. On Apple Silicon (`uname -m` → arm64),
prefer **mlx-whisper** — it runs on the Mac's GPU, is roughly 10× realtime, and does
NOT need the 2 GB PyTorch download:

```bash
pip3 install mlx-whisper --break-system-packages   # small install, Apple Silicon only
mlx_whisper "/path/to/clip.mov" --output-dir "/path/to/out" --output-format json \
  --model mlx-community/whisper-base-mlx
```

The JSON output is `{"segments": [...]}` with `start`/`end`/`text` per segment (no
`speaker` field — speaker separation is skipped on this fast path). The footage-index
`ingest-transcript` command accepts this file directly. Present the transcript, then
feed it to the index (Step 6) like any other result. On Intel Macs, or if mlx-whisper
fails, fall back to `openai-whisper` from the main install path. Either way the user
gets the same transcript; only speed differs.

---

## Phase 1: Fast face extraction

Once dependencies check out, run Phase 1 — this takes 1–3 minutes per clip:

```bash
python3 <skill_dir>/scripts/extract_faces.py \
  --input "/path/to/video.mp4" \
  --output "/path/to/output_dir" \
  [--frame-interval 3]           # seconds between frame samples (default: 3)
  [--face-threshold 0.55]        # clustering distance threshold (default: 0.55)
```

This outputs `<output_dir>/faces.json` — face crops and cluster metadata.
When it finishes, proceed immediately to Step 3 (face labeling artifact).

---

## Step 3: Face labeling — show the Cowork artifact

After Phase 1 completes, read the `faces.json` file and render an interactive labeling
panel as a Cowork artifact using `show_widget`.

Read the faces JSON:
```python
import json
data = json.load(open("/path/to/output_dir/faces.json"))
clusters = data['clusters']
```

Then call `mcp__visualize__show_widget` with HTML that:
1. Shows each face cluster as a card with the base64 face photo
2. Has an editable text input for each person's name
3. Pre-fills "Person_A", "Person_B", etc. as placeholder
4. Has a "Submit Labels" button that calls `sendPrompt(...)` with the label JSON

The widget HTML template (adapt to actual clusters):

```html
<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: system-ui; background: #1a1a1a; color: #eee; padding: 20px; margin: 0; }
  h2 { color: #fff; margin-bottom: 4px; }
  .sub { color: #888; font-size: 13px; margin-bottom: 24px; }
  .grid { display: flex; flex-wrap: wrap; gap: 16px; }
  .card { background: #2a2a2a; border-radius: 10px; padding: 16px; width: 160px; }
  .card img { width: 128px; height: 128px; object-fit: cover; border-radius: 8px; display: block; margin: 0 auto 10px; }
  .card .placeholder { width: 128px; height: 128px; background: #444; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 32px; margin: 0 auto 10px; }
  .card label { font-size: 11px; color: #888; display: block; margin-bottom: 4px; }
  .card .meta { font-size: 11px; color: #666; margin-top: 6px; }
  input[type=text] { width: 100%; box-sizing: border-box; background: #333; border: 1px solid #555; color: #fff; border-radius: 6px; padding: 6px 8px; font-size: 13px; }
  input[type=text]:focus { outline: none; border-color: #888; }
  .submit-btn { margin-top: 24px; background: #e67e22; color: #fff; border: none; border-radius: 8px; padding: 12px 28px; font-size: 15px; font-weight: 600; cursor: pointer; }
  .submit-btn:hover { background: #d35400; }
</style>
</head>
<body>
  <h2>👤 Label Faces</h2>
  <p class="sub">Type a name for each person. Leave blank to keep the auto-label.</p>
  <div class="grid" id="grid"></div>
  <br>
  <button class="submit-btn" onclick="submitLabels()">Submit Labels →</button>

<script>
const clusters = CLUSTERS_JSON_PLACEHOLDER;

const grid = document.getElementById('grid');
clusters.forEach(c => {
  const card = document.createElement('div');
  card.className = 'card';
  if (c.best_crop_base64) {
    card.innerHTML = `<img src="data:image/jpeg;base64,${c.best_crop_base64}" />`;
  } else {
    card.innerHTML = `<div class="placeholder">👤</div>`;
  }
  card.innerHTML += `
    <label>${c.label}</label>
    <input type="text" id="name_${c.label}" placeholder="${c.label}" />
    <div class="meta">${c.appearance_count} appearances · ${formatTC(c.first_seen)}–${formatTC(c.last_seen)}</div>
  `;
  grid.appendChild(card);
});

function formatTC(s) {
  const m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return `${m}:${String(sec).padStart(2,'0')}`;
}

function submitLabels() {
  const labels = {};
  clusters.forEach(c => {
    const val = document.getElementById('name_' + c.label).value.trim();
    labels[c.label.toLowerCase()] = val || c.label;
  });
  const msg = 'FACE_LABELS:' + JSON.stringify(labels);
  sendPrompt(msg);
}
</script>
</body>
</html>
```

Replace `CLUSTERS_JSON_PLACEHOLDER` with the actual clusters array serialized as JSON
(omit the base64 data from the placeholder — the actual base64 goes in the rendered widget,
not the placeholder text in SKILL.md).

**IMPORTANT:** Call `mcp__visualize__read_me` with `modules: ["interactive"]` BEFORE calling
`show_widget` the first time in a session — this loads the CSS variables you need.

---

## Step 4: Receive labels and run Phase 2

Wait for the user to submit the face-labeling artifact. The message will start with
`FACE_LABELS:` followed by a JSON object, e.g.:

```
FACE_LABELS:{"person_a":"John Smith","person_b":"Sarah Jones","person_c":"Person_C"}
```

Parse the labels, then run Phase 2 — the full analysis:

```bash
python3 <skill_dir>/scripts/analyze_footage.py \
  --input "/path/to/video.mp4" \
  --output "/path/to/output_dir" \
  --labels '{"person_a": "John Smith", "person_b": "Sarah Jones"}' \
  [--hf-token "hf_xxxx"]        # optional, for speaker diarization
  [--frame-interval 2]           # default: 2
  [--whisper-model base]         # tiny/base/small/medium/large (default: base)
```

**Output location rule:** `--output` must point OUTSIDE the footage tree — never
inside `01_footage/` and never inside a card folder (the scripts refuse and explain
if it does). Good choices: the project's `09_exports/` or a separate analysis folder.

**Whisper model sizes:**
- `tiny` — fastest, least accurate (~1GB RAM)
- `base` — good default (~1GB RAM)
- `small` — better accuracy (~2GB RAM)
- `medium` — strong accuracy (~5GB RAM)
- `large` — best quality (~10GB RAM)

---

## Step 5: Report results

After Phase 2 finishes, tell the user:
- Duration processed, transcript segment count
- Named faces found (with the labels they provided)
- Speakers detected (if diarization ran)
- Path to `report.html`

Present the HTML report to the user: `open "/path/to/report.html"` works everywhere
on macOS; if the environment offers a file-presentation tool, use that as well.

---

## Step 6: Feed the footage index (if footage-index is installed)

Phase 2 writes `transcript.json` in the output directory — exactly the format the
**footage-index** skill ingests. In the full AOD Footage Pack workflow, analysis feeds
the final index step. Do not show the user an internal handoff packet; just summarize
the useful result ("transcript ready", "faces labeled", "ready to index").

If the index skill is installed, offer:
"Ready for me to index this folder so you can chat with these transcripts?"

(`<footage-index_skill_dir>` below means the footage-index skill's own install
directory — you know it if that skill is active in this session; otherwise locate
its `scripts/footage_index.py` under the same skills folder this skill lives in.)

```bash
python3 <footage-index_skill_dir>/scripts/footage_index.py ingest-transcript \
  --file-path "/path/to/video.mp4" \
  --json "/path/to/output_dir/transcript.json"
```

Then add a person tag for each labeled face:

```bash
python3 <footage-index_skill_dir>/scripts/footage_index.py tag \
  --file-path "/path/to/video.mp4" --kind person --value "Sarah Jones"
```

(If the clip's drive isn't indexed yet, run `ingest-path` on the project first —
see the footage-index skill.) After this, tell the user plainly that the folder is
indexed and they can ask "where does Sarah talk about X" months from now and get this
clip + timecode back.

---

## What the HTML report contains

- **Header bar** — video filename, duration, processing date, quick stats
- **Transcript panel** — full timestamped transcript, color-coded by speaker,
  clickable timecodes
- **Face timeline** — horizontal bar showing each named person's on-screen appearances
- **Face thumbnails grid** — best face crop per person, with their name, screen time, timecodes
- **Speaker breakdown** — speaking time per speaker as a bar chart
- Dark post-production aesthetic. Fully self-contained. No external dependencies.
