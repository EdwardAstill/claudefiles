#!/usr/bin/env bash
# install-hooks.sh — merge agentfiles hook configs into ~/.claude/settings.json
#
# Usage:
#   ./hooks/install-hooks.sh [--dry-run]

set -euo pipefail

SETTINGS="$HOME/.claude/settings.json"
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
    esac
done

# Ensure settings file exists
if [[ ! -f "$SETTINGS" ]]; then
    mkdir -p "$(dirname "$SETTINGS")"
    echo "{}" > "$SETTINGS"
    echo "  [created] $SETTINGS"
fi

HOOKS_CONFIG=$(cat <<'EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/skills/hooks/safety-gate.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/skills/hooks/skill-logger.py"
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

new_hooks = $HOOKS_CONFIG
existing_hooks = settings.setdefault("hooks", {})

for hook_type, new_entries in new_hooks["hooks"].items():
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

echo "  Done. Hook scripts expected at ~/.claude/skills/hooks/"
echo "  Run: af install  to install hook scripts to that location."
