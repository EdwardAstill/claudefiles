"""af terminal — capture the current terminal's scrollback.

Use when the agent needs to see what just printed on the user's terminal —
e.g. "look at the output of setup.fish that just ran". Dumps scrollback so the
agent can Read it (or parse directly).

Supports, in order of preference:
  - tmux pane history    (requires $TMUX)
  - GNU screen hardcopy  (requires $STY)
  - script(1) typescript (if user piped output to a file)
  - pasted output via stdin

Default is to print to stdout; use --out to write a file (easier for the agent
to Read cleanly without tool-output truncation).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Capture this terminal's scrollback for the agent to inspect.")


def _capture_tmux(lines: int) -> Optional[str]:
    if not os.environ.get("TMUX"):
        return None
    # -S -lines: start N lines back. -p: print to stdout. -J: join wrapped lines.
    start = f"-{lines}" if lines > 0 else "-"
    try:
        out = subprocess.run(
            ["tmux", "capture-pane", "-p", "-J", "-S", start],
            check=True, capture_output=True, text=True,
        )
        return out.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _capture_screen(lines: int) -> Optional[str]:
    if not os.environ.get("STY"):
        return None
    try:
        with tempfile.NamedTemporaryFile("r", suffix=".txt", delete=False) as f:
            path = f.name
        subprocess.run(
            ["screen", "-X", "hardcopy", "-h", path], check=True
        )
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        Path(path).unlink(missing_ok=True)
        if lines > 0:
            text = "\n".join(text.splitlines()[-lines:])
        return text
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


@app.callback(invoke_without_command=True)
def main(
    lines: int = typer.Option(
        500, "--lines", "-n", help="How many recent lines to grab (0 = full buffer)"
    ),
    output: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Write capture to this path instead of stdout"
    ),
    stdin: bool = typer.Option(
        False, "--stdin", help="Read from stdin (for piping: `cmd 2>&1 | af terminal --stdin --out /tmp/log.txt`)"
    ),
):
    """Dump the current terminal's scrollback so the agent can see it."""
    text: Optional[str] = None
    source = "unknown"

    if stdin:
        text = sys.stdin.read()
        source = "stdin"
    else:
        text = _capture_tmux(lines)
        if text is not None:
            source = "tmux"
        else:
            text = _capture_screen(lines)
            if text is not None:
                source = "screen"

    if text is None:
        typer.echo(
            "[terminal] could not capture scrollback.\n"
            "  Not running inside tmux or screen. Options:\n"
            "    - Start tmux:       `tmux new -s work`  then re-run the command\n"
            "    - Pipe the command: `setup.fish 2>&1 | af terminal --stdin --out /tmp/setup.log`\n"
            "    - Record a session: `script -q /tmp/session.log` then exit; read the log\n",
            err=True,
        )
        raise typer.Exit(1)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        typer.echo(f"[terminal] source={source}  lines={len(text.splitlines())}  -> {output}", err=True)
    else:
        sys.stdout.write(text)
