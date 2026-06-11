# AOD Footage Pack

> **Alpha (v0.1.0).** Early and under active development. The core has been tested hard,
> but the install and end-to-end run have not yet been proven by an outside user. Treat
> it as a preview, keep a backup of your footage, and expect rough edges.

**Claude becomes your post supervisor.** Three skills for documentary filmmakers:

| Skill | What it does | What you say |
|-------|--------------|--------------|
| 🗂 **aod-footage-organizer** | Audits your drive against a professional folder structure, then — with your approval — safely moves footage into place. Every move is verified with a digital fingerprint, moves on the same drive are undoable with one command, and deleting is impossible. | *"Check my footage folder"* · *"Organize this drive"* |
| 🔎 **aod-footage-index** | A searchable memory of every drive you've ever scanned. Ask for a moment, get the drive, file, and timecode — even if that drive is on a shelf. | *"Where's the interview where she talks about her father?"* |
| 🎞 **aod-footage-analyst** | Transcribes footage, identifies who's on screen (you label the faces), breaks down speakers, makes a beautiful HTML report. | *"Transcribe this clip"* · *"Who's in this video?"* |

Treat them as one bundle, not three separate apps. **Organizer and analyst create the
evidence; index is the final "this folder is searchable now" step.** Once a folder is
indexed, you can just chat with Claude about the footage.

Everything runs **on your computer**. No footage is ever uploaded anywhere.

---

## 🚨 Read this first

These skills work with camera originals — possibly the only copy of irreplaceable
material. They are built around one rule: **they cannot delete your files.** The
organizer only *moves* footage, only after you approve a plan, and only after you
confirm a backup exists. Before and after every move it checks each file's digital
fingerprint — the same kind of verification professional offload tools use — to prove
nothing changed in transit. If you ever change your mind, just say **"undo the
organizer's moves"** and Claude reverses every move it made on that drive. (Moves
*between* drives work differently — and even more safely: the organizer copies and
verifies, and your original is never touched, so there is nothing to undo.)

One important thing from us: **always keep a backup of your footage before organizing
— never work on the only copy.** The skill enforces this (it asks about your backup
before moving a single file), but you're the one responsible for protecting your
material. That's true of any tool that touches camera originals, this one included —
it's provided free, as-is.

---

## Install (first win in ~2 minutes)

You need the **Claude desktop app** (the one with Cowork). **Start with just the
organizer** — it needs no other software, you never open Terminal, and you'll have an
organized drive in a couple of minutes. Add the other two skills later, only when you
want them. You don't have to install all three at once.

**One-time setting (do this first).** In Claude, open **Settings → Capabilities** and
make sure **"Code execution and file creation"** is turned ON. Skills need it to run.

### Step 1 — install the organizer (your first win)

1. **Download** `aod-footage-organizer.skill` from the **Releases** link on this page (or
   the link in your AOD course materials). It lands in your **Downloads** folder.
2. In Claude, click **Customize** in the left sidebar → **Skills**. Click the **+**
   button → **Create skill** → **Upload a skill**, and pick `aod-footage-organizer.skill`
   from Downloads. Claude reads it and shows a short summary.
   *(Don't double-click the `.skill` file in Finder — that opens Claude but installs
   nothing. Always go through Customize → Skills.)*
3. Make sure its toggle in **Customize → Skills** is **ON**. (Skills live in your
   Claude account, so they follow you across your devices.)
4. Start a new Cowork conversation, give Claude access to your footage folder when it
   asks (or use the **+** / folder button to choose your project folder or drive), and
   type: **"check my footage folder."**

That's the whole first experience. No terminal, no setup, nothing to break.

### Step 2 — add search and transcription when you want them

When you're ready for searchable footage and transcripts, install the other two the
same way (**Customize → Skills → + → Upload a skill**):

- **`aod-footage-index.skill`** — searchable memory of every drive. Still zero setup.
- **`aod-footage-analyst.skill`** — transcripts + face ID. The first time you use it,
  Claude installs its free helper tools for you, asking permission as it goes — still
  no Terminal.

Install all three and they work as one pack: organize → analyze → index → then just
chat with your footage.

**Important:** do not drag individual video files into the chat. Put footage in the
project folder or connected drive first, then give Claude access to that folder. The
skills work by scanning the real folder on disk, preserving paths, drive names, card
structures, sidecars, and future index/search results.

