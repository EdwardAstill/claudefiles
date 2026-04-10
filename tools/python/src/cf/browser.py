import typer

app = typer.Typer(help="Browser automation via Playwright (coming soon)")


@app.callback(invoke_without_command=True)
def main():
    typer.echo("cf browser: coming soon. Subcommands will be added here.")
