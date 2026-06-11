# AOD Cowork Skill Pack

---

**A note from me before you start**

This is something I built for you — for this community. It works. I use it myself, I've tested it hard, and I think you're going to find it genuinely useful. But it's early, and you're among the first people outside my own workflow to run it. So go in with that expectation: it's real, it's useful, and there will be rough edges.

The one thing I want you to take seriously: **always point this at a copy of your footage, not your originals.** The tool is designed so it physically cannot delete your files — but that doesn't mean I want you working on the only copy of something irreplaceable.

The easiest way to protect yourself is to make a proxy copy first. Proxies are just smaller, lower-resolution versions of your clips — same filenames, a fraction of the size — safe to experiment on. Your editing app can generate them:

- **Premiere Pro:** right-click your clips in the Project panel → Proxy → Create Proxies
- **Final Cut Pro:** File → Transcode Media → Create Proxy Media
- **DaVinci Resolve:** right-click in the Media Pool → Generate Optimized Media

Or the simplest version: just duplicate your footage folder in Finder before you start. Not technically proxies, but it's a real copy — and that's what matters. Point the organizer at the copy. Keep your originals where they are. Once you're happy with how it runs, apply the same workflow to the real drives.

This is alpha software. It's provided free, as-is, with no warranty. Back up your footage. You're responsible for your material — the same as with any tool that touches camera originals.

— Erich

---

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

## How to install in Claude Cowork

These skills run inside **Claude Cowork** — the desktop version of Claude with the ability to run code and access your files. You need the Claude desktop app and a paid plan (Pro or Max). The web version at claude.ai does not support Cowork.

**Before you start:** make sure you have the Claude desktop app installed and that you are signed in on a Pro or Max plan.

### The easy way: let Claude install it for you

You don't have to follow the steps below on your own. Open a **new chat in the Claude desktop app**, copy the entire block below, and paste it in. Claude becomes your install assistant and walks you through everything, one step at a time, checking your setup as you go.

```
I want to install a Claude skill called "aod-footage-organizer" from the AOD
Cowork Skill Pack. Please act as my personal install assistant and walk me through
it ONE STEP AT A TIME — wait for me to confirm each step before moving to the
next. I am not technical, so keep instructions simple and tell me exactly what
to click. Here is what we need to do together:

1. First, help me check that "Code execution and file creation" is turned ON.
   Tell me how to find it: Settings → Capabilities in this app. Wait until I
   confirm it's on.

2. Then send me this download link and tell me to click it. It saves a file
   called aod-footage-organizer.skill to my Downloads folder:
   https://github.com/erichroepke/aod-cowork-skill-pack/releases/download/v0.1.0-alpha/aod-footage-organizer.skill
   Tell me NOT to double-click the downloaded file — that does nothing.

3. Then walk me through installing it: in this app's left sidebar I click
   "Customize", then "Skills", then the "+" button, then "Create skill", then
   "Upload a skill", and pick the .skill file from my Downloads folder. Stay
   with me while I do this and answer questions if I get stuck.

4. Then have me check that the skill's toggle is ON in the Skills list.

5. Finally, tell me to start a NEW conversation (skills only load in fresh
   chats), give Claude access to a COPY of my footage folder — never my only
   original — using the + / folder button, and type: "Check my footage folder."

Important context for you, Claude: this skill audits and organizes documentary
footage folders. It is read-only until I approve moves, it can never delete
files, and I should always work on a backup copy of my footage. Remind me of
the backup rule before step 5. Start with step 1 now.
```

When you finish and Claude confirms the skill is working, come back here for the other two skills — or just follow the manual steps below if you prefer doing it yourself.

---

### The manual way (same steps, written out)

---

### Step 1 — turn on Code execution (do this once)

1. Open the Claude desktop app.
2. Click your profile icon or go to **Settings**.
3. Click **Capabilities**.
4. Find **"Code execution and file creation"** and make sure the toggle is **ON**.

If this setting is off, the skills cannot run. It only needs to be enabled once — Claude remembers it.

---

### Step 2 — download the skill files

Click each link below. The file will download to your **Downloads** folder.

