#!/usr/bin/env python3
"""
scan_tree.py — summarizing project scanner for footage-organizer.

Walks a production folder and reports structure WITHOUT flooding the
conversation: counts and sizes per folder, sealed camera-card detection,
date-format problems, loose media, and .prproj locations. Full detail goes
to JSON; stdout stays a readable summary even on multi-terabyte drives.

READ-ONLY. This script never modifies, moves, or deletes anything.

Usage:
    python3 scan_tree.py --path /path/to/PROJECT [--json out.json] [--max-depth 8]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

MEDIA_EXTENSIONS = {
    '.mp4', '.mov', '.mxf', '.r3d', '.braw', '.ari', '.mts', '.m2ts',
    '.mpeg', '.mpg', '.m4v', '.mkv', '.webm', '.avi',
    '.wav', '.aiff', '.aif', '.bwf', '.flac', '.mp3', '.m4a',
    '.dng', '.raw', '.cr2', '.cr3', '.arw', '.nef', '.rw2',
}

# Folder names that mark an original camera-card dump (sealed units)
CARD_MARKERS = {'DCIM', 'PRIVATE', 'CONTENTS', 'CLIPS', 'XDROOT', 'M4ROOT',
                'AVCHD', 'BDMV', 'MISC'}

ISO_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
DATEISH = re.compile(
    r'^(\d{8}|\d{1,2}[-_/.]\d{1,2}[-_/.]\d{2,4}|'
    r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-_ ]?\d{1,2})',
    re.IGNORECASE)

LIST_CAP = 40  # max items per issue list on stdout


def human_size(n):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def scan(root: Path, max_depth: int):
    result = {
        'root': str(root),
        'dirs': {},          # rel path -> {files, media_files, size, depth}
        'card_units': [],    # rel paths of detected sealed card structures
        'date_problems': [], # {path, name, suggestion}
        'loose_media': [],   # media files in suspect (non-leaf/root) locations
        'prproj_files': [],
        'sidecar_files': 0,
        'totals': {'files': 0, 'media_files': 0, 'size': 0, 'dirs': 0},
    }

    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        depth = len(d.parts) - root_depth
        if depth >= max_depth:
            dirnames[:] = []
        # skip hidden dirs entirely
        dirnames[:] = [n for n in dirnames if not n.startswith('.')]
        rel = str(d.relative_to(root)) if d != root else '.'

        files = [f for f in filenames if not f.startswith('.')]
        sizes = 0
        media = 0
        for f in files:
            fp = d / f
            try:
                s = fp.stat().st_size
            except OSError:
                continue
            sizes += s
            ext = fp.suffix.lower()
            if ext in MEDIA_EXTENSIONS:
                media += 1
            if ext in {'.xxhash', '.md5', '.xxh64'}:
                result['sidecar_files'] += 1
            if ext == '.prproj':
                result['prproj_files'].append(str(fp.relative_to(root)))

        result['dirs'][rel] = {'files': len(files), 'media_files': media,
                               'size': sizes, 'depth': depth}
        result['totals']['files'] += len(files)
        result['totals']['media_files'] += media
        result['totals']['size'] += sizes
        result['totals']['dirs'] += 1

        # sealed card detection: a child dir named like a card marker
        for name in dirnames:
            if name.upper() in CARD_MARKERS:
                result['card_units'].append(rel if rel != '.' else name)
                break

        # date-format problems: looks like a date, isn't ISO
        base = d.name
        if depth > 0 and not ISO_DATE.match(base) and DATEISH.match(base):
            result['date_problems'].append({
                'path': rel, 'name': base,
                'suggestion': 'rename to YYYY-MM-DD'})

        # loose media: media files sitting in a folder that also has subfolders
        # (non-leaf), or directly in 01_footage root / a shoot root
        if media > 0 and dirnames:
            for f in files:
                if (d / f).suffix.lower() in MEDIA_EXTENSIONS:
                    result['loose_media'].append(str((d / f).relative_to(root)))

    return result


def print_summary(r):
    t = r['totals']
    print(f"\n📁 Scan: {r['root']}")
    print(f"   {t['dirs']} folders · {t['files']} files · "
          f"{t['media_files']} media files · {human_size(t['size'])}\n")

    print("── Top-level structure ──")
    for rel, info in sorted(r['dirs'].items()):
        if info['depth'] == 1:
            print(f"   {rel:<40} {info['files']:>5} files  "
                  f"{human_size(info['size']):>10}")

    def cap_list(title, items, fmt=lambda x: f"   {x}"):
        if not items:
            return
        print(f"\n── {title} ({len(items)}) ──")
        for item in items[:LIST_CAP]:
            print(fmt(item))
        if len(items) > LIST_CAP:
            print(f"   … +{len(items) - LIST_CAP} more (see JSON)")

    cap_list("🔒 Sealed card units detected (never restructure inside)",
             sorted(set(r['card_units'])))
    cap_list("📅 Date-format problems", r['date_problems'],
             lambda p: f"   {p['path']}  ('{p['name']}' → {p['suggestion']})")
    cap_list("🟡 Loose media (in non-leaf folders — candidates for the move plan)",
             r['loose_media'])
    cap_list("🎬 .prproj files", r['prproj_files'])
    print()


def main():
    ap = argparse.ArgumentParser(description='Read-only summarizing footage scanner')
    ap.add_argument('--path', required=True)
    ap.add_argument('--json', default=None, help='write full results to this path')
    ap.add_argument('--max-depth', type=int, default=8)
    args = ap.parse_args()

    root = Path(args.path).expanduser()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}")
        sys.exit(1)

    result = scan(root, args.max_depth)
    print_summary(result)

    if args.json:
        with open(args.json, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"   Full detail saved to: {args.json}\n")


if __name__ == '__main__':
    main()