The skill takes it from there — it introduces itself, looks at your drive (reading
only — nothing moves without your approval), and talks you through everything. If a
skill ever needs a helper tool installed (like the transcription engine), **it asks
your permission and installs it for you**, narrating as it goes.

> 🧭 **Install all three. Use them as one pack.** Start by asking Claude to run the
> AOD footage workflow on a folder or drive. Claude audits and safely organizes first,
> analyzes selected footage when transcripts or people are useful, then indexes last.
> After the index says the folder is complete, the normal interface is chat:
> "find the interview where..." or "show me everything with Sarah."

## How the bundle runs

The pack has one simple rhythm:

```
DOWNLOAD / CONNECT FOLDER
  -> ORGANIZE + VERIFY
  -> ANALYZE SELECTED FOOTAGE
  -> INDEX FINAL STATE
  -> CHAT WITH THE FOOTAGE
```

The steps can overlap, but the index is the durable finish line.

1. **Download / connect** — install all three `.skill` files, then give Claude access
   to the footage folder or drive. Do not attach media files to the chat; add them to
   the folder or drive and let Claude scan that location.
2. **Organize** — Claude scans the folder, shows the folder tree, flags issues, and
   proposes safe moves. Nothing moves until you approve and confirm a backup.
3. **Analyze** — Claude transcribes selected interviews or clips, labels people when
   needed, and creates local reports. This can run while the broader folder is being
   organized or checked.
4. **Index** — Claude ingests the final folder paths plus any transcripts and tags.
   The index is what lets you chat with the footage later.
5. **Chat** — ask normal questions. Claude searches the local index and answers with
   drive, file path, timecode, and matching quote when a transcript exists.

The status surface should stay plain: folder tree, checkmarks, counts, and a short
sidebar summary like **"This folder is indexed: 3 files, 1 transcript, 2 people/tags,
all moves verified."** The LLM reasoning stays in Claude; the visible UI only shows
media state and progress.

## Your first five minutes (just say these)

Everything in this pack is driven by talking to Claude. There's no app to learn —
these prompts are the product:

1. **"Run the AOD footage workflow on this folder"** → audit, summary, and next steps
2. **"Okay, organize it"** → Claude proposes a move plan, asks about your backup,
   and only acts when you approve
3. **"Transcribe these interviews"** → transcript with timecodes (first run installs
   the free transcription engine — Claude walks you through it)
4. **"Index this folder — call the drive [your drive's name]"** → the organized folder
   and analysis results become searchable
5. **"Show me my footage library"** → a simple indexed-folder summary plus visual
   previews where available
6. Months later: **"Which drive has the interview where she talks about her
   father?"** → drive name, file, timecode.

## Updating

Download the new `.skill` files from Releases and install them the same way — the new
version replaces the old one. **Then start a new chat** — Claude loads skills when a
session begins, so an update doesn't apply to chats that are already open.

---

## What's inside (for the curious)

```
aod-footage-organizer/   SKILL.md + scan_tree.py, checksum_scan.py, move_with_manifest.py
aod-footage-index/       SKILL.md + footage_index.py   (SQLite, all local)
aod-footage-analyst/     SKILL.md + extract_faces.py, analyze_footage.py
build.sh                 packages the .skill files (maintainers only)
```

- Organizer + index need **zero dependencies** — they run on what's already on a Mac.
- The analyst uses free, open-source AI (Whisper for transcription, local face
  clustering) — installed on demand, with your permission, all local.
- The index is one SQLite file at `~/Documents/FootageIndex/footage_index.db`.
  Delete that file and the index is gone (your footage is never touched).

## The folder framework

The organizer teaches a professional production structure — `00_projects` /
`01_footage` (shoots → dates → cameras → cards, originals preserved exactly) /
`02_music` / `03_archives` / `04_assets` / `05_proxies` / `09_exports`. The full spec
with rules lives in [aod-footage-organizer/SKILL.md](aod-footage-organizer/SKILL.md).

## License

MIT. Use freely, share freely. No warranty of any kind — **back up your footage.**

---

*Built for the Art of Documentary community. The pack finds and organizes your
material; for shaping the story it becomes, see [ARC](https://storyarc.co).*
