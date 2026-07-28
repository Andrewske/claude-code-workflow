#!/usr/bin/env bash
# Report drift between this repo and ~/.claude. Read-only: copies nothing.
#
# Symlinked directories cannot drift, so they are only checked for still being
# correctly linked. Copied content (the four top-level commands, scripts/) is
# compared byte-for-byte and its direction of drift reported, since that is the
# part an install would silently overwrite.
#
# Run this before install-commands.sh / install-skills.sh, or any time you
# suspect ~/.claude and the repo have diverged.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
drift=0

newer_side() {
  local a="$1" b="$2" at bt
  at=$(stat -f %m "$a" 2>/dev/null || echo 0)
  bt=$(stat -f %m "$b" 2>/dev/null || echo 0)
  if [ "$at" -gt "$bt" ]; then echo "REPO newer"; else echo "LOCAL newer"; fi
}

echo "=== linked command directories ==="
for name in plan qol; do
  src="$REPO/commands/$name"
  dest="$HOME/.claude/commands/$name"
  if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
    echo "  ok       commands/$name -> repo"
  elif [ -L "$dest" ]; then
    echo "  RELINK   commands/$name points at $(readlink "$dest")"; drift=1
  elif [ -d "$dest" ]; then
    echo "  UNLINKED commands/$name is a real directory — run install-commands.sh"; drift=1
  else
    echo "  MISSING  commands/$name"; drift=1
  fi
done

echo "=== linked skills ==="
for src in "$REPO"/skills/*/; do
  src="${src%/}"
  name="$(basename "$src")"
  dest="$HOME/.claude/skills/$name"
  if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
    echo "  ok       skills/$name -> repo"
  elif [ -L "$dest" ]; then
    echo "  RELINK   skills/$name points at $(readlink "$dest")"; drift=1
  elif [ -d "$dest" ]; then
    echo "  UNLINKED skills/$name is a real directory — run install-skills.sh"; drift=1
  else
    echo "  MISSING  skills/$name"; drift=1
  fi
done

echo "=== copied top-level commands ==="
while IFS= read -r f; do
  base="$(basename "$f")"
  [ "$base" = "README.md" ] && continue
  dest="$HOME/.claude/commands/$base"
  if [ ! -e "$dest" ]; then
    echo "  MISSING  $base"; drift=1
  elif ! cmp -s "$f" "$dest"; then
    echo "  DRIFT    $base ($(newer_side "$f" "$dest"))"; drift=1
  fi
done < <(find "$REPO/commands" -maxdepth 1 -name '*.md' -type f | sort)

echo "=== copied scripts ==="
while IFS= read -r f; do
  base="$(basename "$f")"
  case "$base" in install-*) continue ;; esac
  dest="$HOME/.claude/scripts/$base"
  if [ ! -e "$dest" ]; then
    echo "  MISSING  $base"; drift=1
  elif ! cmp -s "$f" "$dest"; then
    echo "  DRIFT    $base ($(newer_side "$f" "$dest"))"; drift=1
  fi
done < <(find "$REPO/scripts" -name '*.sh' -type f | sort)

echo
if [ "$drift" -eq 0 ]; then
  echo "RESULT: in sync."
  exit 0
fi
echo "RESULT: drift above. LOCAL newer means an install would OVERWRITE your edits —"
echo "        copy them into the repo first."
exit 1
