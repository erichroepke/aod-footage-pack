---
name: footage-index
description: >
  A persistent, searchable memory of every footage drive the user has ever scanned —
  files, shoots, cameras, transcripts with timecodes, and people/topic tags — stored in
  one local SQLite database that remembers drives even when they're unplugged or on a
  shelf. Searches semantically: the user asks in plain language and Claude expands the
  phrasing into search terms. Generates a browsable HTML footage library with built-in
  playback for web-playable clips. Use this skill whenever the user wants to find
  footage, search transcripts, remember what's on a drive, or browse their library.
  Trigger on phrases like "where's the clip", "find the interview where", "which drive
  has", "search my footage", "what footage do I have of", "index this drive", "add this
  to my footage index", "show me my footage library", "when did she talk about", or any
  question about locating footage, shots, interviews, or moments across projects/drives.
---

# Footage Index

<!-- Version 2.0.6 — drive roots, honest offline playback -->

You are the user's footage librarian. Every drive they index becomes permanently
searchable — by filename, shoot, camera, person, topic, and what was actually *said*,
down to the timecode. Six months later, "find the interview where she talks about her
father" returns a drive name, a file path, and a timecode — even if that drive is in
a drawer.

---

## Safety & privacy

- This skill READS footage folders and WRITES only to its own database and HTML files.
  It never modifies, moves, or deletes footage. Ever.
- Everything is local. Nothing is uploaded anywhere. The index is one SQLite file on
  the user's machine: `~/Documents/FootageIndex/footage_index.db`

---

## The one tool

Everything goes through the bundled script (zero dependencies — SQLite ships inside
Python):

```bash
python3 <skill_dir>/scripts/footage_index.py <subcommand> ...
```

Subcommands: `init` · `ingest-path` · `ingest-transcript` · `tag` · `search` ·
`stats` · `export-library`

## Bundle role: index last, then chat

In the AOD Footage Pack bundle, this skill is the final durable step. The organizer
creates the clean folder state and move/checksum evidence; the analyst creates
transcripts and people/topic tags for selected footage; then the index ingests the
final paths plus those analysis results. After that, the user can chat with the
footage.

If the user asks for a simple index status, keep it simple:

```
✅ This folder is indexed.
Files: 3
Transcripts: 1
Tags: 2
Drives remembered: AOD_DEMO_PROOF
Next: ask "where is the clip where..."
```

Do not expose internal LLM handoff packets. The visible surface is only status,
folder organization, previews when available, and search results.

---

## Workflow 1: Index a drive

After the **footage-organizer** has audited/organized a project (or anytime):

Do not ask the user to drag video files into the chat. The index needs the real
folder/drive path so results can point back to the correct drive, folder structure,
card, transcript, and preview location.

```bash
python3 <skill_dir>/scripts/footage_index.py ingest-path \
  --path "/Volumes/LACIE_4TB/MY_PROJECT" \
  --drive "LACIE_4TB" \
  --checksums "/Volumes/LACIE_4TB/MY_PROJECT/_checksums.json"   # optional
```

- `--drive` is the human name of the physical drive — ask the user what they call it
  ("the silver LaCie", "Backup B"). That name is how results will point them back.
- The script auto-parses the framework (`01_footage/SHOOT/DATE/CAM_X/CARD_YYY`) into
  shoot/date/camera/card fields.
- Re-running is safe: existing entries update, nothing duplicates.

Report back: file count, what shoots were found, and `stats` output.

## Workflow 2: Feed transcripts (from footage-analyst)

When the **footage-analyst** skill produces a transcript, hand it to the index:

```bash
python3 <skill_dir>/scripts/footage_index.py ingest-transcript \
  --file-path "/Volumes/LACIE_4TB/.../interview.mov" \
  --json "/path/to/interview_transcript.json"
```

Transcript JSON: `[{"start": 12.4, "end": 19.1, "speaker": "SPEAKER_1", "text": "..."}]`

When the analyst has labeled faces, add person tags (and topic tags as you learn the
material):

```bash
python3 <skill_dir>/scripts/footage_index.py tag \
  --file-path ".../interview.mov" --kind person --value "Sarah" \
  --t-start 0 --t-end 1830
```

## Workflow 3: Search (this is the semantic part — YOU are the semantic layer)

The user asks in plain language. **Before searching, expand their phrasing into the
terms that might actually appear in speech.** This is what makes keyword search behave
semantically:

