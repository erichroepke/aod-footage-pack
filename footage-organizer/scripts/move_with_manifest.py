#!/usr/bin/env python3
"""
move_with_manifest.py — the Safe Move Protocol executor for footage-organizer.

Guarantees, enforced in code:
  * NEVER deletes anything. There is no deletion code in this file.
  * NEVER overwrites: a move whose destination exists is refused. No force flag.
  * Same-drive moves are RENAMES (data never rewritten).
  * Cross-drive moves are COPY + VERIFY; the source is always left in place.
  * Every file is hashed before and after; any mismatch aborts the run.
  * Every executed move is appended to a JSONL manifest; renames are undoable.

Usage:
    python3 move_with_manifest.py --plan plan.json [--dry-run] [--manifest out.jsonl]
    python3 move_with_manifest.py --undo --manifest out.jsonl

Plan format (JSON list):
    [{"src": "/abs/path/old", "dst": "/abs/path/new"}, ...]
    Entries may be files or directories. Directories move as whole units.
"""

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path


def hash_file(path):
    """xxHash64 (Hedge/OffShoot-style) with MD5 fallback."""
    try:
        import xxhash
        h = xxhash.xxh64()
        algo = 'xxh64'
    except ImportError:
        import hashlib
        h = hashlib.md5()
        algo = 'md5'
    with open(path, 'rb') as f:
        while chunk := f.read(8 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest(), algo


def files_under(path: Path):
    """All regular files for hashing: the file itself, or every file in a dir."""
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob('*') if p.is_file())


def same_volume(src: Path, dst_parent: Path) -> bool:
    return src.stat().st_dev == dst_parent.stat().st_dev


def validate(plan):
    """Validate every entry before anything runs. All-or-nothing."""
    errors = []
    seen_dst = set()
    for i, entry in enumerate(plan):
        src = Path(entry['src']).expanduser()
        dst = Path(entry['dst']).expanduser()
        tag = f"  [{i+1}] {src} → {dst}"
        if not src.exists():
            errors.append(f"{tag}\n      source does not exist")
        if dst.exists():
            errors.append(f"{tag}\n      DESTINATION ALREADY EXISTS — refusing (no overwrites, ever)")
        if str(dst) in seen_dst:
            errors.append(f"{tag}\n      duplicate destination in plan")
        seen_dst.add(str(dst))
        if src.is_dir() and str(dst.resolve()).startswith(str(src.resolve()) + os.sep):
            errors.append(f"{tag}\n      destination is inside the source folder")
    return errors


def append_manifest(manifest_path: Path, record: dict):
    with open(manifest_path, 'a') as f:
        f.write(json.dumps(record) + '\n')


