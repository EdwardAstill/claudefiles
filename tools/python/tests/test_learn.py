"""Tests for af.learn slug/title heuristics — guarding against path-fragment bleed."""
from __future__ import annotations

from af.learn import _slug, _title


def _edit(path: str) -> dict:
    return {"tool": "Edit", "input": {"file_path": path}}


def _bash(cmd: str) -> dict:
    return {"tool": "Bash", "input": {"command": cmd}}


def test_slug_strips_path_noise_tokens():
    # A hand-crafted title mimicking the old bad output should lose all
    # path-fragment noise words (home, projects, agentfiles, ...).
    slug = _slug("skill home eastill projects agentfiles skills audit-drift")
    for noise in ("home", "eastill", "projects", "agentfiles", "skills"):
        assert noise not in slug.split("-"), f"{noise!r} leaked into slug {slug!r}"
    assert "audit" in slug.split("-")
    assert len(slug) <= 32


def test_title_from_edits_uses_basenames_not_paths():
    entries = [
        _edit("/home/eastill/projects/agentfiles/skills/audit-drift/SKILL.md"),
        _edit("/home/eastill/projects/agentfiles/skills/audit-drift/README.md"),
        _edit("/home/eastill/projects/agentfiles/skills/audit-drift/fixer.py"),
        _bash("af audit --fix"),
        _bash("pytest -q"),
    ]
    idx = list(range(len(entries)))
    slug, title = _title(entries, idx)
    for noise in ("home", "eastill", "projects", "agentfiles", "skills"):
        assert noise not in slug.split("-"), f"{noise!r} leaked into slug {slug!r}"
    # Dominant parent 'audit-drift' must win (3 same-dir edits), appearing as a token.
    assert "audit" in slug and "drift" in slug
    assert len(slug) <= 32


def test_title_skips_flags_in_bash():
    entries = [
        _bash("rm -rf /tmp/foo"),
        _bash("cp --force a.txt b.txt"),
        _edit("/tmp/notes/plan.md"),
    ]
    slug, _ = _title(entries, list(range(len(entries))))
    # flag tokens should never appear as slug tokens.
    assert "r" not in slug.split("-")
    assert "rf" not in slug.split("-")
    assert "force" not in slug.split("-")
    assert len(slug) <= 32


def test_slug_fallback_when_empty():
    assert _slug("") == "session-run"
