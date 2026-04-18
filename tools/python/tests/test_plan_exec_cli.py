"""Phase 2A smoke tests for `af plan-exec` CLI."""
from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from typer.main import get_command

from af.plan_exec_cli import app as plan_exec_app

runner = CliRunner()


def _write_plan(tmp_path: Path, body: str = "") -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text(
        body
        or """
version: 1
plan:
  slug: demo
  goal: demo plan
nodes:
  - id: a
    type: implement
    description: first
  - id: b
    type: implement
    depends_on: [a]
    description: second
"""
    )
    return p


def test_help_lists_all_subcommands():
    result = runner.invoke(get_command(plan_exec_app), ["--help"])
    assert result.exit_code == 0, result.output
    for cmd in ["validate", "list", "next", "mark", "reset", "status"]:
        assert cmd in result.output, f"missing {cmd} in help: {result.output}"


def test_validate_clean_plan(tmp_path):
    plan_path = _write_plan(tmp_path)
    result = runner.invoke(
        get_command(plan_exec_app),
        ["validate", str(plan_path), "--repo-root", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert "OK" in result.output


def test_validate_reports_errors(tmp_path):
    plan_path = _write_plan(
        tmp_path,
        """
version: 1
plan: {slug: bad}
nodes:
  - id: a
    type: implement
    depends_on: [ghost]
    description: dangling
""",
    )
    result = runner.invoke(
        get_command(plan_exec_app),
        ["validate", str(plan_path), "--repo-root", str(tmp_path)],
    )
    assert result.exit_code == 1, result.output
    assert "ghost" in result.output


def test_list_shows_nodes_and_status(tmp_path):
    plan_path = _write_plan(tmp_path)
    # Mark one done.
    runner.invoke(
        get_command(plan_exec_app), ["mark", str(plan_path), "a", "done"]
    )
    result = runner.invoke(get_command(plan_exec_app), ["list", str(plan_path)])
    assert result.exit_code == 0, result.output
    assert "a" in result.output and "b" in result.output
    # Line for `a` should show done glyph.
    a_line = next(line for line in result.output.splitlines() if " a  " in line)
    assert "✓" in a_line, f"expected done glyph for a, got: {a_line}"


def test_next_emits_json_for_ready_nodes(tmp_path):
    plan_path = _write_plan(tmp_path)
    # With no state, only `a` (no deps) is ready.
    result = runner.invoke(get_command(plan_exec_app), ["next", str(plan_path)])
    assert result.exit_code == 0, result.output
    lines = [line for line in result.output.strip().splitlines() if line.strip()]
    assert len(lines) == 1, f"expected 1 ready node, got: {lines}"
    rec = json.loads(lines[0])
    assert rec["id"] == "a"
    assert rec["type"] == "implement"

    # Mark `a` done → `b` becomes ready.
    runner.invoke(
        get_command(plan_exec_app), ["mark", str(plan_path), "a", "done"]
    )
    result = runner.invoke(get_command(plan_exec_app), ["next", str(plan_path)])
    assert result.exit_code == 0, result.output
    lines = [line for line in result.output.strip().splitlines() if line.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0])["id"] == "b"


def test_mark_unknown_node_fails(tmp_path):
    plan_path = _write_plan(tmp_path)
    result = runner.invoke(
        get_command(plan_exec_app),
        ["mark", str(plan_path), "nope", "done"],
    )
    assert result.exit_code != 0
    assert "nope" in result.output


def test_status_summary(tmp_path):
    plan_path = _write_plan(tmp_path)
    runner.invoke(
        get_command(plan_exec_app), ["mark", str(plan_path), "a", "done"]
    )
    result = runner.invoke(
        get_command(plan_exec_app), ["status", str(plan_path)]
    )
    assert result.exit_code == 0, result.output
    assert "1 pending" in result.output
    assert "1 done" in result.output
    assert "2 total" in result.output


def test_reset_with_yes_removes_state(tmp_path):
    plan_path = _write_plan(tmp_path)
    runner.invoke(
        get_command(plan_exec_app), ["mark", str(plan_path), "a", "done"]
    )
    state_path = plan_path.with_suffix(plan_path.suffix + ".state.json")
    assert state_path.exists()
    result = runner.invoke(
        get_command(plan_exec_app), ["reset", str(plan_path), "--yes"]
    )
    assert result.exit_code == 0, result.output
    assert not state_path.exists()
