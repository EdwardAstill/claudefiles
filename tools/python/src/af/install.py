"""Thin wrapper around install.sh — delegates all install logic to the bash script."""

import subprocess
import sys
from pathlib import Path

import click


def _find_install_sh() -> Path:
    """Locate install.sh relative to this package's repo root."""
    import af

    repo_root = Path(af.__file__).resolve().parent.parent.parent.parent.parent
    script = repo_root / "install.sh"
    if script.is_file():
        return script

    import os

    env_root = os.environ.get("AGENT_PLUGIN_ROOT")
    if env_root:
        script = Path(env_root) / "install.sh"
        if script.is_file():
            return script

    raise FileNotFoundError(
        f"Cannot find install.sh (searched {repo_root} and $AGENT_PLUGIN_ROOT)"
    )


@click.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def install_cmd(args):
    """Install agentfiles skills — delegates to install.sh."""
    try:
        script = _find_install_sh()
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        raise SystemExit(1)

    result = subprocess.run(["bash", str(script)] + list(args))
    raise SystemExit(result.returncode)
