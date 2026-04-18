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
    ("index", "index"),
    ("search", "search"),
    ("setup", "setup"),
    ("tools", "tools_cmd"),
    ("tree", "tree"),
    ("secrets", "secrets"),
    ("preview", "preview"),
    ("screenshot", "screenshot"),
    ("test-skill", "test_skill"),
    ("hub", "hub"),
    ("repo", "repo"),
    ("caveman", "caveman"),
    ("youtube", "youtube"),
    ("terminal", "terminal"),
    ("webscraper", "webscraper"),
    ("archetype", "archetype"),
    ("ak", "agent_knowledge"),
]

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Agent Files CLI - A personal skill suite for Agentic."""
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())

def _register():
    import importlib
    for name, module_name in _SUBCOMMANDS:
        try:
            mod = importlib.import_module(f"af.{module_name}")
            app.add_typer(mod.app, name=name)
        except ModuleNotFoundError as e:
            # Only silence missing submodules, not missing dependencies
            if f"af.{module_name}" in str(e):
                pass
            else:
                print(f"Warning: af {name}: {e}", file=sys.stderr)

_register()


# Register install as a visible command (actual execution is intercepted in _run)
@app.command()
def install():
    """Install agentfiles skills, hooks, and CLI tools."""
    pass  # Never reached; _run() intercepts first


@app.command()
def research():
    """Scaffold a deep-research session (PROMPT.md + output dir)."""
    pass  # Never reached; _run() intercepts first


def _run():
    """Entry point — intercepts commands that need passthrough arg handling."""
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        from af.install import install_cmd
        install_cmd(sys.argv[2:], standalone_mode=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "research":
        # Intercepted because Typer treats a sub-typer-with-positional as a
        # group expecting a COMMAND token. research uses argparse directly.
        from af.research import cli as research_cli
        research_cli(sys.argv[2:])
    else:
        app()


if __name__ == "__main__":
    _run()
