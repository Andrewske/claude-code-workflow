#!/usr/bin/env bash
# Install commands and supporting scripts from this repo to ~/.claude/
# - Commands (.md files) → ~/.claude/commands/
# - Scripts (scripts/*.sh, excluding install-*.sh) → ~/.claude/scripts/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
CMD_SRC="$REPO_ROOT/commands"
CMD_DEST="$HOME/.claude/commands"
SCRIPTS_SRC="$SCRIPT_DIR"
SCRIPTS_DEST="$HOME/.claude/scripts"

if [ ! -d "$CMD_SRC" ]; then
  echo "Error: commands directory not found at $CMD_SRC"
  exit 1
fi

# Install commands
mkdir -p "$CMD_DEST"

count=0
while IFS= read -r file; do
  rel="${file#$CMD_SRC/}"

  basename="$(basename "$rel")"
  if [ "$basename" = "README.md" ]; then
    continue
  fi

  dir="$(dirname "$rel")"
  if [ "$dir" != "." ]; then
    mkdir -p "$CMD_DEST/$dir"
  fi

  cp "$file" "$CMD_DEST/$rel"
  count=$((count + 1))
  echo "  $rel"
done < <(find "$CMD_SRC" -name '*.md' -type f | sort)

echo ""
echo "Installed $count commands to $CMD_DEST"

# Install supporting scripts (skip install-*.sh)
mkdir -p "$SCRIPTS_DEST"

script_count=0
while IFS= read -r file; do
  basename="$(basename "$file")"

  # Skip installer scripts themselves
  case "$basename" in install-*) continue ;; esac

  cp "$file" "$SCRIPTS_DEST/$basename"
  chmod +x "$SCRIPTS_DEST/$basename"
  script_count=$((script_count + 1))
  echo "  $basename"
done < <(find "$SCRIPTS_SRC" -name '*.sh' -type f | sort)

echo ""
echo "Installed $script_count scripts to $SCRIPTS_DEST"
