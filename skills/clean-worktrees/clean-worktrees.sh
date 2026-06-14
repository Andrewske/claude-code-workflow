#!/usr/bin/env bash
#
# clean-worktrees.sh — discover, classify, and clean stale git worktrees.
#
# Backs the /clean-worktrees skill. Safe by default (dry-run). Works from the
# Glade dev root (sweeps every child repo) or from inside a single repo.
#
# Usage:
#   clean-worktrees.sh [options] [repo ...]
#
# Options:
#   (default)        Dry-run: classify and print the summary, remove nothing.
#   --safe-only      Remove worktrees whose branch is gone-from-remote or merged
#                    into the default branch, plus matching orphan branches.
#                    Leaves needs-confirm + locked untouched.
#   --all            Also remove needs-confirm worktrees (unmerged/ahead/
#                    detached). DESTRUCTIVE — unpushed commits are lost.
#   --no-fetch       Skip `git fetch --prune` (faster; classification may be
#                    stale, so [gone] won't reflect remote deletions).
#   -h, --help       Show this help.
#
# Positional args: one or more repo paths to limit the sweep. If omitted, the
# scope is auto-detected (current repo, or all child repos at the dev root).
#
# Exit status: 0 on success; non-zero if any removal failed.
#
# Targets bash 3.2 (macOS default): no `set -u`, no associative arrays.

MODE="dry"            # dry | safe | all
DO_FETCH=1
REPOS=()
HAD_FAILURE=0

# ---- colors (only if stdout is a tty) ----
if [ -t 1 ]; then
  C_HDR=$'\033[1;36m'; C_SAFE=$'\033[32m'; C_WARN=$'\033[33m'
  C_LOCK=$'\033[35m'; C_ERR=$'\033[31m'; C_RST=$'\033[0m'
else
  C_HDR=""; C_SAFE=""; C_WARN=""; C_LOCK=""; C_ERR=""; C_RST=""
fi

usage() { sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

# ---- parse args ----
while [ $# -gt 0 ]; do
  case "$1" in
    --safe-only) MODE="safe" ;;
    --all)       MODE="all" ;;
    --dry-run)   MODE="dry" ;;
    --no-fetch)  DO_FETCH=0 ;;
    -h|--help)   usage 0 ;;
    -*)          echo "Unknown option: $1" >&2; usage 1 ;;
    *)           REPOS+=("$1") ;;
  esac
  shift
done

