"""Parity tests for hooks/install-hooks.sh ↔ hooks/install-gemini-hooks.sh.

The two scripts target different hosts (~/.claude vs ~/.gemini) so their
paths and config envelopes legitimately differ, but the *set* of hook
scripts they register should stay in sync — that's the drift surface 5-3
in NEXT_STEPS.md calls out.

If you intentionally diverge (e.g. a gemini-only hook), add the exception
to _ALLOWED_DIVERGENCE below with a brief rationale.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[3]
CLAUDE_INSTALL = REPO / "hooks" / "install-hooks.sh"
GEMINI_INSTALL = REPO / "hooks" / "install-gemini-hooks.sh"


# Basenames (or stems) that are allowed to appear in only one install script.
# Document the reason inline.
_ALLOWED_DIVERGENCE: dict[str, str] = {
    "statusline.sh": (
        "Claude Code supports a statusLine setting; Gemini does not have an "
        "equivalent surface, so install-hooks.sh wires statusline.sh and "
        "install-gemini-hooks.sh does not."
    ),
    "session-start": (
        "Gemini only uses SessionStart; Claude Code wires session-start via "
        "hooks/hooks.json during plugin install and also needs PreToolUse + "
        "PostToolUse + UserPromptSubmit + Stop + Notification, so "
        "install-hooks.sh covers a broader event surface that doesn't "
        "name the script path directly."
    ),
}


def _extract_hook_basenames(script_text: str) -> set[str]:
    """Pull every .py / .sh / `session-start` reference out of a bash script
    and return just the basename.

    Matches paths like `~/.claude/skills/hooks/safety-gate.py` and lifts the
    final path component. Also accepts bare script names (no directory).
    """
    pattern = re.compile(
        r"""
        (?:/|~/|\./|\b)                # boundary or path prefix
        ([a-zA-Z0-9_\-]+               # basename
            (?:\.py|\.sh)?
            |session-start)            # or the special executable
        (?=                            # followed by
            \s|"|'|\)|;|<|>|$
        )
        """,
        re.VERBOSE,
    )

    allowlist = {"safety-gate.py", "modes.py", "notify.py", "skill-logger.py",
                 "session-start", "statusline.sh"}
    found: set[str] = set()
    for match in pattern.finditer(script_text):
        name = match.group(1)
        if name in allowlist:
            found.add(name)
    return found


@pytest.mark.skipif(
    not CLAUDE_INSTALL.exists() or not GEMINI_INSTALL.exists(),
    reason="install script(s) not present",
)
def test_install_scripts_reference_same_hooks():
    claude_hooks = _extract_hook_basenames(CLAUDE_INSTALL.read_text())
    gemini_hooks = _extract_hook_basenames(GEMINI_INSTALL.read_text())

    claude_only = claude_hooks - gemini_hooks - set(_ALLOWED_DIVERGENCE)
    gemini_only = gemini_hooks - claude_hooks - set(_ALLOWED_DIVERGENCE)

    msgs = []
    if claude_only:
        msgs.append(
            f"install-hooks.sh references hooks missing from install-gemini-hooks.sh: "
            f"{sorted(claude_only)}"
        )
    if gemini_only:
        msgs.append(
            f"install-gemini-hooks.sh references hooks missing from install-hooks.sh: "
            f"{sorted(gemini_only)}"
        )

    assert not msgs, "\n".join(msgs) + (
        "\n\nFix: either sync the scripts or add the basename to "
        "_ALLOWED_DIVERGENCE in tests/test_install_scripts_parity.py "
        "with a one-line rationale."
    )


@pytest.mark.skipif(
    not CLAUDE_INSTALL.exists() or not GEMINI_INSTALL.exists(),
    reason="install script(s) not present",
)
def test_install_scripts_same_line_count_order_of_magnitude():
    """Soft parity check — if one script grows by 50% or more vs the other,
    we've probably diverged without meaning to."""
    claude_lines = len(CLAUDE_INSTALL.read_text().splitlines())
    gemini_lines = len(GEMINI_INSTALL.read_text().splitlines())

    ratio = max(claude_lines, gemini_lines) / min(claude_lines, gemini_lines)
    assert ratio < 1.5, (
        f"install scripts line count ratio {ratio:.2f} > 1.5: "
        f"install-hooks.sh={claude_lines}, install-gemini-hooks.sh={gemini_lines}. "
        f"Likely drift — one script grew without the other keeping pace."
    )
