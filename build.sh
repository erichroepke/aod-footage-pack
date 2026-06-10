#!/bin/bash
# build.sh — packages each skill folder into a .skill file in dist/
#
# .skill files are zip archives containing the skill folder at the zip root
# (e.g. footage-organizer/SKILL.md). They are BUILT by this script, never
# hand-made — that's how we keep one canonical source and zero version drift.
#
# Usage: ./build.sh

set -euo pipefail
cd "$(dirname "$0")"

SKILLS=(footage-organizer footage-index footage-analyst)
mkdir -p dist

echo "📦 Building AOD Footage Pack"
echo

for skill in "${SKILLS[@]}"; do
  if [ ! -f "$skill/SKILL.md" ]; then
    echo "❌ $skill/SKILL.md missing — aborting"
    exit 1
  fi
  out="dist/${skill}.skill"
  [ -f "$out" ] && mv "$out" "$out.previous"   # keep last build, never delete
  # -X strips extended attrs; exclude junk
  zip -X -r "$out" "$skill" \
    -x "*/.DS_Store" -x "*/__pycache__/*" -x "*/_work/*" >/dev/null

  # verify: non-empty and a valid zip that contains the SKILL.md
  size=$(stat -f%z "$out")
  if [ "$size" -lt 1000 ]; then
    echo "❌ $out is suspiciously small ($size bytes) — aborting"
    exit 1
  fi
  unzip -t "$out" >/dev/null || { echo "❌ $out failed zip integrity"; exit 1; }
  unzip -l "$out" | grep -q "$skill/SKILL.md" || { echo "❌ $out missing SKILL.md"; exit 1; }
  echo "  ✅ $out ($(du -h "$out" | cut -f1 | tr -d ' '))"
done

echo
echo "Done. Upload the dist/*.skill files to a GitHub Release."
