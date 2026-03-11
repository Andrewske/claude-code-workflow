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

  cp "$file" "$DEST_DIR/$rel"
  count=$((count + 1))
  echo "  $rel"
done < <(find "$SRC_DIR" -type f | sort)

echo ""
echo "Installed $count skill files to $DEST_DIR"
