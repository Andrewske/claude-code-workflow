#!/usr/bin/env bash
# Install skills from this repo into ~/.claude/skills/.
#
# Each repo skill is SYMLINKED as a whole directory. ~/.claude/skills also holds
# skills this repo does not own (Glade-specific ones); those are left untouched
# as real directories.
#
# Why directory links: Claude Code's Edit tool refuses to write through a file
# symlink, but writes straight through a file inside a symlinked directory. So a
# linked skill stays editable in place, and `git status` in this repo becomes the
# drift detector. The previous version copied instead, which is how the split of
# dual-review-protocol into SKILL.md + sections/ came within one install of being
# silently reverted to the 717-line monolith.
#
# The old rm -f-before-cp existed to avoid clobbering gstack-managed symlinks.
# gstack is uninstalled, and that logic is precisely what defeats linking, so it
# is gone.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/../skills" && pwd)"
DEST_DIR="$HOME/.claude/skills"

if [ ! -d "$SRC_DIR" ]; then
  echo "Error: skills directory not found at $SRC_DIR" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

linked=0
for src in "$SRC_DIR"/*/; do
  name="$(basename "$src")"
  src="${src%/}"
  dest="$DEST_DIR/$name"

  if [ -L "$dest" ]; then
    if [ "$(readlink "$dest")" = "$src" ]; then
      echo "  ok   $name (already linked)"
      linked=$((linked + 1))
      continue
    fi
    rm -f "$dest"
  elif [ -d "$dest" ]; then
    # Refuse to discard a real directory holding files the repo does not have.
    unowned=0
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
  echo "  link $name -> $src"
  linked=$((linked + 1))
done

echo
echo "Linked $linked skills into $DEST_DIR"
