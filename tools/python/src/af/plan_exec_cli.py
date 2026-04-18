"""`af plan-exec` CLI — validator + state tracker + next-node picker.

Phase 2A of the plan YAML work. This command does NOT dispatch subagents;
that is the `subagent-driven-development` skill's job (Phase 2C). The CLI
is a thin wrapper over `af.plan_exec` for humans and skills to drive a
plan through its lifecycle.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

import typer

from af.plan_exec import (
    Plan,
    PlanParseError,
    StateFile,
    VALID_STATES,
    load,
    toposort,
    validate,
)

app = typer.Typer(help="Validate, inspect, and track state of a plan YAML.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_repo_root(plan_path: Path, explicit: Optional[Path]) -> Path:
    """Pick a repo root: explicit → nearest ancestor with .git → cwd."""
    if explicit is not None:
        return Path(explicit).resolve()
    start = plan_path.resolve().parent
    cur = start
    while True:
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return Path.cwd()


def _state_path_for(plan_path: Path) -> Path:
    return plan_path.with_suffix(plan_path.suffix + ".state.json")


def _load_or_die(plan_path: Path) -> Plan:
    try:
        return load(plan_path)
    except PlanParseError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(code=1)


def _status_glyph(status: str) -> str:
    return {
        "done": "[✓]",
        "running": "[.]",
        "failed": "[✗]",
        "pending": "[ ]",
    }.get(status, "[ ]")


def _all_node_ids(plan: Plan) -> set[str]:
    """Top-level + loop body ids — what `mark` is allowed to reference."""
    out: set[str] = set()
    for n in plan.nodes:
        out.add(n.id)
        body = getattr(n, "body", None)
        if body:
            for inner in body:
                out.add(inner.id)
    return out


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("validate")
def validate_cmd(
    plan_yaml: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
    repo_root: Optional[Path] = typer.Option(
        None,
        "--repo-root",
        help="Base path for files.create / files.modify checks. "
        "Defaults to nearest parent with .git, else cwd.",
    ),
) -> None:
    """Load + validate a plan. Exit 0 clean, exit 1 with issues."""
    plan = _load_or_die(plan_yaml)
    root = _resolve_repo_root(plan_yaml, repo_root)
    errors = validate(plan, repo_root=root)
    if errors:
        typer.echo(f"{plan_yaml}: {len(errors)} validation issue(s):")
        for e in errors:
            typer.echo(f"  - {e}")
        raise typer.Exit(code=1)
    typer.echo(f"{plan_yaml}: OK ({len(plan.nodes)} nodes)")


@app.command("list")
def list_cmd(
    plan_yaml: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
) -> None:
    """Print toposorted nodes with current status."""
    plan = _load_or_die(plan_yaml)
    try:
        order = toposort(plan)
    except ValueError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(code=1)
    sf = StateFile.load(_state_path_for(plan_yaml))
    for n in order:
        status = sf.states.get(n.id, "pending")
        glyph = _status_glyph(status)
        typer.echo(f"{glyph} {n.id}  {n.type}  {n.description}")


@app.command("next")
def next_cmd(
    plan_yaml: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
) -> None:
    """Print JSON-line records for nodes ready to run (deps done, self pending)."""
    plan = _load_or_die(plan_yaml)
    sf = StateFile.load(_state_path_for(plan_yaml))
    try:
        ready = sf.ready_nodes(plan)
    except ValueError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(code=1)
    for n in ready:
        typer.echo(
            json.dumps(
                {"id": n.id, "type": n.type, "description": n.description},
                ensure_ascii=False,
            )
        )


@app.command("mark")
def mark_cmd(
    plan_yaml: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
    node_id: str = typer.Argument(..., help="Node id to mark."),
    status: str = typer.Argument(
        ..., help="One of: pending, running, done, failed."
    ),
) -> None:
    """Mutate state file for a single node."""
    if status not in VALID_STATES:
        typer.echo(
            f"error: invalid status '{status}'; expected one of "
            f"{sorted(VALID_STATES)}",
            err=True,
        )
        raise typer.Exit(code=2)
    plan = _load_or_die(plan_yaml)
    known = _all_node_ids(plan)
    if node_id not in known:
        typer.echo(
            f"error: node '{node_id}' not found in plan {plan_yaml}",
            err=True,
        )
        raise typer.Exit(code=2)
    state_path = _state_path_for(plan_yaml)
    sf = StateFile.load(state_path)
    sf.path = state_path  # ensure save target is set even for fresh files
    sf.mark(node_id, status)
    typer.echo(f"{node_id}: {status}")


@app.command("reset")
def reset_cmd(
    plan_yaml: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt."
    ),
) -> None:
    """Wipe the state file for a plan."""
    state_path = _state_path_for(plan_yaml)
    if not yes:
        confirmed = typer.confirm(
            f"Delete state file {state_path}?",
            default=False,
        )
        if not confirmed:
            typer.echo("aborted")
            raise typer.Exit(code=1)
    existed = state_path.exists()
    StateFile.reset(state_path)
    typer.echo(f"{'removed' if existed else 'no state file'}: {state_path}")


@app.command("status")
def status_cmd(
    plan_yaml: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
) -> None:
    """Summary of node states for a plan."""
    plan = _load_or_die(plan_yaml)
    sf = StateFile.load(_state_path_for(plan_yaml))
    total = len(plan.nodes)
    # `pending` = in-plan top-level nodes that are not recorded as anything else.
    recorded = sf.status_summary()
    non_pending_in_plan = sum(
        1
        for n in plan.nodes
        if sf.states.get(n.id, "pending") != "pending"
    )
    pending_count = total - non_pending_in_plan
    running = recorded["running"]
    done = recorded["done"]
    failed = recorded["failed"]
    typer.echo(
        f"{pending_count} pending / {running} running / "
        f"{done} done / {failed} failed / {total} total"
    )
