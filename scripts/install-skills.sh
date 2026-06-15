#!/usr/bin/env bash
# Install skills from this repo to ~/.claude/skills/
# Copies all files (preserving directory structure).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$SCRIPT_DIR/../skills"
DEST_DIR="$HOME/.claude/skills"

if [ ! -d "$SRC_DIR" ]; then
  echo "Error: skills directory not found at $SRC_DIR"
  exit 1
fi

mkdir -p "$DEST_DIR"

count=0
while IFS= read -r file; do
  # Get relative path from skills/
  rel="${file#$SRC_DIR/}"

  # Create subdirectory if needed
  dir="$(dirname "$rel")"
  if [ "$dir" != "." ]; then
    mkdir -p "$DEST_DIR/$dir"
  fi

  # Remove any existing dest first: if it's a symlink (e.g. a gstack-managed
  # skill linking into ~/.claude/skills/gstack/), a plain `cp` would follow the
  # link and overwrite the link *target* instead of replacing the link with our
  # real file. rm -f guarantees a real-file copy lands.
  rm -f "$DEST_DIR/$rel"
  cp "$file" "$DEST_DIR/$rel"
  count=$((count + 1))
  echo "  $rel"
done < <(find "$SRC_DIR" -type f | sort)

echo ""
echo "Installed $count skill files to $DEST_DIR"
