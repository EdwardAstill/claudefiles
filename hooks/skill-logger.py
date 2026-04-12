#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PostToolUse skill logger — records SKILL.md reads to ~/.claude/logs/claudefiles.jsonl."""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "logs" / "claudefiles.jsonl"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = data.get("tool_name", "") or data.get("tool", "")
    file_path = (
        data.get("tool_input", {}).get("file_path")
        or data.get("input", {}).get("file_path")
        or data.get("file_path")
        or ""
    )

    if tool_name != "Read":
        sys.exit(0)

    if not file_path.endswith("SKILL.md"):
        sys.exit(0)

    # Extract skill name from the directory containing SKILL.md
    skill_name = Path(file_path).parent.name

    session_id = (
        data.get("session_id")
        or data.get("session", {}).get("id")
        or os.environ.get("CLAUDE_SESSION_ID", "")
    )

    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skill": skill_name,
        "session": session_id,
    }

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
