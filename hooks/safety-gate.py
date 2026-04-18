#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PreToolUse safety gate — blocks dangerous Bash commands.

`rm -rf` uses a blacklist: allowed unless the target resolves to a catastrophic
path (`/`, top-level system dirs, `$HOME` exact, anywhere outside the user's
home or /tmp). Rationale — the original blanket block caused too much friction
on routine cleanup (bun installs, cloned projects, scratch dirs); the real
risk is a handful of catastrophic targets, not every `rm -rf` ever.

Other patterns (force push, DROP TABLE, fork bomb, dd, mkfs) remain hard-blocked.
"""

import json
import os
import re
import sys

# (pattern, uses_rm_blacklist)
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

# Absolute paths that are catastrophic to rm -rf. Exact match on the resolved
# absolute path, OR target is the filesystem root.
_CATASTROPHIC_EXACT = {
    "/",
    "/bin", "/boot", "/etc", "/home", "/lib", "/lib32", "/lib64",
    "/opt", "/proc", "/root", "/run", "/sbin", "/srv", "/sys",
    "/usr", "/var",
}


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


def _resolve_target(path: str, cwd: str) -> str:
    """Expand ~ and make absolute against cwd."""
    return os.path.abspath(os.path.join(cwd, os.path.expanduser(path)))


def _is_catastrophic(path: str, cwd: str) -> bool:
    """Return True if rm -rf on this path would be a disaster."""
    abs_path = _resolve_target(path, cwd)
    normalized = os.path.normpath(abs_path).rstrip("/") or "/"

    # Catastrophic exact-match paths: / and top-level system dirs
    if normalized in _CATASTROPHIC_EXACT:
        return True

    # $HOME exact, or ~ exact (already expanded by _resolve_target)
    home = os.path.expanduser("~").rstrip("/")
    if home and normalized == home:
        return True

    # A wildcard (*, ?, [) near the root is dangerous — e.g. rm -rf /*, rm -rf ~/*
    # Detect by checking if the ORIGINAL argument (pre-resolve) contained a glob
    # that would expand to catastrophic paths. We do a simple check: if the
    # argument contains any glob char and the parent dir is in the catastrophic
    # set (or is /, or is $HOME), block.
    if any(ch in path for ch in "*?[") :
        parent = os.path.dirname(normalized).rstrip("/") or "/"
        if parent in _CATASTROPHIC_EXACT or parent == home or parent == "/":
            return True

    # Outside $HOME and outside /tmp: suspicious. Block unless explicitly
    # under common scratch/project roots users do own.
    safe_prefixes = [home + "/", "/tmp/", "/var/tmp/"]
    if not any(normalized.startswith(p) for p in safe_prefixes) and normalized not in (home, "/tmp", "/var/tmp"):
        return True

    return False


def _rm_any_target_catastrophic(command: str, cwd: str) -> bool:
    """True when at least one rm target would be catastrophic — block the command."""
    targets = _extract_rm_targets(command)
    if not targets:
        # No extractable targets (parse fail) — be safe, block.
        return True
    return any(_is_catastrophic(t, cwd) for t in targets)


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

    for pattern, rm_blacklist in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            if rm_blacklist and not _rm_any_target_catastrophic(command, cwd):
                # No catastrophic target — let it through.
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
