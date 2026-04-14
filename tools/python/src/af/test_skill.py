import json
from pathlib import Path

import typer

from af.lib import git_root

app = typer.Typer(invoke_without_command=True)

_TEMPLATE = {
    "version": 1,
    "skill_name": "",
    "skill_path": "",
    "evals": []
}


def _next_iteration(skill_dir: Path) -> int:
    n = 1
    while (skill_dir / f"iteration-{n}").exists():
        n += 1
    return n


@app.callback(invoke_without_command=True)
def main(
    skill_name: str = typer.Argument(..., help="Name of the skill to test"),
):
    """Scaffold a skill test workspace."""
    root = git_root()
    tests_dir = root / "tests"
    skill_dir = tests_dir / skill_name
    evals_path = skill_dir / "evals.json"

    # No evals.json — create template
    if not evals_path.exists():
        skill_dir.mkdir(parents=True, exist_ok=True)
        template = {**_TEMPLATE, "skill_name": skill_name}
        evals_path.write_text(json.dumps(template, indent=2) + "\n")
        typer.echo(f"Created template at {evals_path.relative_to(root)}")
        typer.echo("Fill in skill_path, evals (with prompt + reference_answer), then run again.")
        return

    # Load and validate
    data = json.loads(evals_path.read_text())
    if not data.get("evals"):
        typer.echo(f"No evals defined in {evals_path.relative_to(root)}. Add evals and run again.")
        return

    # Create workspace
    n = _next_iteration(skill_dir)
    workspace = skill_dir / f"iteration-{n}"
    workspace.mkdir(parents=True)
    typer.echo(f"Workspace ready at {workspace.relative_to(root)}/")
    typer.echo("Invoke the skill-tester skill to run evals.")
