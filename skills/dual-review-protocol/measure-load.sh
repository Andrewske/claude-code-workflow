#!/usr/bin/env bash
# measure-load.sh — baseline token-load instrumentation for the dual-review commands.
#
# Maps every file pulled into Claude's CONTEXT during a /dual-code-review run to
# the phase it loads at, and estimates tokens (bytes/4 heuristic — no tiktoken).
# Codex-side files (output schemas, the rendered gpt-prompt temp file) are NOT
# Claude context and are listed separately as a reference, excluded from totals.
#
# Usage: ./measure-load.sh [command]   (command defaults to dual-code-review)
# Output: a table grouped by UPFRONT vs LAZY, with per-group + grand totals.

set -euo pipefail

CLAUDE="$HOME/.claude"
SKILL="$CLAUDE/skills/dual-review-protocol"

# est_tokens <file>  -> echoes "<bytes> <est_tokens>"; missing file -> "0 0 (MISSING)"
est() {
  local f="$1"
  if [[ ! -f "$f" ]]; then printf '0 0 MISSING'; return; fi
  local bytes tok
  bytes=$(wc -c <"$f" | tr -d ' ')
  tok=$(( (bytes + 2) / 4 ))
  printf '%s %s OK' "$bytes" "$tok"
}

# row <phase> <load-class> <label> <path>
declare -a ROWS
add() {
  local phase="$1" cls="$2" label="$3" path="$4"
  read -r bytes tok status <<<"$(est "$path")"
  ROWS+=("$cls|$phase|$label|$bytes|$tok|$status")
}

# ---- Load graph for /dual-code-review (post-split: SKILL.md is a thin index) ----
# UPFRONT = read before any review work (command body + the index + voice setup).
add "start"     UPFRONT "command: dual-code-review.md"        "$CLAUDE/commands/dual-code-review.md"
add "start"     UPFRONT "skill: dual-review-protocol INDEX"   "$SKILL/SKILL.md"
add "start §0"  UPFRONT "skill: outbound-prose-setup"         "$CLAUDE/skills/outbound-prose-setup/SKILL.md"

# LAZY = read at a specific phase, only when that phase runs.
add "1.5"  LAZY "skill: pre-commit-check"                 "$CLAUDE/skills/pre-commit-check/SKILL.md"
add "1.6"  LAZY "sections/tier.md (§12)"                  "$SKILL/sections/tier.md"
add "2"    LAZY "sections/codex.md (§1,§10)"              "$SKILL/sections/codex.md"
add "2"    LAZY "sections/findings.md (§2)"               "$SKILL/sections/findings.md"
add "2"    LAZY "sections/lenses.md (§3,§14)"             "$SKILL/sections/lenses.md"
add "2"    LAZY "structural-lens.md"                      "$SKILL/structural-lens.md"
add "2"    LAZY "templates/gpt-prompt-code.md"            "$SKILL/templates/gpt-prompt-code.md"
add "3"    LAZY "sections/triage.md (§4,§5,§13)"          "$SKILL/sections/triage.md"
add "4*"   LAZY "sections/debate.md (§6, gated)"          "$SKILL/sections/debate.md"
add "3"    LAZY "templates/triage.md"                     "$SKILL/templates/triage.md"
add "4"    LAZY "templates/debate.md"                     "$SKILL/templates/debate.md"
add "5-6"  LAZY "sections/routing-present.md (§7-9,§11)"  "$SKILL/sections/routing-present.md"
add "6 go" LAZY "sections/resolution-code.md (Phase 6)"   "$SKILL/sections/resolution-code.md"

# CODEX-SIDE = passed to codex by path; never enters Claude context. Reference only.
add "2"    CODEX "schemas/findings-code.json"            "$SKILL/schemas/findings-code.json"

print_group() {
  local want="$1" title="$2"
  local sum_b=0 sum_t=0 n=0
  printf '\n%s\n' "$title"
  printf '  %-6s  %-38s %9s %9s\n' "PHASE" "FILE" "BYTES" "~TOKENS"
  printf '  %s\n' "-------------------------------------------------------------------------"
  local r cls phase label bytes tok status
  for r in "${ROWS[@]}"; do
    IFS='|' read -r cls phase label bytes tok status <<<"$r"
    [[ "$cls" == "$want" ]] || continue
    local mark=""; [[ "$status" == "MISSING" ]] && mark="  <-- MISSING"
    printf '  %-6s  %-38s %9s %9s%s\n' "$phase" "$label" "$bytes" "$tok" "$mark"
    sum_b=$((sum_b + bytes)); sum_t=$((sum_t + tok)); n=$((n + 1))
  done
  printf '  %s\n' "-------------------------------------------------------------------------"
  printf '  %-6s  %-38s %9s %9s\n' "" "subtotal ($n files)" "$sum_b" "$sum_t"
  GROUP_TOK=$sum_t
}

echo "=================================================================================="
echo " dual-code-review — Claude-context load baseline   ($(date +%Y-%m-%d))"
echo " token estimate = bytes/4 (no tiktoken); within ~10% for markdown"
echo "=================================================================================="

print_group UPFRONT "[UPFRONT]  read before any review work — paid on EVERY run"
UPFRONT_TOK=$GROUP_TOK
print_group LAZY    "[LAZY]     read per-phase — paid only when that phase runs"
LAZY_TOK=$GROUP_TOK
print_group CODEX   "[CODEX-SIDE]  passed to codex by path — NOT Claude context (reference)"

echo ""
echo "=================================================================================="
printf ' UPFRONT (every run):        ~%5d tokens\n' "$UPFRONT_TOK"
printf ' LAZY (max, all phases hit): ~%5d tokens\n' "$LAZY_TOK"
printf ' Claude-context total (max): ~%5d tokens\n' "$((UPFRONT_TOK + LAZY_TOK))"
echo "=================================================================================="
echo " Note: schemas/ + the rendered /tmp gpt-prompt are codex-side, excluded above."
