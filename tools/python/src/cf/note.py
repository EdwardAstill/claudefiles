import typer
from datetime import datetime
from typing import Optional
from cf.lib import bus, ensure_bus

app = typer.Typer(invoke_without_command=True)

@app.callback(invoke_without_command=True)
def main(
    message: Optional[str] = typer.Argument(None),
    agent: str = typer.Option("agent", "--agent"),
    read: bool = typer.Option(False, "--read"),
    clear: bool = typer.Option(False, "--clear"),
):
    notes_file = bus() / "notes.md"

    if read:
        if notes_file.exists():
            typer.echo(notes_file.read_text(), nl=False)
        else:
            typer.echo("(no notes yet)")
        return

    if clear:
        if not notes_file.exists():
            typer.echo("Nothing to clear.")
            return
        notes_file.unlink()
        typer.echo("Cleared.")
        return

    if not message:
        typer.echo("Usage: cf note [--agent <name>] <message>", err=True)
        raise typer.Exit(1)

    ensure_bus()
    if not notes_file.exists():
        notes_file.write_text("# SESSION NOTES\n# .claudefiles/notes.md\n\n")

    ts = datetime.now().strftime("%H:%M:%S")
    with notes_file.open("a") as f:
        f.write(f"[{ts}] [{agent}]\n{message}\n\n")
    typer.echo(f"Note appended to {notes_file}")
