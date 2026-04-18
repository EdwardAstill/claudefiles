"""af plan-scaffold — emit a YAML skeleton from an existing prose plan.

Migration helper for in-flight markdown plans written before the YAML
sidecar schema existed (see docs/plans/2026-04-18-plan-yaml-schema.md §6).

Scope: grep `### Task N:` headings, emit one `implement` node per task
with a sequential `depends_on` chain, and run the sidecar through
`plan_exec.load` + `plan_exec.validate` as a sanity check. The author
still fills in `verify:` commands, real `depends_on` edges, and human
gate / loop nodes — this is a skeleton, not a translation.
"""

from __future__ import annotations

import re
from pathlib import Path

import typer

from af import plan_exec

app = typer.Typer(help="Scaffold a YAML sidecar from a prose plan markdown.")


_TASK_HEADING_RE = re.compile(r"^###\s+Task\s+(\d+)\s*:\s*(.+?)\s*$")


def _slugify_task_name(name: str) -> str:
    """Convert a task heading title into a snake_case node id fragment."""
    # Strip backticks and other markdown punctuation that would make ugly ids.
    cleaned = re.sub(r"[`*_\[\]()]", "", name)
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", cleaned)
    cleaned = cleaned.strip("_").lower()
    return cleaned or "task"


def _parse_tasks(md_text: str) -> list[tuple[int, str]]:
    """Return [(task_number, heading_title), ...] in file order."""
    out: list[tuple[int, str]] = []
    for line in md_text.splitlines():
        m = _TASK_HEADING_RE.match(line)
        if m:
            out.append((int(m.group(1)), m.group(2).strip()))
    return out


def _derive_slug(md_path: Path) -> str:
    """Derive a plan slug from the markdown filename.

    `docs/plans/2026-04-18-behavioral-modes.md` -> `behavioral-modes`.
    Strips a leading ISO date prefix if present.
    """
    stem = md_path.stem
    m = re.match(r"^\d{4}-\d{2}-\d{2}-(.+)$", stem)
    return m.group(1) if m else stem


def _yaml_escape(value: str) -> str:
    """Double-quote a YAML scalar, escaping backslashes and quotes."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def build_yaml(md_path: Path, tasks: list[tuple[int, str]]) -> str:
    """Render the scaffold YAML text for the given tasks."""
    slug = _derive_slug(md_path)
    prose_rel = md_path.name  # sibling reference; author can edit if needed

    lines: list[str] = [
        f"# Scaffolded from {md_path.name}. Review and edit.",
        "version: 1",
        "plan:",
        f"  slug: {slug}",
        f"  prose: {prose_rel}",
        f"  goal: {_yaml_escape('TODO: one-sentence goal (see ' + md_path.name + ' header)')}",
        "",
        "nodes: []" if not tasks else "nodes:",
    ]

    ids: list[str] = []
    for i, (num, title) in enumerate(tasks):
        node_id = f"task_{num}_{_slugify_task_name(title)}"
        ids.append(node_id)
        lines.append(f"  - id: {node_id}")
        lines.append("    type: implement")
        lines.append(f"    description: {_yaml_escape(title)}")
        if i > 0:
            lines.append(f"    depends_on: [{ids[i - 1]}]")
        lines.append("    # TODO: fill in files.create / files.modify / verify commands")
        lines.append("    verify: []")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def scaffold(md_path: Path, *, force: bool = False) -> tuple[Path, list[tuple[int, str]], list[str]]:
    """Write a YAML skeleton sibling to `md_path`.

    Returns `(yaml_path, tasks, validation_errors)`. Raises `FileNotFoundError`
    if the markdown does not exist, and `FileExistsError` if the YAML is
    already present and `force` is false.
    """
    md_path = Path(md_path)
    if not md_path.exists():
        raise FileNotFoundError(f"plan markdown not found: {md_path}")

    yaml_path = md_path.with_suffix(".yaml")
    if yaml_path.exists() and not force:
        raise FileExistsError(
            f"refusing to overwrite existing YAML: {yaml_path} (use --force)"
        )

    tasks = _parse_tasks(md_path.read_text())
    yaml_text = build_yaml(md_path, tasks)
    yaml_path.write_text(yaml_text)

    # Sanity-check the scaffold parses + validates. Dangling deps and empty
    # verifies are expected noise; we still surface them so the author knows
    # what's left.
    try:
        plan = plan_exec.load(yaml_path)
        errors = plan_exec.validate(plan, repo_root=md_path.parent)
    except plan_exec.PlanParseError as e:
        errors = [f"PlanParseError: {e}"]

    return yaml_path, tasks, errors


# ── CLI ───────────────────────────────────────────────────────────────────────


@app.callback(invoke_without_command=True)
def _main(
    plan_md: Path = typer.Argument(..., help="Path to the prose plan markdown."),
    force: bool = typer.Option(
        False, "--force", help="Overwrite an existing sibling .yaml."
    ),
):
    """Scaffold a YAML sidecar alongside an existing plan markdown."""
    try:
        yaml_path, tasks, errors = scaffold(plan_md, force=force)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=2)
    except FileExistsError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)

    typer.echo(f"wrote {yaml_path}")
    typer.echo(f"  {len(tasks)} task heading(s) detected")
    typer.echo("  review and fill in `verify:`, `depends_on:`, and gate placements.")

    if errors:
        typer.echo("")
        typer.echo("validation notes (expected for a fresh scaffold):")
        for err in errors:
            typer.echo(f"  - {err}")
