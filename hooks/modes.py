#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""UserPromptSubmit hook — re-injects active behavioral modes each turn.

Scans `~/.claude/modes/` for active mode state files. Each filename is a
mode name, contents are the active level. For each active mode, locates
the matching `agentfiles/modes/<name>/MODE.md`, reads its `reminder:` (or
per-level `reminders:` entry), and concatenates them in category priority
order into a single `additionalContext` payload.

Zero external deps on purpose — this runs on every user prompt and has to
be fast. YAML-ish frontmatter parsing is inline; it handles only the
subset we commit to in `agentfiles/modes/README.md`.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Make the sibling `hooks/hook_types.py` importable. `uv run --script`
# doesn't add the script's directory to sys.path automatically, so we do
# it here. Named `hook_types` (not `types`) so it doesn't shadow the
# stdlib `types` module during import.
sys.path.insert(0, str(Path(__file__).parent))
import hook_types  # noqa: E402  (import after sys.path tweak)


# ── Paths ─────────────────────────────────────────────────────────────────────

def _state_dir() -> Path:
    override = os.environ.get("AF_MODES_STATE_DIR")
    if override:
        return Path(override)
    return Path.home() / ".claude" / "modes"


def _modes_root() -> Path | None:
    """Locate the `agentfiles/modes/` directory.

    Order:
      1. $AF_MODES_DIR override.
      2. $CLAUDE_PLUGIN_ROOT (set by Claude Code when invoking the hook).
      3. Walk up from this file.
    """
    override = os.environ.get("AF_MODES_DIR")
    if override:
        return Path(override)
    plugin = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin:
        candidate = Path(plugin) / "agentfiles" / "modes"
        if candidate.is_dir():
            return candidate
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / "agentfiles" / "modes").is_dir():
            return p / "agentfiles" / "modes"
    return None


# ── Frontmatter + minimal YAML-ish parser (inline; keep deps zero) ───────────

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def _split_frontmatter(text: str) -> str:
    m = _FRONTMATTER_RE.match(text)
    return m.group(1) if m else ""


def _parse_scalar(v: str) -> str:
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    if v.startswith("'") and v.endswith("'"):
        return v[1:-1]
    return v


def _parse_frontmatter(fm: str) -> dict:
    out: dict = {}
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_\-]*\s*:", line):
            i += 1
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.rstrip()
        if rest.strip() in (">", ">-", "|", "|-"):
            i += 1
            collected: list[str] = []
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                collected.append(lines[i].strip())
                i += 1
            out[key] = " ".join(x for x in collected if x).strip()
            continue
        if rest.strip():
            value = rest.strip()
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1]
                out[key] = [
                    _parse_scalar(x) for x in inner.split(",") if x.strip()
                ] if inner.strip() else []
            elif value.lower() in ("true", "false"):
                out[key] = value.lower() == "true"
            else:
                out[key] = _parse_scalar(value)
            i += 1
            continue
        # Block value
        i += 1
        block_lines: list[str] = []
        while i < len(lines):
            ln = lines[i]
            if not ln.strip():
                block_lines.append(ln)
                i += 1
                continue
            if not ln.startswith((" ", "\t")):
                break
            block_lines.append(ln)
            i += 1
        stripped_block = [b for b in block_lines if b.strip()]
        if stripped_block and stripped_block[0].lstrip().startswith("- "):
            items = []
            for b in stripped_block:
                s = b.lstrip()
                if s.startswith("- "):
                    items.append(_parse_scalar(s[2:]))
            out[key] = items
        else:
            mapping: dict[str, str] = {}
            idx = 0
            while idx < len(block_lines):
                b = block_lines[idx]
                s = b.strip()
                if not s or ":" not in s:
                    idx += 1
                    continue
                k, _, v = s.partition(":")
                v = v.strip()
                if v in (">", ">-", "|", "|-"):
                    folded: list[str] = []
                    base_indent = len(b) - len(b.lstrip())
                    j = idx + 1
                    while j < len(block_lines):
                        ln2 = block_lines[j]
                        if not ln2.strip():
                            j += 1
                            continue
                        ln_indent = len(ln2) - len(ln2.lstrip())
                        if ln_indent <= base_indent:
                            break
                        folded.append(ln2.strip())
                        j += 1
                    mapping[k.strip()] = " ".join(folded).strip()
                    idx = j
                    continue
                mapping[k.strip()] = _parse_scalar(v)
                idx += 1
            out[key] = mapping
    return out


_CATEGORY_PRIORITY = {
    "rigor": 0,
    "research": 1,
    "communication": 2,
    "planning": 3,
    "novelty": 4,
}


def _category_rank(cat: str) -> int:
    return _CATEGORY_PRIORITY.get(cat, 5)


# ── Reminder assembly ────────────────────────────────────────────────────────

def _reminder_for(spec: dict, level: str) -> str:
    reminders = spec.get("reminders") if isinstance(spec.get("reminders"), dict) else {}
    per = reminders.get(level) if reminders else None
    if per:
        return str(per).strip()
    return str(spec.get("reminder") or "").strip()


def _collect_reminders() -> list[str]:
    state = _state_dir()
    if not state.exists():
        return []
    active: dict[str, str] = {}
    for f in state.iterdir():
        if not f.is_file() or f.name.startswith("."):
            continue
        try:
            level = f.read_text().strip() or "on"
        except OSError:
            continue
        active[f.name] = level
    if not active:
        return []
    root = _modes_root()
    if root is None:
        return []
    entries: list[tuple[int, str, str]] = []
    for name, level in active.items():
        md = root / name / "MODE.md"
        if not md.exists():
            continue
        try:
            fm = _split_frontmatter(md.read_text())
            spec = _parse_frontmatter(fm)
        except Exception:
            continue
        reminder = _reminder_for(spec, level)
        if not reminder:
            continue
        category = str(spec.get("category") or "communication")
        entries.append((_category_rank(category), name, reminder))
    entries.sort(key=lambda e: (e[0], e[1]))
    return [f"Reminder: {r}" for _, _, r in entries]


def main() -> None:
    # Drain stdin through the typed parser. modes.py doesn't consume any
    # payload fields today (its state lives in ~/.claude/modes/), but we
    # still parse for consistency with the other hooks. Unlike safety-gate,
    # an empty/malformed payload is NOT a reason to bail — the reminder
    # logic reads from the filesystem, not the payload. We read stdin only
    # to drain the pipe cleanly and surface typed access if a future change
    # wants to gate on `payload["prompt"]`.
    payload: hook_types.UserPromptSubmitPayload = hook_types.parse(  # noqa: F841
        "UserPromptSubmit", sys.stdin.read()
    )

    reminders = _collect_reminders()
    if not reminders:
        sys.exit(0)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n".join(reminders),
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
