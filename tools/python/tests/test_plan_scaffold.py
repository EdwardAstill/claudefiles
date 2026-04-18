"""Tests for `af plan-scaffold` — YAML skeleton emitter for prose plans."""
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from af import plan_exec
from af.main import app
from af.plan_scaffold import scaffold

runner = CliRunner()


def _fake_plan_md(path: Path, n_tasks: int = 3) -> None:
    """Write a plan markdown with `n_tasks` `### Task N:` headings."""
    lines = [
        "# Fake Plan",
        "",
        "**Goal:** smoke-test the scaffolder.",
        "",
    ]
    for i in range(1, n_tasks + 1):
        lines += [
            f"### Task {i}: Do step {i}",
            "",
            f"- [ ] **Step 1:** do thing {i}",
            "",
        ]
    path.write_text("\n".join(lines) + "\n")


def test_scaffold_emits_yaml_with_sequential_deps(tmp_path):
    md = tmp_path / "2026-04-18-demo.md"
    _fake_plan_md(md, n_tasks=3)

    yaml_path, tasks, _errors = scaffold(md)

    assert yaml_path == md.with_suffix(".yaml")
    assert yaml_path.exists()
    assert len(tasks) == 3

    # Parses via plan_exec.load and has 3 sequential implement nodes.
    plan = plan_exec.load(yaml_path)
    assert plan.version == 1
    assert plan.plan.slug == "demo"
    assert plan.plan.prose == md.name
    assert len(plan.nodes) == 3
    assert all(isinstance(n, plan_exec.ImplementNode) for n in plan.nodes)
    assert plan.nodes[0].depends_on == []
    assert plan.nodes[1].depends_on == [plan.nodes[0].id]
    assert plan.nodes[2].depends_on == [plan.nodes[1].id]

    # Header comment is preserved.
    assert yaml_path.read_text().startswith(
        "# Scaffolded from 2026-04-18-demo.md. Review and edit."
    )


def test_scaffold_force_overwrites_existing_yaml(tmp_path):
    md = tmp_path / "2026-04-18-demo.md"
    _fake_plan_md(md, n_tasks=2)

    yaml_path = md.with_suffix(".yaml")
    yaml_path.write_text("stale: true\n")

    # Without --force: refuses.
    try:
        scaffold(md)
    except FileExistsError:
        pass
    else:
        raise AssertionError("scaffold should refuse to overwrite without force")

    # With force: overwrites, parses, has 2 nodes.
    yaml_path2, tasks, _errors = scaffold(md, force=True)
    assert yaml_path2 == yaml_path
    assert "stale: true" not in yaml_path.read_text()
    assert len(tasks) == 2
    plan = plan_exec.load(yaml_path)
    assert len(plan.nodes) == 2


def test_scaffold_cli_missing_input_exits_with_error(tmp_path):
    missing = tmp_path / "does-not-exist.md"
    result = runner.invoke(app, ["plan-scaffold", str(missing)])
    assert result.exit_code == 2
    # Typer may route stderr through result.output depending on mix_stderr.
    combined = result.output + (result.stderr if result.stderr_bytes else "")
    assert "not found" in combined or "does not exist" in combined.lower()
