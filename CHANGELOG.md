# Changelog

## 0.1.0-alpha — 2026-06-11

Honest version reset + AOD naming. No code behavior change.

- **Version reset to 0.1.0-alpha.** The earlier 2.0.x numbers implied a maturity
  this pack has not earned: no outside user has installed it, and the end-to-end
  run (Claude executing the scripts against a real drive in Cowork) is still
  unverified. This is an alpha. The prior 2.0.x history is preserved in git tags;
  all 2.0.x release pages are superseded by this one.
- **All three skills renamed with an `aod-` prefix** so they're identifiable in a
  student's skills list and namespaced to the Art of Documentary course:
  - `footage-organizer` → `aod-footage-organizer`
  - `footage-index` → `aod-footage-index`
  - `footage-analyst` → `aod-footage-analyst`
  The `name:` field in each SKILL.md (what Claude keys on), the folders, the build
  script, every cross-reference, and the user-facing script messages were all
  updated. Distributed files are now `aod-footage-*.skill`.
- **Note for anyone who installed a pre-rename version:** the rename makes these
  NEW skills in your account, not in-place updates. Remove the old
  `footage-organizer` (etc.) from Customize → Skills and install the `aod-`
  versions.

---

## 2.0.7 — 2026-06-11
*(superseded by 0.1.0-alpha — version numbering reset; content carried forward)*

Install path corrected and staged (docs/packaging only, no script changes):

- **README + release notes:** the documented, working install path is
  **Customize → Skills → + → Create skill → Upload a skill** inside Claude.
  Double-clicking a `.skill` file in Finder opens Claude but does NOT install
  anything — verified on a real machine 2026-06-10 (file association exists,
  no install handler fires, nothing lands in the account). Added the one-time
  prerequisite (Settings → Capabilities → "Code execution and file creation")
  and the toggle-ON verification step. Skills live in the Claude account, not
  on local disk.
- **Staged install:** the README now walks the student through installing
  **footage-organizer first** (zero setup, first win in ~2 minutes), then
  adding footage-index and footage-analyst later when they want search and
  transcription. One upload to start, not three. The pack stays three separate
  skills on purpose — precise per-skill triggers, lighter context per use, and
  a clean safety boundary around the never-delete organizer (mirrors how
  Anthropic ships pdf/docx/xlsx as separate skills, not one mega-skill).
- **Version markers:** all three SKILL.md files stamped 2.0.7 so the release
  tag, docs, and bundled skills all read the same version.

## 2.0.6 — 2026-06-10

