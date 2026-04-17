#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""UserPromptSubmit hook — re-injects caveman mode each turn if enabled.

Controlled by ~/.claude/caveman-mode (file exists = enabled; contents = level).

Levels: lite, full, actual-caveman. Default: full.
Disable: delete the file (or `af caveman off`).
"""

import json
import sys
from pathlib import Path

STATE = Path.home() / ".claude" / "caveman-mode"

REMINDERS = {
    "lite": (
        "caveman-lite: drop filler (just/really/basically), pleasantries "
        "(sure/of course), hedging. Keep articles and full grammar."
    ),
    "full": (
        "caveman-full: drop filler, pleasantries, hedging, AND articles. "
        "Fragments OK. Short synonyms. Technical terms exact. "
        "Code blocks unchanged. One sentence per thought. "
        "Auto-clarity: drop to normal prose for security/destructive warnings "
        "and multi-step instructions; resume after."
    ),
    "actual-caveman": (
        "actual-caveman: grunt style, cave analogies, broken grammar on purpose. "
        "Keep code blocks and errors unchanged. Drop to normal prose for "
        "security/destructive warnings."
    ),
}

# Accepted aliases → canonical key
ALIASES = {
    "lite": "lite",
    "full": "full",
    "actual": "actual-caveman",
    "actual-caveman": "actual-caveman",
    "cave": "actual-caveman",
}


def main() -> None:
    if not STATE.exists():
        sys.exit(0)

    try:
        raw = STATE.read_text().strip().lower() or "full"
    except OSError:
        sys.exit(0)

    level = ALIASES.get(raw, "full")
    msg = f"Reminder: {REMINDERS[level]}"

    payload = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": msg,
        }
    }
    print(json.dumps(payload))
    sys.exit(0)


if __name__ == "__main__":
    main()
