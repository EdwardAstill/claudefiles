"""Tests for `af check plans` — YAML <-> prose drift watchdog."""
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from af.main import app

runner = CliRunner()


CLEAN_MD = """# Demo Plan

## Task 1: Lay the foundation

Foundation prose.

### Task 1: Foundation

- [ ] **Step 1:** do the thing.

### Task 2: Wire it up

- [ ] **Step 1:** connect the pieces.
"""


CLEAN_YAML = """version: 1
plan:
  slug: demo
  prose: demo.md
  goal: Demo plan for drift tests.

nodes:
  - id: foundation
    type: implement
    description: Lay the foundation.
    prose_ref: task-1-foundation

  - id: wire_it_up
    type: implement
    depends_on: [foundation]
    description: Wire it up.
    prose_ref: task-2-wire-it-up
"""


def _write_pair(tmp_path: Path, md: str, yml: str) -> tuple[Path, Path]:
    plans_dir = tmp_path / "docs" / "plans"
    plans_dir.mkdir(parents=True)
    md_path = plans_dir / "demo.md"
    yaml_path = plans_dir / "demo.yaml"
    md_path.write_text(md)
    yaml_path.write_text(yml)
    return yaml_path, md_path


def test_clean_plan_pair_passes(tmp_path, monkeypatch):
    _write_pair(tmp_path, CLEAN_MD, CLEAN_YAML)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check", "plans"])
    assert result.exit_code == 0, result.output
    assert "clean" in result.output.lower()


def test_missing_prose_ref_is_flagged(tmp_path, monkeypatch):
    bad_yaml = CLEAN_YAML.replace(
        "prose_ref: task-2-wire-it-up",
        "prose_ref: task-2-does-not-exist",
    )
    _write_pair(tmp_path, CLEAN_MD, bad_yaml)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check", "plans"])
    assert result.exit_code == 1, result.output
    assert "task-2-does-not-exist" in result.output
    assert "wire_it_up" in result.output


def test_extra_markdown_task_is_flagged(tmp_path, monkeypatch):
    # Prose has 3 Task headings, YAML has only 2 implement nodes.
    extra_md = CLEAN_MD + "\n### Task 3: Extra work\n\n- [ ] **Step 1:** do it.\n"
    _write_pair(tmp_path, extra_md, CLEAN_YAML)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check", "plans"])
    assert result.exit_code == 1, result.output
    assert "3" in result.output
    assert "implement node" in result.output


def test_no_pairs_reports_clean(tmp_path, monkeypatch):
    # Only a markdown plan, no YAML sidecar: should be a no-op clean pass.
    plans_dir = tmp_path / "docs" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "lonely.md").write_text("# Lonely prose plan\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check", "plans"])
    assert result.exit_code == 0, result.output
    assert "no yaml+md plan pairs" in result.output.lower()
