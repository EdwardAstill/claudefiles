#!/usr/bin/env python3
"""Exercise hooks/safety-gate.py with hand-crafted JSON payloads.

Run:
    python3 hooks/tests/test_safety_gate.py
"""

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent.parent / "safety-gate.py"
HOME = str(Path.home())


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
    # ── rm -rf: catastrophic (blocked) ──────────────────────────────────
    ("rm -rf /",                           "rm -rf /",                                         "/",   2),
    ("rm -rf /etc",                        "rm -rf /etc",                                      "/",   2),
    ("rm -rf /usr",                        "rm -rf /usr",                                      "/",   2),
    ("rm -rf $HOME exact",                 f"rm -rf {HOME}",                                   "/",   2),
    ("rm -rf ~ (expands to $HOME)",        "rm -rf ~",                                         "/",   2),
    ("rm -rf /home",                       "rm -rf /home",                                     "/",   2),
    ("rm -rf ~/* (glob at home root)",     "rm -rf ~/*",                                       HOME,  2),
    ("rm -rf /tmp/../etc (outside home)",  "rm -rf /etc/passwd",                               "/",   2),
    # ── rm -rf: non-catastrophic (allowed) ─────────────────────────────
    ("rm -rf ~/projects/storm",            f"rm -rf {HOME}/projects/storm",                    HOME,  0),
    ("rm -rf /tmp/scratch",                "rm -rf /tmp/scratch",                              "/",   0),
    ("rm -rf ~/.cache/foo",                f"rm -rf {HOME}/.cache/foo",                        HOME,  0),
    ("rm -rf node_modules (relative)",     "rm -rf node_modules",                              f"{HOME}/projects/foo", 0),
    # ── other dangerous patterns (always blocked) ──────────────────────
    ("git push --force",                   "git push --force",                                 "/",   2),
    ("DROP TABLE",                         "psql -c 'DROP TABLE users'",                       "/",   2),
    ("fork bomb",                          ":(){:|:&};:",                                      "/",   2),
    ("dd if=",                             "dd if=/dev/zero of=/tmp/out bs=1M count=100",      "/",   2),
    # ── benign (allowed) ───────────────────────────────────────────────
    ("benign ls",                          "ls -la",                                           "/",   0),
    ("cp without rm",                      "cp foo bar",                                       "/",   0),
]


def main() -> int:
    fails = 0
    for desc, cmd, cwd, expected in CASES:
        got = run(cmd, cwd)
        ok = "✓" if got == expected else "✗"
        if got != expected:
            fails += 1
        print(f"  {ok}  {desc:<40}  want={expected}  got={got}")
    print()
    print(f"SUMMARY: {len(CASES) - fails}/{len(CASES)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
