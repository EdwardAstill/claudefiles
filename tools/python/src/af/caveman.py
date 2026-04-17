"""af caveman — toggle persistent caveman mode across all Claude Code sessions.

Three levels: lite, full (default/recommended), actual-caveman. Plus off.
"""

from pathlib import Path

import typer

app = typer.Typer(help="Toggle persistent caveman-mode re-injection (UserPromptSubmit hook).")

STATE = Path.home() / ".claude" / "caveman-mode"

# Canonical levels
LEVELS = {"lite", "full", "actual-caveman"}
# User-friendly aliases → canonical
ALIASES = {
    "lite": "lite",
    "full": "full",
    "actual": "actual-caveman",
    "actual-caveman": "actual-caveman",
    "cave": "actual-caveman",
    "caveman": "actual-caveman",
}

LEVEL_DESC = {
    "lite": "light touch — drops filler, keeps grammar (no quality hit)",
    "full": "max token save — drops articles too, fragments OK (slight quality hit)",
    "actual-caveman": "grunt style with cave analogies (novelty, not for serious work)",
}


def _write(level: str) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(level + "\n")


@app.command()
def on(
    level: str = typer.Argument("full", help=f"Level: {', '.join(sorted(LEVELS))}."),
):
    """Enable persistent caveman mode at the given level."""
    canon = ALIASES.get(level.lower())
    if not canon:
        typer.echo(f"Unknown level: {level}. Choose from: {', '.join(sorted(LEVELS))}")
        raise typer.Exit(1)
    _write(canon)
    typer.echo(f"caveman mode: ON ({canon}) — {LEVEL_DESC[canon]}")


@app.command()
def off():
    """Disable persistent caveman mode."""
    if STATE.exists():
        STATE.unlink()
    typer.echo("caveman mode: OFF")


@app.command()
def status():
    """Show current caveman-mode state."""
    if STATE.exists():
        level = STATE.read_text().strip() or "full"
        canon = ALIASES.get(level, "full")
        typer.echo(f"caveman mode: ON ({canon}) — {LEVEL_DESC[canon]}")
    else:
        typer.echo("caveman mode: OFF")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Toggle persistent caveman mode. With no subcommand, shows status."""
    if ctx.invoked_subcommand is None:
        status()
