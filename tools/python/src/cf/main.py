import typer

app = typer.Typer()

_SUBCOMMANDS = [
    ("context", "context"),
    ("status", "status"),
    ("versions", "versions"),
    ("routes", "routes"),
    ("note", "note"),
    ("read", "read"),
    ("init", "init"),
    ("worktree", "worktree"),
    ("agents", "agents"),
    ("check", "check"),
    ("setup", "setup"),
    ("github", "github"),
    ("browser", "browser"),
    ("install", "install"),
    ("tools", "tools_cmd"),
]

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Claude Files CLI - A personal skill suite for Claude Code."""
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())

def _register():
    import importlib
    for name, module_name in _SUBCOMMANDS:
        try:
            mod = importlib.import_module(f"cf.{module_name}")
            app.add_typer(mod.app, name=name)
        except ImportError:
            pass

_register()

if __name__ == "__main__":
    app()
