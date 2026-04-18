"""af caveman — backwards-compatible alias for `af mode on/off caveman`.

The caveman mode was the original ad-hoc behavioral mode. It has since been
ported to the generic `agentfiles/modes/` primitive (see
`agentfiles/modes/caveman/MODE.md`). This module is kept as a thin wrapper so
existing shortcuts (shell aliases, fish config, muscle memory) keep working.

Legacy state file `~/.claude/caveman-mode` is still read on first use and
migrated to `~/.claude/modes/caveman`.
"""

from __future__ import annotations

from pathlib import Path

import typer

from af import mode as mode_mod

app = typer.Typer(help="Toggle caveman mode — alias for `af mode on/off caveman`.")

LEGACY_STATE = Path.home() / ".claude" / "caveman-mode"

# User-friendly aliases → canonical level. Matches legacy behaviour.
ALIASES = {
    "lite": "lite",
    "full": "full",
    "actual": "actual-caveman",
    "actual-caveman": "actual-caveman",
    "cave": "actual-caveman",
    "caveman": "actual-caveman",
    "on": "full",
}

LEVEL_DESC = {
    "lite": "light touch — drops filler, keeps grammar (no quality hit)",
    "full": "max token save — drops articles too, fragments OK (slight quality hit)",
    "actual-caveman": "grunt style with cave analogies (novelty, not for serious work)",
}


def _migrate_legacy() -> None:
    """If the old `~/.claude/caveman-mode` file exists, migrate to new state dir."""
    if not LEGACY_STATE.exists():
        return
    try:
        level = LEGACY_STATE.read_text().strip().lower() or "full"
    except OSError:
        return
    canon = ALIASES.get(level, "full")
    mode_mod.activate("caveman", canon)
    try:
        LEGACY_STATE.unlink()
    except OSError:
        pass


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context):
    """Toggle caveman mode. With no subcommand, shows status."""
    _migrate_legacy()
    if ctx.invoked_subcommand is None:
        _status()


@app.command()
def on(
    level: str = typer.Argument("full", help="lite | full | actual-caveman"),
):
    """Enable caveman mode at the given level."""
    _migrate_legacy()
    canon = ALIASES.get(level.strip().lower())
    if not canon:
        typer.echo(
            f"Unknown level: {level}. Choose from: lite, full, actual-caveman.",
            err=True,
        )
        raise typer.Exit(1)
    mode_mod.activate("caveman", canon)
    typer.echo(f"caveman mode: ON ({canon}) — {LEVEL_DESC[canon]}")


@app.command()
def off():
    """Disable caveman mode."""
    _migrate_legacy()
    _off()


@app.command()
def status():
    """Show current caveman-mode state."""
    _migrate_legacy()
    _status()


def _off() -> None:
    active = mode_mod.active_modes()
    if "caveman" in active:
        mode_mod.deactivate("caveman")
    typer.echo("caveman mode: OFF")


def _status() -> None:
    active = mode_mod.active_modes()
    level = active.get("caveman")
    if level is None:
        typer.echo("caveman mode: OFF")
        return
    canon = ALIASES.get(level, level)
    desc = LEVEL_DESC.get(canon, "")
    typer.echo(f"caveman mode: ON ({canon}) — {desc}")
