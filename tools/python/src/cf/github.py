import typer

app = typer.Typer(help="GitHub — PRs, issues, branches (coming soon)")


@app.callback(invoke_without_command=True)
def main():
    typer.echo("cf github: coming soon. Subcommands will be added here.")
