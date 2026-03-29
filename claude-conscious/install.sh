#!/usr/bin/env bash
# Install Claude Conscious — session telemetry and self-improvement system.
#
# What this does:
#   1. Creates ~/.claude/conscious/ directory structure
#   2. Copies src/conscious_hook.py and src/parse_session.py to ~/.claude/conscious/scripts/
#   3. Registers conscious_hook.py as a Stop hook in ~/.claude/settings.json
#   4. Installs commands/review-suggestions.md to ~/.claude/commands/
#
# Idempotent: running twice does not duplicate anything.
# Use --uninstall to remove everything cleanly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
CONSCIOUS_DIR="$CLAUDE_DIR/conscious"
SCRIPTS_DEST="$CONSCIOUS_DIR/scripts"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
HOOK_SCRIPT="$SCRIPTS_DEST/conscious_hook.py"
PLIST_LABEL="com.claude-conscious.analyze"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1" >&2; }

# --- Uninstall ---

if [ "${1:-}" = "--uninstall" ]; then
    echo "Uninstalling Claude Conscious..."

    # Remove hook from settings.json
    if [ -f "$SETTINGS_FILE" ]; then
        python3 -c "
import json
path = '$SETTINGS_FILE'
hook_cmd = '$HOOK_SCRIPT'
with open(path) as f:
    settings = json.load(f)
hooks = settings.get('hooks', {})
stop_hooks = hooks.get('Stop', [])
# Remove entries containing our hook command
cleaned = []
for entry in stop_hooks:
    inner = entry.get('hooks', [])
    inner = [h for h in inner if h.get('command', '') != hook_cmd]
    if inner:
        entry['hooks'] = inner
        cleaned.append(entry)
if cleaned:
    hooks['Stop'] = cleaned
elif 'Stop' in hooks:
    del hooks['Stop']
if hooks:
    settings['hooks'] = hooks
elif 'hooks' in settings:
    del settings['hooks']
with open(path, 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
" && info "Removed hook from settings.json" || warn "Could not update settings.json"
    fi

    # Remove installed scripts
    [ -f "$SCRIPTS_DEST/conscious_hook.py" ] && rm "$SCRIPTS_DEST/conscious_hook.py" && info "Removed conscious_hook.py"
    [ -f "$SCRIPTS_DEST/parse_session.py" ] && rm "$SCRIPTS_DEST/parse_session.py" && info "Removed parse_session.py"

    # Remove command
    [ -f "$CLAUDE_DIR/commands/review-suggestions.md" ] && rm "$CLAUDE_DIR/commands/review-suggestions.md" && info "Removed review-suggestions command"

    # Unload and remove launchd plist
    if [ -f "$PLIST_DEST" ]; then
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
        rm "$PLIST_DEST"
        info "Removed daily analysis cron"
    fi

    # Remove analysis script
    [ -f "$SCRIPTS_DEST/analyze_sessions.py" ] && rm "$SCRIPTS_DEST/analyze_sessions.py" && info "Removed analyze_sessions.py"

    echo ""
    echo "Uninstall complete. Telemetry data preserved at $CONSCIOUS_DIR/telemetry/"
    echo "To remove all data: rm -rf $CONSCIOUS_DIR"
    exit 0
fi

# --- Install ---

echo "Installing Claude Conscious..."
echo ""

# 1. Create directory structure
for dir in telemetry suggestions metrics scripts; do
    mkdir -p "$CONSCIOUS_DIR/$dir"
done
info "Created directory structure at $CONSCIOUS_DIR/"

# 2. Copy scripts
cp "$SCRIPT_DIR/src/parse_session.py" "$SCRIPTS_DEST/parse_session.py"
cp "$SCRIPT_DIR/src/conscious_hook.py" "$SCRIPTS_DEST/conscious_hook.py"
chmod +x "$SCRIPTS_DEST/conscious_hook.py"
info "Installed scripts to $SCRIPTS_DEST/"

# 3. Register Stop hook in settings.json
if [ ! -f "$SETTINGS_FILE" ]; then
    echo '{}' > "$SETTINGS_FILE"
    info "Created $SETTINGS_FILE"
fi

python3 -c "
import json

path = '$SETTINGS_FILE'
hook_cmd = '$HOOK_SCRIPT'

with open(path) as f:
    settings = json.load(f)

hooks = settings.setdefault('hooks', {})
stop_hooks = hooks.setdefault('Stop', [])

# Check if already registered (idempotent) — search inside hooks arrays
already_registered = any(
    any(inner.get('command', '') == hook_cmd for inner in entry.get('hooks', []))
    for entry in stop_hooks
)

if not already_registered:
    stop_hooks.append({
        'matcher': '',
        'hooks': [{'type': 'command', 'command': hook_cmd}],
    })

settings['hooks']['Stop'] = stop_hooks

with open(path, 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
" && info "Registered Stop hook in settings.json" || error "Failed to register hook"

# 4. Install commands (if commands dir exists in repo)
if [ -f "$SCRIPT_DIR/commands/review-suggestions.md" ]; then
    mkdir -p "$CLAUDE_DIR/commands"
    cp "$SCRIPT_DIR/commands/review-suggestions.md" "$CLAUDE_DIR/commands/review-suggestions.md"
    info "Installed /review-suggestions command"
else
    warn "commands/review-suggestions.md not found (will be created in Phase 3)"
fi

# 5. Copy backfill and analysis scripts
for script in backfill_telemetry.py analyze_sessions.py; do
    if [ -f "$SCRIPT_DIR/src/$script" ]; then
        cp "$SCRIPT_DIR/src/$script" "$SCRIPTS_DEST/$script"
    fi
done
info "Installed analysis scripts"

# 6. Install daily cron via launchd
mkdir -p "$CONSCIOUS_DIR/logs"
if [ -f "$SCRIPT_DIR/src/$PLIST_LABEL.plist" ]; then
    # Update paths in plist to match current user
    sed "s|/Users/kevinandrews|$HOME|g" "$SCRIPT_DIR/src/$PLIST_LABEL.plist" > "$PLIST_DEST"
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    launchctl load "$PLIST_DEST"
    info "Installed daily analysis cron (6:37 AM)"
else
    warn "Plist not found, skipping daily cron"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Start a Claude Code session and interact normally"
echo "  2. After Claude responds, check: ls ~/.claude/conscious/telemetry/"
echo "  3. To backfill historical data: python3 $SCRIPTS_DEST/backfill_telemetry.py"
echo ""
echo "To uninstall: $0 --uninstall"