# ---- discover repos if none given ----
discover_repos() {
  if git rev-parse --git-dir >/dev/null 2>&1; then
    local common main
    common=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
    main=$(dirname "$common")
    REPOS=("$main")
  else
    local d
    for d in */; do
      [ -d "${d}.git" ] && REPOS+=("$PWD/${d%/}")
    done
  fi
}
[ ${#REPOS[@]} -eq 0 ] && discover_repos

if [ ${#REPOS[@]} -eq 0 ]; then
  echo "No git repositories found in $PWD" >&2
  exit 1
fi

# ---- default branch for a repo ----
default_branch() {
  local repo="$1" ref
  ref=$(git -C "$repo" symbolic-ref refs/remotes/origin/HEAD 2>/dev/null)
  if [ -n "$ref" ]; then echo "${ref#refs/remotes/origin/}"; return; fi
  if git -C "$repo" rev-parse --verify -q origin/main >/dev/null 2>&1; then echo main; return; fi
  if git -C "$repo" rev-parse --verify -q origin/master >/dev/null 2>&1; then echo master; return; fi
  echo main
}

# ---- per-repo processing ----
process_repo() {
  local repo="$1"
  local name; name=$(basename "$repo")
  local def; def=$(default_branch "$repo")
  local origin_def="origin/$def"
  local main_path="$repo"

  if [ "$DO_FETCH" -eq 1 ]; then
    git -C "$repo" fetch --prune >/dev/null 2>&1 \
      || echo "${C_WARN}  fetch failed for $name — classification may be stale${C_RST}"
  fi

  # gone branch names (fixed-string lookup), and the set of worktree branches.
  local gone_tmp wt_branches_tmp
  gone_tmp=$(mktemp); wt_branches_tmp=$(mktemp)
  git -C "$repo" for-each-ref --format='%(refname:short)%09%(upstream:track)' refs/heads/ \
    | awk -F'\t' '$2 ~ /\[gone\]/ {print $1}' > "$gone_tmp"

  is_gone()   { grep -qxF "$1" "$gone_tmp"; }
  is_merged() { git -C "$repo" merge-base --is-ancestor "$1" "$origin_def" 2>/dev/null; }

  # Display label: dir basename, but disambiguate when it collides with the
  # repo name (e.g. codex worktrees nested as <hash>/<repo-name>).
  disp() {
    local b; b=$(basename "$1")
    if [ "$b" = "$name" ]; then echo "$(basename "$(dirname "$1")")/$b"; else echo "$b"; fi
  }

  # Classification buckets (parallel arrays).
  SAFE_PATH=(); SAFE_BR=(); SAFE_KIND=()
  CONFIRM_DESC=(); CONFIRM_PATH=(); CONFIRM_BR=()
  LOCKED_DESC=(); STALE_PATH=()
  ORPHAN_BR=(); ORPHAN_KIND=()

  classify_wt() {
    local path="$1" branch="$2" locked="$3" detached="$4"
    [ -z "$path" ] && return
    [ "$path" = "$main_path" ] && return
    [ -n "$branch" ] && echo "$branch" >> "$wt_branches_tmp"
    if [ -n "$locked" ]; then
      LOCKED_DESC+=("$(disp "$path") -> ${branch:-detached} (locked: $locked)"); return
    fi
    if [ ! -d "$path" ]; then STALE_PATH+=("$path"); return; fi
    if [ "$detached" = "1" ]; then
      CONFIRM_DESC+=("$(disp "$path") -> detached HEAD")
      CONFIRM_PATH+=("$path"); CONFIRM_BR+=(""); return
    fi
    if is_gone "$branch"; then
      SAFE_PATH+=("$path"); SAFE_BR+=("$branch"); SAFE_KIND+=("gone")
    elif is_merged "$branch"; then
      SAFE_PATH+=("$path"); SAFE_BR+=("$branch"); SAFE_KIND+=("merged")
    else
      CONFIRM_DESC+=("$(disp "$path") -> $branch")
      CONFIRM_PATH+=("$path"); CONFIRM_BR+=("$branch")
    fi
  }

  # ---- parse worktree porcelain ----
  local line key val p="" b="" lk="" dt=0
  while IFS= read -r line; do
    if [ -z "$line" ]; then
      classify_wt "$p" "$b" "$lk" "$dt"; p=""; b=""; lk=""; dt=0; continue
    fi
    key="${line%% *}"; val="${line#* }"
    case "$key" in
      worktree) p="$val" ;;
      branch)   b="${val#refs/heads/}" ;;
      detached) dt=1 ;;
      locked)   if [ "$line" = "locked" ]; then lk="(no reason)"; else lk="$val"; fi ;;
    esac
  done < <(git -C "$repo" worktree list --porcelain)
  classify_wt "$p" "$b" "$lk" "$dt"

  # ---- orphan branches (local branch, no worktree, gone or merged) ----
  local br
  while IFS= read -r br; do
    [ -z "$br" ] && continue
    [ "$br" = "$def" ] && continue
    grep -qxF "$br" "$wt_branches_tmp" && continue
    if is_gone "$br"; then ORPHAN_BR+=("$br"); ORPHAN_KIND+=("gone")
    elif is_merged "$br"; then ORPHAN_BR+=("$br"); ORPHAN_KIND+=("merged"); fi
  done < <(git -C "$repo" for-each-ref --format='%(refname:short)' refs/heads/)

  # ---- CWD safety: never remove a worktree we're standing in ----
  local i kp=() kb=() kk=()
  for i in "${!SAFE_PATH[@]}"; do
    case "$PWD/" in
      "${SAFE_PATH[$i]}/"*)
        echo "${C_WARN}  skipping ${SAFE_PATH[$i]} — current directory is inside it${C_RST}" ;;
      *)
        kp+=("${SAFE_PATH[$i]}"); kb+=("${SAFE_BR[$i]}"); kk+=("${SAFE_KIND[$i]}") ;;
    esac
  done
  SAFE_PATH=("${kp[@]}"); SAFE_BR=("${kb[@]}"); SAFE_KIND=("${kk[@]}")

  # ---- report ----
  local n_safe=${#SAFE_PATH[@]} n_orphan=${#ORPHAN_BR[@]} n_conf=${#CONFIRM_DESC[@]}
  local n_lock=${#LOCKED_DESC[@]} n_stale=${#STALE_PATH[@]}
  if [ $((n_safe + n_orphan + n_conf + n_lock + n_stale)) -eq 0 ]; then
    rm -f "$gone_tmp" "$wt_branches_tmp"; return
  fi

  echo "${C_HDR}=== $name (${n_safe} safe wt, ${n_orphan} orphan br, ${n_conf} confirm, ${n_lock} locked, ${n_stale} stale) ===${C_RST}"
  if [ "$n_safe" -gt 0 ] || [ "$n_orphan" -gt 0 ]; then
    echo "${C_SAFE}  SAFE:${C_RST}"
    for i in "${!SAFE_PATH[@]}"; do
      printf '    [%s] %s -> %s\n' "${SAFE_KIND[$i]}" "$(disp "${SAFE_PATH[$i]}")" "${SAFE_BR[$i]}"
    done
    for i in "${!ORPHAN_BR[@]}"; do
      printf '    [orphan, %s] %s\n' "${ORPHAN_KIND[$i]}" "${ORPHAN_BR[$i]}"
    done
  fi
  if [ "$n_stale" -gt 0 ]; then
    echo "${C_SAFE}  STALE (prune):${C_RST}"
    for i in "${!STALE_PATH[@]}"; do printf '    %s\n' "${STALE_PATH[$i]}"; done
  fi
  if [ "$n_conf" -gt 0 ]; then
    echo "${C_WARN}  NEEDS CONFIRM:${C_RST}"
    for i in "${!CONFIRM_DESC[@]}"; do printf '    %s\n' "${CONFIRM_DESC[$i]}"; done
  fi
  if [ "$n_lock" -gt 0 ]; then
    echo "${C_LOCK}  LOCKED (skip):${C_RST}"
    for i in "${!LOCKED_DESC[@]}"; do printf '    %s\n' "${LOCKED_DESC[$i]}"; done
  fi

  # ---- act ----
  if [ "$MODE" != "dry" ]; then
    git -C "$repo" worktree prune
    for i in "${!SAFE_PATH[@]}"; do
      if git -C "$repo" worktree remove --force "${SAFE_PATH[$i]}"; then
        git -C "$repo" branch -D "${SAFE_BR[$i]}" >/dev/null 2>&1
      else
        echo "${C_ERR}  FAILED to remove ${SAFE_PATH[$i]}${C_RST}"; HAD_FAILURE=1
      fi
    done
    for i in "${!ORPHAN_BR[@]}"; do
      git -C "$repo" branch -D "${ORPHAN_BR[$i]}" >/dev/null 2>&1 \
        || { echo "${C_ERR}  FAILED to delete branch ${ORPHAN_BR[$i]}${C_RST}"; HAD_FAILURE=1; }
    done
    if [ "$MODE" = "all" ]; then
      for i in "${!CONFIRM_PATH[@]}"; do
        [ -d "${CONFIRM_PATH[$i]}" ] || continue
        if git -C "$repo" worktree remove --force "${CONFIRM_PATH[$i]}"; then
          [ -n "${CONFIRM_BR[$i]}" ] && git -C "$repo" branch -D "${CONFIRM_BR[$i]}" >/dev/null 2>&1
        else
          echo "${C_ERR}  FAILED to remove ${CONFIRM_PATH[$i]}${C_RST}"; HAD_FAILURE=1
        fi
      done
    fi
    git -C "$repo" worktree prune
    rmdir "$repo/.claude/worktrees" 2>/dev/null || true
  fi

  rm -f "$gone_tmp" "$wt_branches_tmp"
}

for repo in "${REPOS[@]}"; do
  process_repo "$repo"
done

if [ "$MODE" = "dry" ]; then
  echo
  echo "Dry-run only. Re-run with ${C_SAFE}--safe-only${C_RST} to remove the SAFE items."
fi

exit "$HAD_FAILURE"
