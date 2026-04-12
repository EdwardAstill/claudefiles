#!/usr/bin/env bash
# install-hooks.sh — merge claudefiles hook configs into ~/.claude/settings.json
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
        "matcher": "Read",
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

# Use Python to deep-merge the hooks config into existing settings
python3 - "$SETTINGS" <<PYEOF
import json, sys, copy

settings_path = sys.argv[1]

with open(settings_path) as f:
    settings = json.load(f)

new_hooks = $HOOKS_CONFIG

# Deep-merge hooks: for each hook type (PreToolUse, PostToolUse, etc.)
# append entries that aren't already present (matched by command string)
existing_hooks = settings.setdefault("hooks", {})

for hook_type, new_entries in new_hooks["hooks"].items():
    existing_entries = existing_hooks.setdefault(hook_type, [])
    # Collect existing commands to avoid duplicates
    existing_commands = set()
    for entry in existing_entries:
        for h in entry.get("hooks", []):
            existing_commands.add(h.get("command", ""))
    for new_entry in new_entries:
        for h in new_entry.get("hooks", []):
            if h.get("command", "") not in existing_commands:
                existing_entries.append(new_entry)
                existing_commands.add(h.get("command", ""))
                break

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

print(f"  [updated] {settings_path}")
PYEOF

echo "  Done. Hook scripts expected at ~/.claude/skills/hooks/"
echo "  Run: ./install.sh --global  to install hook scripts to that location."
