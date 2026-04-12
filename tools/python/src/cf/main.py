import sys
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
    ("log", "log"),
    ("setup", "setup"),
    ("tools", "tools_cmd"),
    ("tree", "tree"),
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
        except ModuleNotFoundError as e:
            # Only silence missing submodules, not missing dependencies
            if f"cf.{module_name}" in str(e):
                pass
            else:
                print(f"Warning: cf {name}: {e}", file=sys.stderr)

_register()


# Register install as a visible command (actual execution is intercepted in _run)
@app.command()
def install():
    """Install claudefiles skills — delegates to install.sh."""
    pass  # Never reached; _run() intercepts first


def _run():
    """Entry point — intercepts 'install' before Typer to allow passthrough args."""
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        from cf.install import install_cmd
        install_cmd(sys.argv[2:], standalone_mode=True)
    else:
        app()


if __name__ == "__main__":
    _run()
