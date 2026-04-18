#!/usr/bin/env python3
"""Exercise hooks/safety-gate.py with hand-crafted JSON payloads.

Not a pytest suite — just a small script you can run directly to verify
blocking behavior after any hook change. Follows the pattern established in
the hooks/README.md "Testing a hook" section.

Run:
    python3 hooks/tests/test_safety_gate.py
"""

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent.parent / "safety-gate.py"


def run(cmd: str, cwd: str = "/") -> int:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": cmd},
        "cwd": cwd,
    })
    r = subprocess.run(
        [str(HOOK)],
        input=payload,
        text=True,
        capture_output=True,
    )
    return r.returncode


CASES = [
    # (description, command, cwd, expected_exit)
    ("non-git path rm -rf",          "rm -rf /tmp/delete-me",                            "/",                                         2),
    ("inside git worktree rm -rf",   "rm -rf /home/eastill/projects/agentfiles/some",    "/home/eastill/projects/agentfiles",         0),
    ("git push --force",             "git push --force",                                 "/",                                         2),
    ("benign ls",                    "ls -la",                                           "/",                                         0),
    ("DROP TABLE",                   "psql -c 'DROP TABLE users'",                       "/",                                         2),
    ("fork bomb",                    ":(){:|:&};:",                                      "/",                                         2),
    ("dd if=",                       "dd if=/dev/zero of=/tmp/out bs=1M count=100",      "/",                                         2),
]


def main() -> int:
    fails = 0
    for desc, cmd, cwd, expected in CASES:
        got = run(cmd, cwd)
        ok = "✓" if got == expected else "✗"
        if got != expected:
            fails += 1
        print(f"  {ok}  {desc:<35}  want={expected}  got={got}")
    print()
    print(f"SUMMARY: {len(CASES) - fails}/{len(CASES)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
