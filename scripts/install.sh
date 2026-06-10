#!/bin/bash
# Install the Loops skill family into Claude Code (real copies, no symlinks).
set -euo pipefail
SRC="$(cd "$(dirname "$0")/../skills" && pwd)"
DEST="${1:-$HOME/.claude/skills}"
mkdir -p "$DEST"
for skill in "$SRC"/*/; do
  name="$(basename "$skill")"
  rm -rf "$DEST/$name"
  cp -R "$skill" "$DEST/$name"
  echo "installed $name -> $DEST/$name"
done
