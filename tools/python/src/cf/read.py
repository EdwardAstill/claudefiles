import typer
from typing import Optional
from cf.lib import bus

app = typer.Typer(invoke_without_command=True)

FILE_MAP = {
    "context": "context.md",
    "versions": "versions.md",
    "routes": "routes.md",
    "repo-map": "repo-map.md",
    "notes": "notes.md",
}
DIVIDER = "─" * 60

@app.callback(invoke_without_command=True)
def main(target: Optional[str] = typer.Argument(None)):
    b = bus()
    if not b.exists():
        typer.echo("No .claudefiles/ bus found. Run: cf init")
        raise typer.Exit(1)

    def print_file(name):
        p = b / name
        if p.exists():
            typer.echo(DIVIDER)
            typer.echo(p.read_text(), nl=False)

    if target:
        filename = FILE_MAP.get(target)
        if not filename:
            typer.echo(f"Unknown file: {target}. Valid: {', '.join(FILE_MAP)}", err=True)
            raise typer.Exit(1)
        print_file(filename)
    else:
        for name in FILE_MAP.values():
            print_file(name)
