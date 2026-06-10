# AOD Footage Pack

**Claude becomes your post supervisor.** Three skills for documentary filmmakers:

| Skill | What it does | What you say |
|-------|--------------|--------------|
| 🗂 **footage-organizer** | Audits your drive against a professional folder structure, then — with your approval — safely moves footage into place. Checksum-verified, undo log, physically incapable of deleting. | *"Check my footage folder"* · *"Organize this drive"* |
| 🔎 **footage-index** | A searchable memory of every drive you've ever scanned. Ask for a moment, get the drive, file, and timecode — even if that drive is on a shelf. | *"Where's the interview where she talks about her father?"* |
| 🎞 **footage-analyst** | Transcribes footage, identifies who's on screen (you label the faces), breaks down speakers, makes a beautiful HTML report. | *"Transcribe this clip"* · *"Who's in this video?"* |

Everything runs **on your computer**. No footage is ever uploaded anywhere.

---

## 🚨 Read this first

These skills work with camera originals — possibly the only copy of irreplaceable
material. They are built around one rule: **they cannot delete your files.** The
organizer only *moves* footage, only after you approve a plan, only after you confirm
a backup exists, and it verifies every file with checksums before and after (the same
xxHash64 verification used by Hedge and OffShoot). Every move is logged and undoable.

That said: **you are responsible for keeping a backup of your footage.** No warranty.
Rule one of media management — never work on the only copy.

---

## Install (first time, ~2 minutes)

You need the **Claude desktop app** with Cowork. That's it — no other software.

1. Go to this repo's **[Releases page](../../releases)** (link also in your AOD course
   materials)
2. Download the skill files — they look like `footage-organizer.skill`
3. **Double-click the downloaded file** — Claude will offer to install the skill.
   If double-clicking doesn't offer that on your machine: open Claude → Settings →
   Capabilities/Skills → **drag the file in**. Same result.
4. Open a Cowork session, connect your footage folder, and say:
   **"check my footage folder"**

The skill takes it from there — it introduces itself, looks at your drive (reading
only), and walks you through everything conversationally. If a skill ever needs a
helper installed (like the transcription engine), **it asks your permission and does
it for you** — you never have to open Terminal.

> 🧭 **Start with footage-organizer.** It needs nothing installed and gives you a
> full report of your drive in about a minute. Add the index next ("index this
> drive"). Install the analyst when you want transcripts and face ID — its one-time
> setup downloads ~4 GB of free, local AI tools and takes 10–20 minutes, and the
> skill walks you through all of it.

## Updating

Download the new `.skill` files from Releases and install them the same way — the new
version replaces the old one.

---

## What's inside (for the curious)

```
footage-organizer/   SKILL.md + scan_tree.py, checksum_scan.py, move_with_manifest.py
footage-index/       SKILL.md + footage_index.py        (SQLite, all local)
footage-analyst/     SKILL.md + extract_faces.py, analyze_footage.py
build.sh             packages the .skill files (maintainers only)
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
with rules lives in [footage-organizer/SKILL.md](footage-organizer/SKILL.md).

## License

MIT. Use freely, share freely. No warranty of any kind — **back up your footage.**

---

*Built for the Art of Documentary community. The pack finds and organizes your
material; for shaping the story it becomes, see [ARC](https://storyarc.co).*
