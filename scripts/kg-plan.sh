#!/usr/bin/env bash
# kg-plan.sh — plan-storage helper for the `kg` knowledge repo.
#
# Plans live in a dedicated local git repo (~/dev/kg) with status encoded by
# folder location: plans/{repo}/{todo,doing,done}/{slug}/. Status transitions
# are `git mv` + commit, so git history IS the audit trail (no workflow-state.json).
#
# Subcommands:
#   init                              create + git-init ~/dev/kg (idempotent)
#   resolve                           derive REPO/BRANCH/SLUG/LINEAR_ID from cwd
#   create-todo <repo> <slug>         make plans/<repo>/todo/<slug>/ (collision-guarded)
#   move <repo> <slug> <from> <to>    git mv between status dirs + commit
#   list <repo> <status>              print slug dirs under plans/<repo>/<status>/
#
# All subcommands print KEY=value lines or a path to stdout. On failure they
# print a message to stderr and exit non-zero so the calling command can fall
# back to asking the user.

set -euo pipefail

KG_ROOT="${KG_ROOT:-$HOME/dev/kg}"

die() {
  echo "kg-plan: $*" >&2
  exit 1
}

# Ensure ~/dev/kg exists and is a git repo with the expected scaffold.
# Idempotent: a no-op when already initialized.
kg_init() {
  if [ -d "$KG_ROOT/.git" ]; then
    return 0
  fi
  mkdir -p "$KG_ROOT/plans" "$KG_ROOT/initiatives"
  if [ ! -f "$KG_ROOT/README.md" ]; then
    cat > "$KG_ROOT/README.md" <<'EOF'
# kg — knowledge repo

Two sibling trees:

- `plans/{repo}/{todo,doing,done}/{slug}/` — ephemeral implementation plans.
  Status is the folder. Transitions are `git mv` + commit (this repo's history
  is the audit trail). Managed by `kg-plan.sh` (the /plan:* commands).
- `initiatives/{slug}/GOAL.md` — durable knowledge-base layer (frontmatter
  status). The rest of the KB system lands here over time.

Local-only repo. No remote by design.
EOF
  fi
  # Keep empty trees in git.
  [ -f "$KG_ROOT/plans/.gitkeep" ] || touch "$KG_ROOT/plans/.gitkeep"
  [ -f "$KG_ROOT/initiatives/.gitkeep" ] || touch "$KG_ROOT/initiatives/.gitkeep"
  git -C "$KG_ROOT" init -q
  git -C "$KG_ROOT" add -A
  git -C "$KG_ROOT" commit -q -m "init: kg scaffold (plans/ + initiatives/)"
}

# Parse the GitHub/Git repo name from the origin remote URL.
# glade-ai/noodle-api(.git) -> noodle-api ; git@github.com:o/r.git -> r
repo_from_origin() {
  local url
  url="$(git remote get-url origin 2>/dev/null)" || return 1
  [ -n "$url" ] || return 1
  url="${url%.git}"
  url="${url%/}"
  basename "$url"
}

# Strip a single leading "user/" prefix (kevin/, feat/, claude/, ...).
strip_branch_prefix() {
  local b="$1"
  printf '%s' "${b#*/}"
}

