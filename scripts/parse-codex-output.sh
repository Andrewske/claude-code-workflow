#!/usr/bin/env bash
# Parse JSONL output from `codex exec --json`
# Usage: parse-codex-output.sh <file>
# Output: Two sections separated by a marker line:
#   === USAGE ===
#   {"input": N, "output": N, "cached": N}
#   === RESPONSE ===
#   <concatenated agent_message text>

set -euo pipefail

FILE="${1:?Usage: parse-codex-output.sh <file>}"

if [ ! -f "$FILE" ]; then
  echo "Error: file not found: $FILE" >&2
  exit 1
fi

# Extract usage totals from turn.completed events
echo "=== USAGE ==="
jq -s '
  [ .[] | select(.type == "turn.completed") | .usage // {} ]
  | {
      input: (map(.input_tokens // 0) | add // 0),
      output: (map(.output_tokens // 0) | add // 0),
      cached: (map(.input_tokens_details.cached_tokens // 0) | add // 0)
    }
' "$FILE"

# Extract and concatenate agent_message text from item.completed events
echo "=== RESPONSE ==="
jq -r '
  select(.item.type == "agent_message")
  | .item.text // empty
' "$FILE"
