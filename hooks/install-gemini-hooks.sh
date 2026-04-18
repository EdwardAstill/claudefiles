#!/usr/bin/env bash
# install-gemini-hooks.sh — merge agentfiles hook configs into ~/.gemini/settings.json
#
# Usage:
#   ./hooks/install-gemini-hooks.sh [--dry-run] [--target <path>]

set -euo pipefail

SETTINGS="$HOME/.gemini/settings.json"
DRY_RUN=false
HOOK_BASE="~/.gemini/skills/hooks"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --target) SETTINGS="$2/settings.json"; HOOK_BASE="$2/skills/hooks"; shift 2 ;;
        *) shift ;;
    esac
done

# Ensure settings file exists
if [[ ! -f "$SETTINGS" ]]; then
    mkdir -p "$(dirname "$SETTINGS")"
    echo "{}" > "$SETTINGS"
    echo "  [created] $SETTINGS"
fi

HOOKS_CONFIG=$(cat <<EOF
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "name": "agentfiles-init",
            "type": "command",
            "command": "$HOOK_BASE/session-start"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "name": "caveman-mode",
            "type": "command",
            "command": "$HOOK_BASE/caveman-mode.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "name": "safety-gate",
            "type": "command",
            "command": "$HOOK_BASE/safety-gate.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "name": "skill-logger",
            "type": "command",
            "command": "$HOOK_BASE/skill-logger.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "name": "notify-stop",
            "type": "command",
            "command": "$HOOK_BASE/notify.py",
            "async": true
          }
        ]
      }
    ],
    "PermissionRequest": [
      {
        "hooks": [
          {
            "name": "notify-permission",
            "type": "command",
            "command": "$HOOK_BASE/notify.py",
            "async": true
          }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {
            "name": "notify",
            "type": "command",
            "command": "$HOOK_BASE/notify.py",
            "async": true
          }
        ]
      }
    ]
  }
}
EOF
)

if "$DRY_RUN"; then
    echo "  [dry-run] would merge hooks into $SETTINGS:"
    echo "$HOOKS_CONFIG"
    exit 0
fi

# Merge the hooks config into existing settings
if command -v jq &>/dev/null; then
    # Use jq for deep merging if available
    TMP_SETTINGS=$(mktemp)
    echo "$HOOKS_CONFIG" | jq -s '.[0] * .[1]' "$SETTINGS" - > "$TMP_SETTINGS"
    mv "$TMP_SETTINGS" "$SETTINGS"
    echo "  [updated] $SETTINGS (via jq)"
else
    # Fallback to Python if jq is missing
    python3 - "$SETTINGS" <<PYEOF
import json, sys

settings_path = sys.argv[1]
with open(settings_path) as f:
    settings = json.load(f)

new_hooks_data = json.loads('''$HOOKS_CONFIG''')
new_hooks = new_hooks_data.get("hooks", {})

# Deep-merge hooks
existing_hooks = settings.setdefault("hooks", {})

for hook_type, new_entries in new_hooks.items():
    existing_entries = existing_hooks.setdefault(hook_type, [])
    # Basic deduplication by command
    existing_commands = {h.get("command", "") for e in existing_entries for h in e.get("hooks", [])}
    for new_entry in new_entries:
        for h in new_entry.get("hooks", []):
            if h.get("command", "") not in existing_commands:
                existing_entries.append(new_entry)
                break

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
PYEOF
    echo "  [updated] $SETTINGS (via python fallback)"
fi
