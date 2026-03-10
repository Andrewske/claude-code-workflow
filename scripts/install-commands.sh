#!/usr/bin/env bash
# Install commands from this repo to ~/.claude/commands/
# Copies all .md files (preserving directory structure), skips README.md files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$SCRIPT_DIR/../commands"
DEST_DIR="$HOME/.claude/commands"

if [ ! -d "$SRC_DIR" ]; then
  echo "Error: commands directory not found at $SRC_DIR"
  exit 1
fi

mkdir -p "$DEST_DIR"

count=0
while IFS= read -r file; do
  # Get relative path from commands/
  rel="${file#$SRC_DIR/}"

  # Skip README.md files
  basename="$(basename "$rel")"
  if [ "$basename" = "README.md" ]; then
    continue
  fi

  # Create subdirectory if needed
  dir="$(dirname "$rel")"
  if [ "$dir" != "." ]; then
    mkdir -p "$DEST_DIR/$dir"
  fi

  cp "$file" "$DEST_DIR/$rel"
  count=$((count + 1))
  echo "  $rel"
done < <(find "$SRC_DIR" -name '*.md' -type f | sort)

echo ""
echo "Installed $count commands to $DEST_DIR"
