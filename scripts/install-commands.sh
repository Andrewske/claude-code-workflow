#!/usr/bin/env bash
# Install commands and supporting scripts from this repo into ~/.claude/.
#
# Directories that this repo owns wholesale (commands/plan, commands/qol) are
# SYMLINKED, so editing a command in ~/.claude edits the repo and `git status`
# is the drift detector. Copying them instead is what let nine files silently
# drift local-newer and silently reverted best-idea.md on 2026-06-14.
#
# Why directories and not individual files: Claude Code's Edit tool refuses to
# write through a file symlink ("Refusing to write through symlink"), but writes
# straight through a file that merely lives inside a symlinked directory. So
# directory links are editable in place and per-file links are not.
#
# The four loose commands/*.md at the top level cannot be directory-linked
# (~/.claude/commands holds many files this repo does not own), so they stay
# copies. scripts/check-sync.sh covers them.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CMD_SRC="$REPO_ROOT/commands"
CMD_DEST="$HOME/.claude/commands"
SCRIPTS_DEST="$HOME/.claude/scripts"

# Directories this repo owns wholesale -> symlinked.
LINKED_DIRS=(plan qol)

if [ ! -d "$CMD_SRC" ]; then
  echo "Error: commands directory not found at $CMD_SRC" >&2
  exit 1
fi

mkdir -p "$CMD_DEST"

link_dir() {
  local name="$1"
  local src="$CMD_SRC/$name"
  local dest="$CMD_DEST/$name"

  [ -d "$src" ] || { echo "  skip $name/ (not in repo)"; return; }

  if [ -L "$dest" ]; then
    if [ "$(readlink "$dest")" = "$src" ]; then
      echo "  ok   $name/ (already linked)"
      return
    fi
    rm -f "$dest"
  elif [ -d "$dest" ]; then
    # Refuse to discard a real directory holding files the repo does not have.
    local unowned=0
    while IFS= read -r f; do
      rel="${f#$dest/}"
      [ -e "$src/$rel" ] || { echo "  !!   $name/$rel exists only in ~/.claude" >&2; unowned=1; }
    done < <(find "$dest" -type f | sort)
    if [ "$unowned" -eq 1 ]; then
      echo "Error: $dest holds files absent from the repo; copy them in first." >&2
      exit 1
    fi
    rm -rf "$dest"
  fi

  ln -s "$src" "$dest"
  echo "  link $name/ -> $src"
}

echo "Linking repo-owned command directories:"
for d in "${LINKED_DIRS[@]}"; do
  link_dir "$d"
done

echo "Copying top-level commands (cannot be directory-linked):"
copied=0
while IFS= read -r file; do
  base="$(basename "$file")"
  [ "$base" = "README.md" ] && continue
  cp "$file" "$CMD_DEST/$base"
  copied=$((copied + 1))
  echo "  copy $base"
done < <(find "$CMD_SRC" -maxdepth 1 -name '*.md' -type f | sort)

echo "Copying supporting scripts:"
mkdir -p "$SCRIPTS_DEST"
script_count=0
while IFS= read -r file; do
  base="$(basename "$file")"
  case "$base" in install-*) continue ;; esac
  cp "$file" "$SCRIPTS_DEST/$base"
  chmod +x "$SCRIPTS_DEST/$base"
  script_count=$((script_count + 1))
  echo "  copy $base"
done < <(find "$SCRIPT_DIR" -name '*.sh' -type f | sort)

echo
echo "Linked ${#LINKED_DIRS[@]} directories, copied $copied commands and $script_count scripts."
