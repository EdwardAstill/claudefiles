#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PreToolUse safety gate — blocks dangerous Bash commands."""

import json
import sys
import re

DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"git\s+push\s+--force",
    r"git\s+push\s+-f",
    r"DROP\s+TABLE",
    r"DROP\s+DATABASE",
    r":\(\)\{:\|:&\};:",   # fork bomb
    r"dd\s+if=",
    r"mkfs",
]

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = data.get("tool_name", "") or data.get("tool", "")
    # Handle both flat and nested input shapes
    command = (
        data.get("tool_input", {}).get("command")
        or data.get("input", {}).get("command")
        or data.get("command")
        or ""
    )

    if tool_name != "Bash":
        sys.exit(0)

    if not command:
        sys.exit(0)

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            print(
                f"[safety-gate] BLOCKED: command matches dangerous pattern '{pattern}'",
                file=sys.stderr,
            )
            print(f"[safety-gate] Command: {command[:200]}", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
