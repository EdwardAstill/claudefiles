import typer
from af.lib import ensure_bus, gitignore_bus, bus_exists

app = typer.Typer(invoke_without_command=True)

@app.callback(invoke_without_command=True)
def main(dry_run: bool = typer.Option(False, "--dry-run")):
    if dry_run:
        typer.echo("[dry-run] Would create .agentfiles/")
        typer.echo("[dry-run] Would add .agentfiles/ to .gitignore")
        typer.echo("[dry-run] Would generate: context.md, versions.md, routes.md, status.md")
        return

    ensure_bus()
    gitignore_bus()

    # Generate all context files
    from af.context import main as ctx_main
    from af.versions import main as ver_main
    from af.routes import main as routes_main
    from af.status import main as status_main

    typer.echo("Initializing .agentfiles/ ...", err=True)
    ctx_main(write=True)
    ver_main(write=True)
    routes_main(write=True)
    status_main(write=True)
    typer.echo("Done. .agentfiles/ is ready.", err=True)
