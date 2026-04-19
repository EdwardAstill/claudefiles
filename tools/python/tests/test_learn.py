"""Tests for af.learn slug/title heuristics — guarding against path-fragment bleed."""
from __future__ import annotations

import json

from af.learn import _session_files, _slug, _title


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


def test_title_strips_path_fragments_from_bash_commands():
    """Defect N24/B4#2: raw path fragments must not leak into description/title."""
    entries = [
        _bash("cat /home/user/projects/foo/bar.txt"),
        _bash("grep -r pattern /tmp/logs"),
        _bash("pytest -q"),
        _edit("/tmp/notes/plan.md"),
    ]
    slug, title = _title(entries, list(range(len(entries))))
    for noise in ("/home/user/projects/foo/bar.txt", "/home", "/tmp/logs"):
        assert noise not in title, f"path fragment {noise!r} leaked into title {title!r}"
    # Title should also not contain bare path-noise tokens.
    title_tokens = title.lower().replace("/", " ").split()
    for noise in ("home", "user", "projects", "tmp"):
        assert noise not in title_tokens, f"path noise {noise!r} leaked into title {title!r}"


def test_slug_strips_redirect_tokens():
    """Defect N24/B4#3: shell redirection fragments must not become slug tokens."""
    entries = [
        _bash("myscript --fix-thing 2 > /dev/null"),
        _bash("other-cmd 2>/dev/null"),
        _bash("third &> /tmp/log"),
        _bash("fourth >/dev/null"),
        _bash("fifth >&2"),
    ]
    slug, _ = _title(entries, list(range(len(entries))))
    tokens = slug.split("-")
    # redirect fragments and the lonely stream number should never surface.
    for bad in ("2", "dev", "null", "1", "amp"):
        assert bad not in tokens, f"redirect artifact {bad!r} in slug {slug!r}"


def test_propose_excludes_active_session_file(tmp_path, monkeypatch):
    """Defect N24/B4#1: the file named session-$CLAUDE_SESSION_ID.jsonl must be skipped."""
    import af.learn as learn_mod

    sess_dir = tmp_path / "sessions"
    sess_dir.mkdir()
    active_id = "active1234"
    active = sess_dir / f"session-{active_id}.jsonl"
    active.write_text(json.dumps({"tool": "Bash", "input": {"command": "echo mid-write"}}) + "\n")
    stale = sess_dir / "session-stale0001.jsonl"
    stale.write_text(json.dumps({"tool": "Bash", "input": {"command": "echo stale"}}) + "\n")

    monkeypatch.setattr(learn_mod, "SESSION_LOG_DIR", sess_dir)
    monkeypatch.setenv("CLAUDE_SESSION_ID", active_id)

    files = _session_files()
    names = [p.name for p in files]
    assert active.name not in names, f"active session {active.name!r} was scanned: {names}"
    assert stale.name in names, f"stale session missing from scan: {names}"
