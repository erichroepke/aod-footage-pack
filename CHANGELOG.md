# Changelog

## 2.0.0 — 2026-06-10

The pack release. Two skills become three, and the organizer learns to act.

### footage-organizer 2.0.0
- **Spine flip:** from read-only auditor to safe mover. New Safe Move Protocol:
  scan → propose plan → backup gate → approval → checksum before → move (rename;
  cross-drive is copy+verify, source retained) → checksum after → undo log
- Still cannot delete. Now enforced in code, not just instructions
  (`move_with_manifest.py` contains no deletion calls; destinations that exist are
  refused — no overwrites, no force flag)
- New `scan_tree.py`: summarizing scanner — multi-TB drives no longer flood the chat
- New eval: move-protocol behavior (backup gate, plan-first, never-delete)

### footage-index 1.0.0 (new)
- One local SQLite database remembers every drive scanned: files, shoots, cameras,
  cards, hashes, transcript segments, person/topic tags
- FTS5 search with Claude-side semantic query expansion; results return drive +
  path + timecode
- `export-library` feeds a generated HTML footage library (browse, filter, search,
  in-browser playback for web-playable clips)

### footage-analyst 2.0.0
- Pre-flight checks (disk/RAM/chip) + honest time expectations before installing
- Resume-safe, checkpointed installer messaging
- **Quick-transcribe fast path:** mlx-whisper on Apple Silicon (no 2 GB PyTorch
  download) for transcription-only requests
- Phase 2 `transcript.json` + face labels now feed the footage index

### Pack
- `build.sh`: .skill packages are built from one canonical source (kills version
  drift and 0-byte packages), with zip integrity verification
- Beginner-first README (install via Releases, double-click/drag, no terminal)

## 1.0.0 — 2026-06-10 (morning session)
- footage-organizer (read-only audit + xxHash64) and footage-analyst (two-phase
  face/transcript pipeline), first packaged versions