- [`aod-footage-organizer.skill`](https://github.com/erichroepke/aod-cowork-skill-pack/releases/download/v0.1.0-alpha/aod-footage-organizer.skill)
- [`aod-footage-index.skill`](https://github.com/erichroepke/aod-cowork-skill-pack/releases/download/v0.1.0-alpha/aod-footage-index.skill)
- [`aod-footage-analyst.skill`](https://github.com/erichroepke/aod-cowork-skill-pack/releases/download/v0.1.0-alpha/aod-footage-analyst.skill)

Do not double-click these files in Finder and do not download the "Source code" zip. The steps below are the only way to install them.

---

### Step 3 — install the organizer skill

Start with just the organizer. The other two come later.

1. In the Claude desktop app, click **Customize** in the left sidebar.
2. Click **Skills**.
3. Click the **+** button → **Create skill** → **Upload a skill**.
4. A file picker opens. Navigate to your **Downloads** folder and select **`aod-footage-organizer.skill`**.
5. Claude reads the file and shows you a short description of what the skill does. This is normal.
6. Make sure the toggle next to the skill is switched **ON**.
7. The skill is now installed. It lives in your Claude account and follows you across your devices.

---

### Step 4 — run it for the first time

1. Start a **new Cowork conversation** (click the pencil/compose icon, or open a new chat).
2. Click the **+** button or the folder icon in the chat and give Claude access to your footage folder or drive. This is how Claude sees your files — you are granting access, not uploading anything.
3. Type exactly this:

   > **"Check my footage folder."**

Claude will scan the folder (read-only — nothing moves yet), show you the folder tree, flag any issues, and tell you what it found. That is the whole first experience. No Terminal, no setup, nothing to break.

---

### Step 5 — add the index and analyst when you're ready

Once you have the organizer running, install the other two skills the same way (Customize → Skills → + → Upload a skill):

**`aod-footage-index.skill`** — searchable memory of every drive you scan. Zero additional setup. After indexing a folder, you can ask things like "which drive has the interview about her father?" and get back a drive name, file path, and timecode.

**`aod-footage-analyst.skill`** — transcription, speaker identification, and face labeling. The first time you use this one, Claude will need to install some free tools on your Mac. Here is exactly what it installs and why:

| Tool | What it is | Why it's needed |
|------|-----------|-----------------|
| **Homebrew** | macOS package manager | Required to install ffmpeg and cmake |
| **ffmpeg** | Video processing tool | Extracts audio and frames from your footage |
| **cmake** | Build tool | Required to compile the face recognition library |
| **openai-whisper** | Transcription model (runs locally) | Converts speech to text with timecodes |
| **face_recognition** | Face detection library | Identifies and clusters faces across clips |
| **pyannote.audio** | Speaker diarization | Separates "who said what" in multi-person recordings |
| **numpy, Pillow, scikit-learn** | Python support libraries | Required by the above |

Claude walks you through each install step by step, asking permission before it does anything. If the session dies mid-install, just run it again — it picks up where it left off and skips anything already done. This setup happens once and never again.

---

### Important: give Claude folder access, not individual files

Do not drag video files directly into the chat. Instead, give Claude access to your footage folder or drive using the **+** / folder button, and let the skills scan that location. This preserves your folder structure, drive names, card structure, sidecar files, and everything the index and search depend on.

---

> **Start with the organizer. It needs no setup and gives you a result in minutes. Add the other two skills later, only when you want them.**

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

Copyright (c) 2026 Erich Roepke. All Rights Reserved.

For use by enrolled AOD members only. No redistribution, modification, or commercial use without written permission. No warranty of any kind — **back up your footage.** See [LICENSE](LICENSE) for full terms.

---

## What I use alongside this

These are tools I'm actively using in my own post workflow. None of them are required to run this pack — but if you want to go deeper into organizing your edits and managing projects, this is what I reach for.

**[Wideframe](https://try.wideframe.com)** — AI coworker for video editors. Where the AOD pack handles your raw footage (organizing, indexing, transcription), Wideframe goes further into the editorial layer: it understands your project semantically, lets you search your library by meaning, and can rough-assemble sequences from a natural-language description. It outputs real Premiere Pro project files — not synthetic video, actual assembled timelines from your footage. I've been running it alongside this pack and they complement each other well: use the pack to get your footage organized and indexed, then bring Wideframe in when you're ready to start cutting. It's a paid app (Mac only, Apple Silicon), but if you're spending serious time in post, it's worth looking at.

---

*Built for the Art of Documentary community. The pack finds and organizes your
material; for shaping the story it becomes, see [ARC](https://storyarc.co).*
