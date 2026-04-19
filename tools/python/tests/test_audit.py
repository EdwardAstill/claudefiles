"""Tests for the `af audit` check 9 (hook script health)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
from typer.testing import CliRunner

from af.audit import app as audit_app
from af.audit import (
    _audit_hooks,
    _audit_plan_pairs,
    _dep_package_name,
    _parse_shebang,
    _parse_uv_script_deps,
)

runner = CliRunner()


# ── Unit tests on the parsers ────────────────────────────────────────────────


def test_parse_uv_script_deps_empty():
    src = (
        "#!/usr/bin/env -S uv run --script\n"
        "# /// script\n"
        "# requires-python = \">=3.11\"\n"
        "# dependencies = []\n"
        "# ///\n"
        "print('hi')\n"
    )
    has_block, deps, err = _parse_uv_script_deps(src)
    assert has_block is True
    assert deps == []
    assert err is None


def test_parse_uv_script_deps_multiple():
    src = (
        "# /// script\n"
        "# requires-python = \">=3.11\"\n"
        '# dependencies = ["requests>=2.0", "rich"]\n'
        "# ///\n"
    )
    has_block, deps, _ = _parse_uv_script_deps(src)
    assert has_block is True
    assert deps == ["requests>=2.0", "rich"]


def test_parse_uv_script_deps_absent():
    has_block, deps, _ = _parse_uv_script_deps("print('no block')\n")
    assert has_block is False
    assert deps == []


def test_parse_shebang():
    assert _parse_shebang("#!/usr/bin/env bash\n") == "/usr/bin/env"
    assert _parse_shebang("no shebang\n") is None


def test_dep_package_name():
    assert _dep_package_name("requests>=2.0") == "requests"
    assert _dep_package_name("rich[jupyter]~=13") == "rich"
    assert _dep_package_name("foo") == "foo"


# ── Integration: synthesize a tiny agentfiles repo with a hooks/ dir ─────────


def _make_fake_repo(root: Path) -> Path:
    (root / "manifest.toml").write_text("")
    (root / "agentfiles").mkdir()
    (root / "hooks").mkdir()
    return root


def test_valid_hook_passes(tmp_path, monkeypatch):
    repo = _make_fake_repo(tmp_path)
    hook = repo / "hooks" / "valid.py"
    hook.write_text(
        "#!/usr/bin/env -S uv run --script\n"
        "# /// script\n"
        "# requires-python = \">=3.11\"\n"
        "# dependencies = []\n"
        "# ///\n"
        "print('ok')\n"
    )
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
    issues = _audit_hooks(repo)
    assert issues == [], f"expected clean hook, got: {issues}"


def test_hook_with_bogus_dep_is_flagged(tmp_path):
    repo = _make_fake_repo(tmp_path)
    hook = repo / "hooks" / "broken.py"
    # Use a name we're confident does not exist on PyPI to force uv to fail
    # resolution. The dep check shells out to `uv pip install --dry-run`.
    bogus = "this-package-definitely-does-not-exist-af-audit-test-xyz"
    hook.write_text(
        "#!/usr/bin/env -S uv run --script\n"
        "# /// script\n"
        "# requires-python = \">=3.11\"\n"
        f'# dependencies = ["{bogus}"]\n'
        "# ///\n"
        "print('nope')\n"
    )
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)

    import shutil as _sh
    if _sh.which("uv") is None:
        pytest.skip("uv not on PATH — dep resolution check cannot run")

    issues = _audit_hooks(repo)
    joined = "\n".join(issues)
    assert bogus in joined, f"expected bogus dep to be flagged, got: {issues}"
    assert "broken.py" in joined


def test_hooks_json_missing_command_flagged(tmp_path):
    repo = _make_fake_repo(tmp_path)
    (repo / "hooks" / "hooks.json").write_text(
        '{"hooks": {"SessionStart": [{"hooks": [{"type": "command", '
        '"command": "${CLAUDE_PLUGIN_ROOT}/hooks/does-not-exist"}]}]}}'
    )
    issues = _audit_hooks(repo)
    joined = "\n".join(issues)
    assert "does-not-exist" in joined


# ── Check 10: plan pair drift ────────────────────────────────────────────────


_CLEAN_YAML = """\
version: 1
id: sample-plan
nodes:
  - id: t1
    type: implement
    prose_ref: task-1-do-the-thing
    spec: do the thing
"""

_CLEAN_MD = """\
# Sample Plan

### Task 1: Do the thing

Write some code.
"""


def _plans_repo(root: Path) -> Path:
    """Build a minimal agentfiles repo with a docs/plans/ dir."""
    (root / "manifest.toml").write_text("")
    (root / "agentfiles").mkdir()
    (root / "docs" / "plans").mkdir(parents=True)
    return root


def test_plan_pairs_clean_returns_no_issues(tmp_path):
    repo = _plans_repo(tmp_path)
    (repo / "docs" / "plans" / "sample.yaml").write_text(_CLEAN_YAML)
    (repo / "docs" / "plans" / "sample.md").write_text(_CLEAN_MD)

    issues, count = _audit_plan_pairs(repo)
    assert issues == []
    assert count == 1


def test_plan_pairs_drift_flagged(tmp_path):
    repo = _plans_repo(tmp_path)
    # prose_ref points at an anchor that does not exist in the .md
    drifted_yaml = _CLEAN_YAML.replace(
        "task-1-do-the-thing", "task-1-does-not-exist-in-prose"
    )
    (repo / "docs" / "plans" / "sample.yaml").write_text(drifted_yaml)
    (repo / "docs" / "plans" / "sample.md").write_text(_CLEAN_MD)

    issues, count = _audit_plan_pairs(repo)
    assert count == 1
    joined = "\n".join(issues)
    assert "sample.yaml" in joined
    assert "task-1-does-not-exist-in-prose" in joined


def test_plan_pairs_no_plans_dir(tmp_path):
    # No docs/plans/ at all — check should be a no-op, not an error.
    (tmp_path / "manifest.toml").write_text("")
    (tmp_path / "agentfiles").mkdir()
    issues, count = _audit_plan_pairs(tmp_path)
    assert issues == []
    assert count == 0


def test_audit_cli_reports_check_10(tmp_path, monkeypatch):
    """End-to-end: `af audit` invocation includes CHECK 10 in its summary."""
    repo = _plans_repo(tmp_path)
    (repo / "docs" / "plans" / "sample.yaml").write_text(_CLEAN_YAML)
    (repo / "docs" / "plans" / "sample.md").write_text(_CLEAN_MD)
    # Minimal skills/ so registry check doesn't choke.
    (repo / "skills").mkdir()

    monkeypatch.chdir(repo)
    result = runner.invoke(audit_app, [])
    assert "CHECK 10" in result.stdout
    assert "10/10" in result.stdout or "10 checks" in result.stdout


def test_audit_cli_fails_on_plan_drift(tmp_path, monkeypatch):
    """Deliberate drift causes `af audit` to exit non-zero."""
    repo = _plans_repo(tmp_path)
    drifted_yaml = _CLEAN_YAML.replace(
        "task-1-do-the-thing", "bogus-anchor-not-in-prose"
    )
    (repo / "docs" / "plans" / "sample.yaml").write_text(drifted_yaml)
    (repo / "docs" / "plans" / "sample.md").write_text(_CLEAN_MD)
    (repo / "skills").mkdir()

    monkeypatch.chdir(repo)
    result = runner.invoke(audit_app, [])
    assert result.exit_code == 1
    assert "bogus-anchor-not-in-prose" in result.stdout
