import typer
import subprocess
import socket
import os
from pathlib import Path
from typing import Optional
from af.lib import git_root

app = typer.Typer(invoke_without_command=True)

def find_free_port(start: int = 3000) -> int:
    """Find the first available port starting from start."""
    for port in range(start, start + 100):
        with socket.socket() as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    return start

@app.callback(invoke_without_command=True)
def main(
    branch: str = typer.Argument(...),
    base: str = typer.Argument("main"),
):
    root = git_root()
    repo_name = root.name
    worktree_path = root.parent / f"{repo_name}-{branch}"

    if worktree_path.exists():
        typer.echo(f"Worktree already exists: {worktree_path}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Creating worktree: {worktree_path}")
    result = subprocess.run(
        ["git", "-C", str(root), "worktree", "add", "-b", branch, str(worktree_path), base],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        typer.echo(result.stderr, err=True)
        raise typer.Exit(1)

    port = find_free_port()
    typer.echo(f"Worktree created at {worktree_path}", err=True)
    typer.echo(f"Port allocated: {port}", err=True)

    # Print WORKTREE CONTEXT block (for other tools to read)
    typer.echo("")
    typer.echo("WORKTREE CONTEXT")
    typer.echo(f"  Path:   {worktree_path}")
    typer.echo(f"  Branch: {branch}")
    typer.echo(f"  Port:   {port}")
    typer.echo("")

    typer.echo(f"Open Agentic with: claude {worktree_path}", err=True)

    # Try to launch Agentic in a new terminal
    term = os.environ.get("TERMINAL", "")
    if term:
        try:
            subprocess.Popen([term, "-e", f"claude {worktree_path}"])
            typer.echo(f"Opened Agentic in new terminal", err=True)
        except Exception as e:
            typer.echo(f"Could not open terminal: {e}", err=True)
    else:
        typer.echo("(No TERMINAL env set — open Agentic manually)", err=True)
