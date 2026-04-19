"""Tests for `af check modes` — MODE.md frontmatter validator."""
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from af.check import check_mode_file
from af.main import app

runner = CliRunner()


SINGLE_LEVEL_MODE = """---
name: {name}
description: >
  A test mode.
category: test
levels: [on]
reminder: >
  do the test thing
---

# {name}
"""


MULTI_LEVEL_MODE = """---
name: {name}
description: >
  A multi-level test mode.
category: test
levels: [lite, full]
reminder: >
  default reminder text
reminders:
  lite: >
    lite reminder text
  full: >
    full reminder text
---

# {name}
"""


def _write_mode(modes_dir: Path, name: str, body: str) -> Path:
    mode_dir = modes_dir / name
    mode_dir.mkdir(parents=True)
    mode_md = mode_dir / "MODE.md"
    mode_md.write_text(body)
    return mode_md


# ── Unit tests on check_mode_file ────────────────────────────────────────────


def test_single_level_mode_clean(tmp_path):
    mode_md = _write_mode(
        tmp_path, "alpha", SINGLE_LEVEL_MODE.format(name="alpha")
    )
    assert check_mode_file(mode_md) == []


def test_multi_level_mode_clean(tmp_path):
    mode_md = _write_mode(tmp_path, "beta", MULTI_LEVEL_MODE.format(name="beta"))
    assert check_mode_file(mode_md) == []


def test_name_mismatch_flagged(tmp_path):
    mode_md = _write_mode(
        tmp_path, "alpha", SINGLE_LEVEL_MODE.format(name="wrong-name")
    )
    issues = check_mode_file(mode_md)
    assert any("does not match directory" in i for i in issues)


def test_missing_required_field_flagged(tmp_path):
    body = SINGLE_LEVEL_MODE.format(name="gamma").replace(
        "category: test\n", ""
    )
    mode_md = _write_mode(tmp_path, "gamma", body)
    issues = check_mode_file(mode_md)
    assert any("missing required field 'category'" in i for i in issues)


def test_multi_level_requires_reminders(tmp_path):
    """A mode with more than 1 level must have a `reminders` mapping."""
    body = MULTI_LEVEL_MODE.format(name="delta").replace(
        "reminders:\n  lite: >\n    lite reminder text\n  full: >\n    full reminder text\n",
        "",
    )
    mode_md = _write_mode(tmp_path, "delta", body)
    issues = check_mode_file(mode_md)
    assert any("needs a 'reminders' mapping" in i for i in issues)


def test_multi_level_reminders_must_cover_all_levels(tmp_path):
    body = MULTI_LEVEL_MODE.format(name="epsilon").replace(
        "  full: >\n    full reminder text\n", ""
    )
    mode_md = _write_mode(tmp_path, "epsilon", body)
    issues = check_mode_file(mode_md)
    assert any("reminders missing entry for level 'full'" in i for i in issues)


def test_yaml_boolean_levels_normalized(tmp_path):
    """YAML 1.1 parses `on` as True. The validator should accept it as 'on'."""
    # `on` is bareword; YAML safe_load coerces to True.
    body = SINGLE_LEVEL_MODE.format(name="zeta")
    mode_md = _write_mode(tmp_path, "zeta", body)
    # If the coercion were flagged, there'd be an 'empty or non-string' issue.
    issues = check_mode_file(mode_md)
    assert not any("non-string or empty" in i for i in issues)


def test_no_frontmatter_flagged(tmp_path):
    mode_md = _write_mode(tmp_path, "eta", "just a body, no frontmatter\n")
    issues = check_mode_file(mode_md)
    assert issues and "no YAML frontmatter" in issues[0]


# ── CLI end-to-end ───────────────────────────────────────────────────────────


def test_cli_clean_exits_zero(tmp_path, monkeypatch):
    modes_dir = tmp_path / "agentfiles" / "modes"
    _write_mode(modes_dir, "alpha", SINGLE_LEVEL_MODE.format(name="alpha"))
    _write_mode(modes_dir, "beta", MULTI_LEVEL_MODE.format(name="beta"))

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check", "modes"])
    assert result.exit_code == 0
    assert "2 mode(s) clean" in result.stdout


def test_cli_reports_drift_nonzero(tmp_path, monkeypatch):
    modes_dir = tmp_path / "agentfiles" / "modes"
    _write_mode(
        modes_dir, "broken", SINGLE_LEVEL_MODE.format(name="renamed-but-not-dir")
    )

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check", "modes"])
    assert result.exit_code == 1
    assert "does not match directory" in result.stdout


def test_cli_no_modes_dir_is_quiet(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check", "modes"])
    assert result.exit_code == 0
    assert "not found" in result.stdout
