#!/usr/bin/env python3
"""
extract_faces.py
Phase 1: Fast face extraction and clustering only.
Outputs a JSON file with face crops (base64) and cluster metadata
so the user can label people before running the full analysis.

Usage:
    python3 extract_faces.py \
        --input /path/to/video.mp4 \
        --output /path/to/output_dir \
        [--frame-interval 3] \
        [--face-threshold 0.55]

Output:
    <output_dir>/faces.json  — face crops + cluster info for labeling
    Prints a summary of detected clusters.
"""

import argparse
import base64
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def check_dependencies():
    missing = []
    for pkg in ['face_recognition', 'PIL', 'sklearn', 'numpy']:
        try:
            __import__(pkg if pkg != 'PIL' else 'PIL')
        except ImportError:
            missing.append(pkg)
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        if result.returncode != 0:
            missing.append('ffmpeg')
    except FileNotFoundError:
        missing.append('ffmpeg')
    return missing


def extract_frames(video_path, output_dir, interval=3):
    """Extract frames from video at given interval (seconds)."""
    frames_dir = Path(output_dir) / 'frames'
    frames_dir.mkdir(exist_ok=True)

    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-vf', f'fps=1/{interval}',
        '-q:v', '2',
        str(frames_dir / 'frame_%06d.jpg'),
        '-y', '-loglevel', 'error'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: ffmpeg failed: {result.stderr}")
        sys.exit(1)

    frames = sorted(frames_dir.glob('frame_*.jpg'))
    print(f"  Extracted {len(frames)} frames (every {interval}s)")
    return frames, interval


def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        info = json.loads(result.stdout)
        return float(info.get('format', {}).get('duration', 0))
    return 0


def detect_and_cluster_faces(frames, interval, threshold=0.55):
    """
    Detect faces in frames, cluster by identity using DBSCAN.
    Returns list of cluster dicts with best crop and timecodes.
    """
    import face_recognition
    import numpy as np
    from sklearn.cluster import DBSCAN
    from PIL import Image

    all_encodings = []
    all_crops = []   # (frame_idx, face_location, frame_path)

    print(f"\n  Detecting faces in {len(frames)} frames...")
    for i, frame_path in enumerate(frames):
        if i % 20 == 0:
            print(f"    Frame {i+1}/{len(frames)}...", end='\r', flush=True)

        try:
            img = face_recognition.load_image_file(str(frame_path))
            locations = face_recognition.face_locations(img, model='hog')
            encodings = face_recognition.face_encodings(img, locations)
        except Exception:
            continue

        for loc, enc in zip(locations, encodings):
            all_encodings.append(enc)
            all_crops.append((i, loc, frame_path))

    print(f"\n  Found {len(all_encodings)} face detections total")

    if not all_encodings:
        return []

    # Cluster with DBSCAN
    X = np.array(all_encodings)
    labels = DBSCAN(eps=threshold, min_samples=1, metric='euclidean').fit_predict(X)

    n_clusters = len(set(l for l in labels if l >= 0))
    print(f"  Clustered into {n_clusters} distinct person(s)")

    # Build cluster info
    clusters = {}
    for idx, (label, (frame_i, loc, frame_path)) in enumerate(zip(labels, all_crops)):
        if label < 0:  # noise
            continue
        key = f"person_{chr(65 + label)}"  # Person_A, Person_B, ...
        if key not in clusters:
            clusters[key] = {
                'label': key,
                'name': '',
                'appearances': [],
                'best_crop_base64': None,
                'best_crop_size': 0,
            }

        timecode = frame_i * interval
        clusters[key]['appearances'].append(timecode)

        # Extract face crop
        top, right, bottom, left = loc
        pad = 20
        try:
            from PIL import Image as PILImage
            img = PILImage.open(frame_path)
            crop = img.crop((
                max(0, left - pad),
                max(0, top - pad),
                min(img.width, right + pad),
                min(img.height, bottom + pad)
            ))
            area = crop.width * crop.height
            # Keep the largest (clearest) crop as the representative
            if area > clusters[key]['best_crop_size']:
                buf = io.BytesIO()
                crop.save(buf, format='JPEG', quality=85)
                clusters[key]['best_crop_base64'] = base64.b64encode(buf.getvalue()).decode()
                clusters[key]['best_crop_size'] = area
        except Exception:
            pass

    # Sort appearances, compute stats
    result = []
    for key in sorted(clusters.keys()):
        c = clusters[key]
        appearances = sorted(set(c['appearances']))
        result.append({
            'label': c['label'],
            'name': c['name'],
            'appearance_count': len(appearances),
            'first_seen': appearances[0] if appearances else 0,
            'last_seen': appearances[-1] if appearances else 0,
            'timecodes': appearances,
            'best_crop_base64': c['best_crop_base64'],
        })

    return result


def format_timecode(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def main():
    parser = argparse.ArgumentParser(description='Phase 1: extract and cluster faces from footage')
    parser.add_argument('--input', required=True, help='Path to input video file')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--frame-interval', type=int, default=3,
                        help='Seconds between frame samples (default: 3)')
    parser.add_argument('--face-threshold', type=float, default=0.55,
                        help='Face clustering distance threshold (default: 0.55)')
    args = parser.parse_args()

    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"ERROR: Missing dependencies: {', '.join(missing)}")
        print("Run the footage-analyst skill setup to install them.")
        sys.exit(1)

    video_path = Path(args.input)
    if not video_path.exists():
        print(f"ERROR: File not found: {video_path}")
        sys.exit(1)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🎬 Footage Analyst — Phase 1: Face Extraction")
    print(f"   Input:  {video_path.name}")
    print(f"   Output: {out_dir}")

    duration = get_video_duration(video_path)
    print(f"   Duration: {format_timecode(duration)}")

    # Extract frames
    with tempfile.TemporaryDirectory() as tmp:
        frames, interval = extract_frames(video_path, tmp, args.frame_interval)
        clusters = detect_and_cluster_faces(frames, interval, args.face_threshold)

    # Write output JSON
    output = {
        'video': str(video_path),
        'duration': duration,
        'duration_formatted': format_timecode(duration),
        'frame_interval': args.frame_interval,
        'face_threshold': args.face_threshold,
        'clusters': clusters,
    }

    out_file = out_dir / 'faces.json'
    with open(out_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Done! Detected {len(clusters)} person cluster(s):\n")
    for c in clusters:
        print(f"   {c['label']:10s}  {c['appearance_count']:3d} appearances  "
              f"first seen {format_timecode(c['first_seen'])}  "
              f"last seen {format_timecode(c['last_seen'])}")

    print(f"\n📄 Face data saved to: {out_file}")
    print(f"\nNext step: Claude will show you a face-labeling panel.")
    print(f"Label each person, then run the full analysis with:")
    print(f"  python3 analyze_footage.py --input \"{video_path}\" --output \"{out_dir}\" \\")
    print(f'    --labels \'{{\"person_a\": \"Name\", \"person_b\": \"Name\"}}\'')

    return str(out_file)


if __name__ == '__main__':
    main()
