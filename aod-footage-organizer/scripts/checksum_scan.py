#!/usr/bin/env python3
"""
checksum_scan.py
Fast xxHash64 checksum scanning for footage folders.
Uses the same hash algorithm as Hedge and OffShoot.

Usage:
    python3 checksum_scan.py --path /path/to/01_footage [--write-sidecars] [--json output.json]

Output:
    - Prints a checksum report to stdout
    - Optionally writes .xxh64 sidecar files alongside each media file
    - Optionally saves results as JSON for the HTML report
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Media file extensions to scan
MEDIA_EXTENSIONS = {
    '.mp4', '.mov', '.mxf', '.r3d', '.braw', '.ari', '.mts', '.m2ts',
    '.mpeg', '.mpg', '.m4v', '.mkv', '.webm', '.avi',
    '.wav', '.aiff', '.aif', '.bwf', '.flac', '.mp3', '.m4a',
    '.dng', '.raw', '.cr2', '.cr3', '.arw', '.nef', '.rw2',
}


def hash_file(path, algo):
    """Compute a file hash for a specific sidecar algorithm."""
    if algo == 'xxh64':
        try:
            import xxhash
        except ImportError as exc:
            raise RuntimeError('xxhash unavailable') from exc
        h = xxhash.xxh64()
    elif algo == 'md5':
        import hashlib
        h = hashlib.md5()
    else:
        raise ValueError(f'unsupported checksum algorithm: {algo}')

    with open(path, 'rb') as f:
        while chunk := f.read(8 * 1024 * 1024):  # 8MB chunks
            h.update(chunk)
    return h.hexdigest(), algo


def preferred_hash_file(path):
    """Compute xxHash64 when available. Falls back to MD5 for new local sidecars."""
    try:
        return hash_file(path, 'xxh64')
    except RuntimeError:
        return hash_file(path, 'md5')


def sidecar_path(file_path, algo):
    """Return the expected sidecar file path for a given file."""
    return Path(str(file_path) + f'.{algo}')


def read_sidecar(file_path):
    """Return (hash, algo) from an existing sidecar, None if there is no
    sidecar, or ('', algo) if a sidecar exists but is empty/unreadable.
    Always reports which algorithm the sidecar was written with, so the
    caller never compares hashes from two different algorithms."""
    for ext, algo in (('.xxh64', 'xxh64'), ('.xxhash', 'xxh64'), ('.md5', 'md5')):
        sp = Path(str(file_path) + ext)
        if sp.exists():
            try:
                tokens = sp.read_text(errors='replace').strip().split()
            except OSError:
                tokens = []
            return (tokens[0] if tokens else ''), algo
    return None


# Folder names that mark an original camera-card dump (sealed units).
# Keep in sync with scan_tree.py / move_with_manifest.py.
CARD_MARKERS = {'DCIM', 'PRIVATE', 'CONTENTS', 'CLIPS', 'XDROOT', 'M4ROOT',
                'AVCHD', 'BDMV', 'MISC'}


def inside_card(file_path, root):
    """True if the file sits inside a sealed camera-card structure.
    Exact uppercase match (cameras always write DCIM/PRIVATE/... in caps)."""
    rel_parts = Path(file_path).relative_to(root).parts
    return any(part in CARD_MARKERS for part in rel_parts)


def human_size(n):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def scan(root_path, write_sidecars=False):
    """
    Scan all media files under root_path.
    Returns list of result dicts.
    """
    root = Path(root_path)
    if not root.exists():
        print(f"ERROR: Path not found: {root_path}")
        sys.exit(1)

    results = []
    files = [
        f for f in root.rglob('*')
        if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS
        and not f.name.startswith('.')
    ]

    total = len(files)
    print(f"\n🔍 Scanning {total} media file(s) under {root}\n")

    for i, fpath in enumerate(sorted(files), 1):
        rel = fpath.relative_to(root)
        size = fpath.stat().st_size
        print(f"  [{i}/{total}] {rel} ({human_size(size)})", end=' ', flush=True)

        t0 = time.time()

        # Check for existing sidecar — compute the sidecar's own algorithm when possible.
        existing = read_sidecar(fpath)
        if existing is None:
            existing_hash = None
            computed, algo = preferred_hash_file(fpath)
            status, icon = 'no_sidecar', '⚪'
        elif existing[0] == '':
            # sidecar file exists but holds no hash — flag it, never crash,
            # never overwrite it
            existing_hash = None
            computed, algo = preferred_hash_file(fpath)
            status, icon = 'sidecar_malformed', '🟠'
        else:
            existing_hash, existing_algo = existing
            try:
                computed, algo = hash_file(fpath, existing_algo)
            except RuntimeError:
                # A xxhash sidecar exists but this machine cannot compute xxhash.
                # NOT verified, NOT assumed corrupt — and never silently replaced.
                computed, algo = preferred_hash_file(fpath)
                status, icon = 'sidecar_unverifiable', '🟠'
            else:
                if existing_hash.lower() == computed.lower():
                    status, icon = 'verified', '✅'
                else:
                    status, icon = 'mismatch', '🔴'

        elapsed = time.time() - t0
        speed = size / elapsed / (1024**2) if elapsed > 0 else 0

        print(f"{icon} {computed[:12]}... [{algo}] {speed:.0f} MB/s")

        if write_sidecars and status == 'no_sidecar':
            if inside_card(fpath, root):
                # never write into an original card dump — the checksum is
                # still recorded in the report/JSON, just not beside the file
                print(f"     ⤷ inside a sealed card structure — checksum kept "
                      f"in the report only, no sidecar written")
            else:
                sp = sidecar_path(fpath, algo)
                sp.write_text(f"{computed}  {fpath.name}\n")
                print(f"     → wrote {sp.name}")

        results.append({
            'path': str(rel),
            'abs_path': str(fpath),
            'size': size,
            'size_human': human_size(size),
            'algo': algo,
            'computed': computed,
            'existing': existing_hash,
            'status': status,
            'speed_mbs': round(speed, 1),
        })

    # Summary
    verified = sum(1 for r in results if r['status'] == 'verified')
    mismatches = [r for r in results if r['status'] == 'mismatch']
    no_sidecar = sum(1 for r in results if r['status'] == 'no_sidecar')
    unverifiable = sum(1 for r in results if r['status'] == 'sidecar_unverifiable')
    malformed = sum(1 for r in results if r['status'] == 'sidecar_malformed')
    total_size = sum(r['size'] for r in results)

    print(f"\n{'='*60}")
    print(f"  Total files:    {total}")
    print(f"  Total size:     {human_size(total_size)}")
    print(f"  ✅ Verified:    {verified}")
    print(f"  ⚪ No sidecar:  {no_sidecar}")
    print(f"  🔴 Mismatches:  {len(mismatches)}")
    if malformed:
        print(f"  🟠 Malformed sidecars: {malformed} — a checksum file exists but "
              f"holds no hash. The media was hashed fresh; replace the empty "
              f"sidecar after investigating where it came from.")
    if unverifiable:
        print(f"  🟠 Unverifiable: {unverifiable} — sidecars exist but use a different "
              f"algorithm than this machine can compute.")
        print(f"     Install xxhash (pip3 install xxhash) to verify xxHash sidecars. "
              f"MD5 sidecars are verified without extra tools. These files "
              f"were NOT checked and NOT modified.")

    if mismatches:
        print(f"\n  ⚠️  CORRUPTION WARNINGS:")
        for r in mismatches:
            print(f"    {r['path']}")
            print(f"      Expected: {r['existing']}")
            print(f"      Got:      {r['computed']}")

    if no_sidecar > 0 and not write_sidecars and results:
        print(f"\n  💡 Run with --write-sidecars to create .{results[0]['algo']} sidecar files")

    print()
    return results, {
        'total': total,
        'total_size': total_size,
        'total_size_human': human_size(total_size),
        'verified': verified,
        'mismatches': len(mismatches),
        'no_sidecar': no_sidecar,
        'malformed': malformed,
        'algo': results[0]['algo'] if results else 'xxh64',
    }


def main():
    parser = argparse.ArgumentParser(description='xxHash64 checksum scan for footage folders')
    parser.add_argument('--path', required=True, help='Root path to scan')
    parser.add_argument('--write-sidecars', action='store_true',
                        help='Write .xxhash sidecar files for files without one')
    parser.add_argument('--json', default=None, help='Save results as JSON to this path')
    args = parser.parse_args()

    results, summary = scan(args.path, write_sidecars=args.write_sidecars)

    if args.json:
        out = {'summary': summary, 'files': results}
        with open(args.json, 'w') as f:
            json.dump(out, f, indent=2)
        print(f"  JSON saved to: {args.json}")

    # Exit code: 0=clean, 1=mismatches or malformed sidecars found
    sys.exit(1 if (summary['mismatches'] > 0 or summary['malformed'] > 0) else 0)


if __name__ == '__main__':
    main()
