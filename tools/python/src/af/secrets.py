import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import typer

app = typer.Typer(invoke_without_command=True)

_SECRETS_FILE = Path.home() / ".claude" / "secrets"


def _load() -> Dict[str, str]:
    """Load secrets from the secrets file. Returns empty dict if file doesn't exist."""
    secrets: Dict[str, str] = {}
    if not _SECRETS_FILE.exists():
        return secrets
    for line in _SECRETS_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            secrets[key.strip()] = value
    return secrets


def _save(secrets: Dict[str, str]) -> None:
    """Save secrets to the secrets file with chmod 600."""
    _SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}" for k, v in secrets.items()]
    _SECRETS_FILE.write_text("\n".join(lines) + ("\n" if lines else ""))
    _SECRETS_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Manage API keys and secrets stored in ~/.claude/secrets."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def set(
    key: str = typer.Argument(..., help="Secret key name"),
    value: str = typer.Argument(..., help="Secret value"),
) -> None:
    """Store or update a secret."""
    secrets = _load()
    secrets[key] = value
    _save(secrets)
    typer.echo(f"Set {key}")


@app.command()
def get(
    key: str = typer.Argument(..., help="Secret key name"),
) -> None:
    """Print the value of a secret."""
    secrets = _load()
    if key not in secrets:
        typer.echo(f"Error: key '{key}' not found", err=True)
        raise typer.Exit(1)
    typer.echo(secrets[key], nl=False)
    typer.echo("")


@app.command(name="list")
def list_keys() -> None:
    """List all secret key names (not values)."""
    secrets = _load()
    if not secrets:
        typer.echo("(no secrets stored)")
        return
    for key in secrets:
        typer.echo(key)


@app.command()
def remove(
    key: str = typer.Argument(..., help="Secret key name"),
) -> None:
    """Delete a secret."""
    secrets = _load()
    if key not in secrets:
        typer.echo(f"Error: key '{key}' not found", err=True)
        raise typer.Exit(1)
    del secrets[key]
    _save(secrets)
    typer.echo(f"Removed {key}")


@app.command()
def env() -> None:
    """Print all secrets as `export KEY=value` lines (for eval)."""
    secrets = _load()
    for key, value in secrets.items():
        typer.echo(f"export {key}={value}")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def exec(
    ctx: typer.Context,
    cmd: List[str] = typer.Argument(..., help="Command and arguments to run"),
) -> None:
    """Run a command with all secrets injected as environment variables."""
    if not cmd:
        typer.echo("Error: no command provided", err=True)
        raise typer.Exit(1)
    secrets = _load()
    env_vars = {**os.environ, **secrets}
    result = subprocess.run(cmd, env=env_vars)
    raise typer.Exit(result.returncode)
