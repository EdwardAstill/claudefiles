import typer
from cf.lib import ensure_bus, gitignore_bus, bus_exists

app = typer.Typer(invoke_without_command=True)

@app.callback(invoke_without_command=True)
def main(dry_run: bool = typer.Option(False, "--dry-run")):
    if dry_run:
        typer.echo("[dry-run] Would create .claudefiles/")
        typer.echo("[dry-run] Would add .claudefiles/ to .gitignore")
        typer.echo("[dry-run] Would generate: context.md, versions.md, routes.md, status.md")
        return

    ensure_bus()
    gitignore_bus()

    # Generate all context files
    from cf.context import main as ctx_main
    from cf.versions import main as ver_main
    from cf.routes import main as routes_main
    from cf.status import main as status_main

    typer.echo("Initializing .claudefiles/ ...", err=True)
    ctx_main(write=True)
    ver_main(write=True)
    routes_main(write=True)
    status_main(write=True)
    typer.echo("Done. .claudefiles/ is ready.", err=True)