Closes the last open Codex-audit finding (#16, library playback paths):

- **footage_index.py:** the index now remembers each drive's scanned root
  (mount location). Older databases migrate automatically. Re-ingesting a
  SUBFOLDER of an indexed drive keeps the original anchor (no duplicate rows,
  no root clobbering); re-ingesting a PARENT re-anchors existing rows to the
  higher root; a drive that shows up at a new mount point updates in place
- **export-library** emits `abs_path` (real on-disk location) and `online`
  (file reachable right now) per clip, plus per-drive root/online status —
  the library page can finally tell the truth instead of guessing with
  relative paths
- **search** results for unplugged drives now say "drive not connected —
  plug it in to open this clip"; **stats** shows connected / on the shelf
  per drive
- **footage-index/SKILL.md:** resolved the contradictory playback
  instructions — the library page lives in `~/Documents/FootageIndex/`, plays
  online clips via `file://` URLs built from `abs_path`, and shows a plain
  "on the shelf · plug in DRIVE to play" state for offline clips. Never a
  silently dead link

## 2.0.5 — 2026-06-10

Safety enforcement pass — every remaining open finding from the 2026-06-10 Codex
audit moved from prompt-level guidance into code, verified against an adversarial
fixture tree (deep AVCHD cards, sealed-card escapes, nested symlinks, empty
sidecars, unicode/space/quote filenames):

- **move_with_manifest.py:** real runs now require `--backup-confirmed` (the
  Backup Gate is enforced in code, not just in the skill prompt); sealed
  camera-card structures (`DCIM`, `PRIVATE`, `AVCHD`, ...) are enforced at
  validation — nothing moves out of, into, or within a card unit, while moving
  the whole card folder stays allowed; folders containing nested symlinks are
  refused at validation; a fsynced `rename_started` record now lands in the
  manifest BEFORE each rename, so a crash mid-run can never strand a moved file
  with no undo entry, and `--undo` recovers started-but-unverified renames
- **checksum_scan.py:** `--write-sidecars` never writes inside sealed card
  structures (checksums stay in the report/JSON only); empty or unreadable
  sidecar files report 🟠 `sidecar_malformed` and exit non-zero instead of
  crashing
- **scan_tree.py:** depth no longer prunes the walk — media nested 9-10 levels
  deep in AVCHD/BDMV/STREAM card structures is always counted (`--max-depth`
  only caps report detail); loose media is now also flagged in leaf shoot
  folders and at shallow levels, and media inside sealed cards is never
  flagged as loose
- **README:** undo claim made accurate (same-drive moves undoable; cross-drive
  copies never touch the original); "no other software" split — organizer/index
  need nothing, analyst guides its own helper installs

## 2.0.4 — 2026-06-10

Bundle workflow guidance:

- **README:** reframed the three skills as one pack: connect/download, organize,
  analyze selected footage, index final state, then chat with the footage
- **footage-organizer:** offers analyst-before-index and index-final handoffs after
  organization/verification
- **footage-analyst:** feeds transcripts and labels into the final index step without
  exposing internal handoff packets
- **footage-index:** documents its bundle role as the final searchable state and
  adds the plain "this folder is indexed" status pattern
- **All skills:** clarified that users should put footage in the project folder/drive
  and grant folder access, not drag individual media files into the chat

## 2.0.3 — 2026-06-10

Demo run-through fix:

- **analyze_footage.py:** full analysis now handles clips with zero detected
  faces without crashing; the report renders the "No faces detected" state

## 2.0.2 — 2026-06-10

Codex CLI second-opinion patch pass. Fixes release blockers found after 2.0.1:

- **move_with_manifest.py:** cross-drive file copies now use exclusive destination
  creation, so a destination that appears after validation still cannot be
  overwritten
- **analyze_footage.py:** replaced shell-built ffmpeg/ffprobe commands with
  list-form subprocess calls; report text/labels are HTML-escaped; temp work
  folders are unique per run so a pre-existing `_work` folder is never deleted;
  macOS `/private/var` temp paths no longer trip the camera-card `PRIVATE`
  folder safety fence
- **footage_index.py:** FTS rows now stay in sync on transcript replacement, and
  existing databases rebuild FTS state on connect; `ingest-transcript` and `tag`
  accept `--drive` for duplicate clip names/paths
- **checksum_scan.py:** existing `.md5` sidecars are verified with stdlib MD5
  instead of being marked unverifiable when xxhash is unavailable

## 2.0.1 — 2026-06-10

Four-agent review pass (beginner experience, code correctness, adversarial safety,
consistency). Fixes:

- **move_with_manifest.py hardened:** path-keyed before/after hash comparison
  (catches swapped-content corruption), symlink/duplicate-source/nested-entry
  rejection at validation, destination re-checked at the moment of every rename
  (no race window), EXDEV fallback to copy, unknown-volume cases default to the
  safer copy mode, failed cross-drive copies leave a manifest record and
  plain-English recovery steps, case-only renames get a clear explanation
- **checksum_scan.py:** sidecars of a different algorithm now report 🟠
  "unverifiable" instead of false corruption alarms or silent replacement;
  empty-folder scan no longer crashes
- **footage_index.py:** accepts whisper/mlx-whisper `{"segments": [...]}` JSON
  directly; same-name clips on multiple drives disambiguate by path components
  (with a warning when truly ambiguous); FTS5 quote escaping; `--topic` filter
  actually works
- **analyst scripts:** refuse `--output` inside `01_footage/` or any card folder
- **SKILL.mds:** folder renames classified as moves (no freehand `mv` loophole),
  backup-gate trust doesn't relax checksums, plain-English narration rules
  (no scary flags shown to users), HuggingFace explained in human terms,
  `.xxh64` naming unified
- **README:** rewritten install steps with checkpoints and fallbacks, warmer
  safety section, undo explained, install-time expectations set
- **Added LICENSE** (MIT — was declared but missing)

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