kg_resolve() {
  local repo branch rest slug team num linear_id

  repo="$(repo_from_origin)" || die "no origin remote in cwd — pass repo explicitly"

  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" || die "not in a git repo"
  [ "$branch" != "HEAD" ] || die "detached HEAD — cannot derive ticket; pass slug explicitly"

  rest="$(strip_branch_prefix "$branch")"

  # Strict ticket derivation: require <team>-<num>-<title>. No match => caller
  # falls back to Linear lookup, then asks the user. Never mint a junk slug.
  if printf '%s' "$rest" | grep -Eq '^[a-z]+-[0-9]+-'; then
    slug="$rest"
    team="$(printf '%s' "$rest" | cut -d- -f1)"
    num="$(printf '%s' "$rest" | cut -d- -f2)"
    linear_id="${team}-${num}"
  else
    die "branch '$branch' has no <team>-<num>- ticket pattern — resolve via Linear or ask the user"
  fi

  printf 'REPO=%s\n' "$repo"
  printf 'BRANCH=%s\n' "$branch"
  printf 'SLUG=%s\n' "$slug"
  printf 'LINEAR_ID=%s\n' "$linear_id"
  printf 'KG_ROOT=%s\n' "$KG_ROOT"
  printf 'TODO_DIR=%s\n' "$KG_ROOT/plans/$repo/todo/$slug"
  printf 'DOING_DIR=%s\n' "$KG_ROOT/plans/$repo/doing/$slug"
  printf 'DONE_DIR=%s\n' "$KG_ROOT/plans/$repo/done/$slug"
}

# Print the status dir a slug currently lives in (todo|doing|done), or empty.
slug_status() {
  local repo="$1" slug="$2" s
  for s in todo doing done; do
    if [ -d "$KG_ROOT/plans/$repo/$s/$slug" ]; then
      printf '%s' "$s"
      return 0
    fi
  done
  return 1
}

kg_create_todo() {
  local repo="$1" slug="$2" existing
  [ -n "$repo" ] && [ -n "$slug" ] || die "usage: create-todo <repo> <slug>"
  kg_init

  if existing="$(slug_status "$repo" "$slug")"; then
    echo "EXISTS=$existing" >&2
    echo "PATH=$KG_ROOT/plans/$repo/$existing/$slug" >&2
    die "plan '$slug' already exists under '$existing/' for $repo — resume or overwrite"
  fi

  mkdir -p "$KG_ROOT/plans/$repo/todo/$slug"
  printf '%s\n' "$KG_ROOT/plans/$repo/todo/$slug"
}

kg_move() {
  local repo="$1" slug="$2" from="$3" to="$4" src dst
  [ -n "$repo" ] && [ -n "$slug" ] && [ -n "$from" ] && [ -n "$to" ] \
    || die "usage: move <repo> <slug> <from> <to>"
  case "$from" in todo|doing|done) ;; *) die "bad <from> '$from' (todo|doing|done)" ;; esac
  case "$to" in todo|doing|done) ;; *) die "bad <to> '$to' (todo|doing|done)" ;; esac
  kg_init

  src="$KG_ROOT/plans/$repo/$from/$slug"
  dst="$KG_ROOT/plans/$repo/$to/$slug"
  [ -d "$src" ] || die "source not found: $src"
  [ ! -e "$dst" ] || die "target already exists: $dst (refusing to clobber)"

  mkdir -p "$KG_ROOT/plans/$repo/$to"
  git -C "$KG_ROOT" mv "$src" "$dst"
  git -C "$KG_ROOT" commit -q -m "plan: move $slug $from->$to"
  printf '%s\n' "$dst"
}

kg_list() {
  local repo="$1" status="$2" dir d
  [ -n "$repo" ] && [ -n "$status" ] || die "usage: list <repo> <status>"
  dir="$KG_ROOT/plans/$repo/$status"
  [ -d "$dir" ] || return 0
  for d in "$dir"/*/; do
    [ -d "$d" ] || continue
    basename "$d"
  done
}

main() {
  local cmd="${1:-}"
  [ -n "$cmd" ] || die "usage: kg-plan.sh <init|resolve|create-todo|move|list> [args]"
  shift || true
  case "$cmd" in
    init)        kg_init ;;
    resolve)     kg_resolve ;;
    create-todo) kg_create_todo "${1:-}" "${2:-}" ;;
    move)        kg_move "${1:-}" "${2:-}" "${3:-}" "${4:-}" ;;
    list)        kg_list "${1:-}" "${2:-}" ;;
    *)           die "unknown subcommand: $cmd" ;;
  esac
}

main "$@"
