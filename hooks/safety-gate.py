#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PreToolUse safety gate — blocks dangerous Bash commands.

`rm -rf` has an escape valve: allowed when every target path is inside the
current git working tree. Rationale — `git checkout` can always restore the
files, so it's not the same blast radius as `rm -rf` on arbitrary paths.
Other patterns (force push, DROP TABLE, fork bomb, dd, mkfs) remain hard-blocked.
"""

import json
import os
import re
import subprocess
import sys

# (pattern, allow_inside_git_worktree)
DANGEROUS_PATTERNS: list[tuple[str, bool]] = [
    (r"rm\s+-rf?\b", True),
    (r"git\s+push\s+--force", False),
    (r"git\s+push\s+-f\b", False),
    (r"DROP\s+TABLE", False),
    (r"DROP\s+DATABASE", False),
    (r":\(\)\{:\|:&\};:", False),   # fork bomb
    (r"dd\s+if=", False),
    (r"\bmkfs\b", False),
]


def _extract_rm_targets(command: str) -> list[str]:
    """Parse out `rm -rf <paths>` — naive but good enough for the check."""
    m = re.search(r"rm\s+-rf?\s+(.+)", command)
    if not m:
        return []
    tail = m.group(1)
    # Stop at shell separators so we only grab the rm's args
    tail = re.split(r"[;&|]|\s&&\s|\s\|\|\s", tail)[0]
    raw = tail.split()
    # Drop flag-only tokens (extra -f, -v, etc.)
    return [tok for tok in raw if not tok.startswith("-")]


def _inside_git_worktree(path: str, cwd: str) -> bool:
    """True when `path` (resolved against cwd) is tracked or inside a git dir."""
    abs_path = os.path.abspath(os.path.join(cwd, os.path.expanduser(path)))
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=os.path.dirname(abs_path) or cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    worktree = result.stdout.strip()
    if not worktree:
        return False
    try:
        rel = os.path.relpath(abs_path, worktree)
    except ValueError:
        return False
    return not rel.startswith("..") and not os.path.isabs(rel)


def _rm_all_targets_in_worktree(command: str, cwd: str) -> bool:
    targets = _extract_rm_targets(command)
    if not targets:
        return False
    return all(_inside_git_worktree(t, cwd) for t in targets)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = data.get("tool_name", "") or data.get("tool", "")
    command = (
        data.get("tool_input", {}).get("command")
        or data.get("input", {}).get("command")
        or data.get("command")
        or ""
    )
    cwd = (
        data.get("cwd")
        or data.get("tool_input", {}).get("cwd")
        or os.getcwd()
    )

    if tool_name != "Bash" or not command:
        sys.exit(0)

    for pattern, git_escape in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            if git_escape and _rm_all_targets_in_worktree(command, cwd):
                # All targets inside a git worktree — recoverable. Let it through.
                sys.exit(0)
            print(
                f"[safety-gate] BLOCKED: command matches dangerous pattern '{pattern}'",
                file=sys.stderr,
            )
            print(f"[safety-gate] Command: {command[:200]}", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