def execute(plan, manifest_path: Path, dry_run: bool):
    errors = validate(plan)
    if errors:
        print("❌ Plan validation failed — NOTHING was moved:\n")
        print('\n'.join(errors))
        sys.exit(2)

    print(f"✅ Plan validated: {len(plan)} move(s)\n")

    moves = []
    for entry in plan:
        src = Path(entry['src']).expanduser()
        dst = Path(entry['dst']).expanduser()
        dst_parent = dst.parent
        # Determine mode now (dst_parent may not exist yet — walk up to nearest existing)
        probe = dst_parent
        while not probe.exists():
            probe = probe.parent
        mode = 'rename' if same_volume(src, probe) else 'copy_verify_source_retained'
        moves.append((src, dst, mode))
        print(f"  {'[DRY] ' if dry_run else ''}{mode:<28} {src}\n"
              f"  {'':>34}→ {dst}")

    if dry_run:
        print(f"\nDry run complete. {len(moves)} move(s) would execute. Nothing was touched.")
        return

    session = time.strftime('%Y-%m-%dT%H:%M:%S')
    moved = 0
    verified_files = 0

    for src, dst, mode in moves:
        # 1) hash everything at the source
        src_files = files_under(src)
        before = {}
        for f in src_files:
            digest, algo = hash_file(f)
            before[str(f.relative_to(src.parent))] = digest

        # 2) execute
        dst.parent.mkdir(parents=True, exist_ok=True)
        if mode == 'rename':
            os.rename(src, dst)
        else:
            if src.is_dir():
                shutil.copytree(src, dst)   # copy only — source untouched
            else:
                shutil.copy2(src, dst)      # copy only — source untouched

        # 3) re-hash at destination and compare (count + multiset of hashes)
        dst_files = files_under(dst)
        after = [hash_file(f) for f in dst_files]
        algo = after[0][1] if after else 'xxh64'
        before_hashes = sorted(before.values())
        after_hashes = sorted(digest for digest, _ in after)
        if len(before_hashes) != len(after_hashes) or before_hashes != after_hashes:
            print(f"\n🔴 CHECKSUM MISMATCH after moving {src} → {dst}")
            print("   Run aborted. Nothing further will move. Investigate before continuing.")
            append_manifest(manifest_path, {
                'session': session, 'mode': mode, 'src': str(src), 'dst': str(dst),
                'files': len(before_hashes), 'verified': False,
                'ts': time.strftime('%Y-%m-%dT%H:%M:%S')})
            sys.exit(3)

        verified_files += len(after_hashes)
        moved += 1
        append_manifest(manifest_path, {
            'session': session, 'mode': mode, 'src': str(src), 'dst': str(dst),
            'files': len(after_hashes), 'algo': algo, 'verified': True,
            'hashes': before, 'ts': time.strftime('%Y-%m-%dT%H:%M:%S')})
        note = '' if mode == 'rename' else '  (source left in place — delete it yourself after verifying)'
        print(f"  ✅ verified {len(after_hashes)} file(s){note}")

    print(f"\n{'='*60}")
    print(f"  START AND FINISH ARE THE SAME")
    print(f"  {moved} move(s) · {verified_files} file(s) · every checksum identical")
    print(f"  0 deletions (this tool cannot delete)")
    print(f"  Undo log: {manifest_path}")


def undo(manifest_path: Path):
    if not manifest_path.exists():
        print(f"No manifest found at {manifest_path}")
        sys.exit(1)
    records = [json.loads(line) for line in manifest_path.read_text().splitlines() if line.strip()]
    renames = [r for r in records if r['mode'] == 'rename' and r.get('verified')]
    copies = [r for r in records if r['mode'] != 'rename']

    if copies:
        print(f"ℹ️  {len(copies)} cross-drive copies are not undone (we never delete copies);")
        print("    their sources were never touched, so there is nothing to restore.\n")

    if not renames:
        print("No renames to undo.")
        return

    print(f"Reversing {len(renames)} rename(s), most recent first:\n")
    undone = 0
    for r in reversed(renames):
        src, dst = Path(r['src']), Path(r['dst'])
        if not dst.exists():
            print(f"  ⚠️ skip (missing): {dst}")
            continue
        if src.exists():
            print(f"  ⚠️ skip (original slot occupied): {src}")
            continue
        src.parent.mkdir(parents=True, exist_ok=True)
        os.rename(dst, src)
        append_manifest(manifest_path, {
            'session': 'undo', 'mode': 'undo_rename', 'src': str(dst),
            'dst': str(src), 'verified': True,
            'ts': time.strftime('%Y-%m-%dT%H:%M:%S')})
        print(f"  ↩️  {dst} → {src}")
        undone += 1
    print(f"\nUndo complete: {undone} rename(s) reversed. Nothing was deleted.")


def main():
    ap = argparse.ArgumentParser(description='Safe Move Protocol executor (never deletes)')
    ap.add_argument('--plan', help='JSON move plan: [{"src":..., "dst":...}]')
    ap.add_argument('--manifest', default=None,
                    help='JSONL undo log (default: _move_manifest.jsonl beside the plan)')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--undo', action='store_true', help='reverse renames from the manifest')
    args = ap.parse_args()

    if args.undo:
        if not args.manifest:
            print("--undo requires --manifest")
            sys.exit(1)
        undo(Path(args.manifest).expanduser())
        return

    if not args.plan:
        print("--plan is required (or use --undo)")
        sys.exit(1)

    plan_path = Path(args.plan).expanduser()
    plan = json.loads(plan_path.read_text())
    manifest = Path(args.manifest).expanduser() if args.manifest \
        else plan_path.parent / '_move_manifest.jsonl'
    execute(plan, manifest, args.dry_run)


if __name__ == '__main__':
    main()