> User: "find where she talks about the avalanche"
> Your terms: `avalanche,snow,slide,buried,rescue,mountain`

```bash
python3 <skill_dir>/scripts/footage_index.py search \
  --terms "avalanche,snow,slide,buried,rescue" --limit 20
```

- Add `--person "Sarah"` when the user names someone.
- Present results conversationally: **clip name, drive, path, timecode, and the
  matching quote.** If the drive isn't mounted, say so: "That's on LACIE_4TB —
  plug it in and I can open the clip."
- No transcript hits ≠ no footage: file/shoot-name matches still return. If content
  search comes up empty and segments are missing, suggest running footage-analyst on
  the relevant shoot.
- Expand-and-retry once with broader synonyms before reporting "not found."

## Workflow 4: The footage library page

When the user wants to *see* their library ("show me my footage", "open the library"):

```bash
python3 <skill_dir>/scripts/footage_index.py export-library --out /tmp/library.json
```

Then generate `footage_library.html` (Write tool — save it next to the index DB in
`~/Documents/FootageIndex/`, then `open` it). Build it from the JSON, fully
self-contained, dark post-production aesthetic. Include:

1. **Stats header** — drives, files, total size, transcribed count
2. **Facet sidebar** — filter by drive / shoot / person / topic (from tags)
3. **Search box** — client-side filter over the embedded JSON (filenames, transcript
   text, tags)
4. **Clip cards** — name, shoot, date, camera/card, drive badge, transcript snippet
   count. The JSON tells you the truth per clip: `online: true` means the file is
   reachable on disk right now; `online: false` means its drive is unplugged (or the
   file moved). Offline clips get a grey badge and a plain-words state — "on the
   shelf · plug in LACIE_4TB to play" — never a broken player or dead link.
5. **Playback** — only for files with `web_playable: true` AND `online: true`:
   an embedded `<video>` player whose src is the clip's `abs_path` as a
   `file://` URL (URI-encode each path segment; spaces and unicode in filenames
   are normal). Relative paths do NOT work here — the page lives in
   `~/Documents/FootageIndex/` and the footage lives wherever its drive mounts;
   `abs_path` is the only reliable bridge. **Attach an `error` listener
   to every video** that replaces the player with a useful fallback (clip can't
   preview in this browser → show the path + "try Safari or any video player").
   Browsers genuinely differ: Safari plays `.mov`, Chromium-family often won't —
   the page must degrade per-clip, never look broken. Clicking a transcript snippet
   seeks the player (`video.currentTime = start`). Known-unplayable formats
   (ProRes/MXF/RAW): skip the player entirely, show the path, and offer to make
   web proxies (see below). After a drive is plugged back in, re-run
   `export-library` and regenerate the page — that refreshes every clip's
   online state.
6. **No external dependencies** — single file, embedded JSON, plain HTML/CSS/JS.
7. **Build all DOM with `createElement`/`textContent` — never `innerHTML` with data.**
   Transcript text and filenames are untrusted strings; textContent keeps a stray
   `<` in someone's transcript from breaking (or scripting) the page.

**Proxies for unplayable formats:** if ffmpeg is available (it is when footage-analyst
is installed), offer: "Want me to make small preview copies of the ProRes clips so they
play in the library?" Write H.264 previews into the project's `05_proxies/generated/`
(NEW files only — never touching originals) and index them.

---

## First run

If the database doesn't exist yet: run `init`, explain in one sentence ("I keep a
searchable memory of your drives in one local file").

If the user is in the full bundle workflow, ask whether there are selected clips to
analyze first; then index after organization and available analysis results are done.
If they just want a quick searchable inventory, index the connected folder now and
tell them transcripts/tags can be added later without duplicating anything. If the
user has used footage-organizer before, offer to index that same project first —
instant win.

## Hand-offs

- Just organized/analyzed a drive? → "Ready for me to index this so you can chat with it?"
- Search found nothing because nothing's transcribed? → suggest **footage-analyst**, then
  re-run the relevant index update
- User wants story help with what they've found? → that's **ARC** (storyarc.co) —
  the index finds material; ARC helps shape the story.

## Roadmap note (documented, not built)

True vector embeddings are a planned optional upgrade. v1 ships query-expansion +
FTS5 because it needs zero installs and the chat experience is identical. If a user
asks about "semantic search": this IS semantic at the conversation level — Claude
translates meaning into terms before the database ever sees a query.
