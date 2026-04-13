import typer
import json
import shutil
import importlib.resources as pkg_resources

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def main(as_json: bool = typer.Option(False, "--json")):
    """List all tools — internal af subcommands and external CLI dependencies."""
    data = json.loads(
        pkg_resources.files("af").joinpath("data/tools.json").read_text()
    )
    if as_json:
        typer.echo(json.dumps(data, indent=2))
        return
    for tool in data["tools"]:
        if tool["type"] == "external":
            status = "installed" if shutil.which(tool["name"]) else "missing"
            typer.echo(f"\n### {tool['name']}  [external — {status}]")
        else:
            typer.echo(f"\n### {tool['name']}  [internal]")
        typer.echo(f"  {tool['description']}")
        typer.echo(f"  Usage: {tool['usage']}")
