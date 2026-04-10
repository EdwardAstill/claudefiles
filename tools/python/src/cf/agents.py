"""cf agents — overview of all Claude Code skills and MCP servers across every scope."""

import json
import shutil
import importlib.resources as pkg_resources
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(invoke_without_command=True)


def get_plugin_info() -> list[dict]:
    plugins_file = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    if not plugins_file.exists():
        return []
    try:
        data = json.loads(plugins_file.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, KeyError):
        return []


def walk_skills(skills_dir: Path, prefix: str = "") -> list[str]:
    """Return sorted list of skill paths relative to skills_dir."""
    if not skills_dir.exists():
        return []
    lines = []
    for item in sorted(skills_dir.iterdir()):
        if item.is_dir() or item.is_symlink():
            lines.append(f"{prefix}{item.name}/")
            if item.is_dir():
                lines.extend(walk_skills(item, prefix + "  "))
    return lines


def render_tree(skills_dir: Path, title: str) -> None:
    if not skills_dir.exists():
        typer.echo(f"{title}: (none)")
        return
    typer.echo(f"\n{title}")
    entries = sorted(skills_dir.iterdir()) if skills_dir.exists() else []
    count = len([e for e in entries if e.is_dir() or e.is_symlink()])
    i = 0
    for item in entries:
        if not (item.is_dir() or item.is_symlink()):
            continue
        i += 1
        is_last = i == count
        connector = "└──" if is_last else "├──"
        child_prefix = "    " if is_last else "│   "

        # Determine display name: use skill name from SKILL.md if present
        skill_md = item / "SKILL.md"
        if skill_md.exists():
            try:
                name = _read_skill_name(skill_md) or item.name
            except Exception:
                name = item.name
        else:
            name = item.name + "/"

        typer.echo(f"  {connector} {name}")

        # Print sub-entries
        if item.is_dir():
            sub_entries = sorted(item.iterdir())
            sub_dirs = [s for s in sub_entries if s.is_dir() or s.is_symlink()]
            for j, sub in enumerate(sub_dirs, 1):
                sub_last = j == len(sub_dirs)
                sub_connector = "└──" if sub_last else "├──"
                sub_skill_md = sub / "SKILL.md"
                if sub_skill_md.exists():
                    try:
                        sub_name = _read_skill_name(sub_skill_md) or sub.name
                    except Exception:
                        sub_name = sub.name
                else:
                    sub_name = sub.name + "/"
                typer.echo(f"  {child_prefix}  {sub_connector} {sub_name}")


def _read_skill_name(skill_md: Path) -> Optional[str]:
    for line in skill_md.read_text().splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def get_mcp_servers() -> dict:
    candidates = [
        Path(".mcp.json"),
        Path(".claude/mcp.json"),
        Path.home() / ".claude" / ".mcp.json",
        Path.home() / ".claude" / "mcp.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                data = json.loads(p.read_text())
                return data.get("mcpServers", data)
            except json.JSONDecodeError:
                pass
    return {}


def get_tools_data() -> list[dict]:
    try:
        data_text = pkg_resources.files("cf").joinpath("data/tools.json").read_text()
        data = json.loads(data_text)
        return data.get("tools", [])
    except Exception:
        return []


@app.callback(invoke_without_command=True)
def main(
    tree: bool = typer.Option(False, "--tree", help="Print skill hierarchy as indented tree"),
    global_: bool = typer.Option(False, "--global", help="User-level skills only"),
    project: bool = typer.Option(False, "--project", help="Project-level skills only"),
    available: bool = typer.Option(False, "--available", help="Skills in dev-suite not yet installed"),
    mcp: bool = typer.Option(False, "--mcp", help="MCP servers only"),
) -> None:
    """Overview of all Claude Code skills and MCP servers across every scope."""
    user_skills = Path.home() / ".claude" / "skills"
    project_skills = Path(".claude") / "skills"

    if tree:
        render_tree(user_skills, "USER SKILLS (~/.claude/skills/)")
        render_tree(project_skills, "PROJECT SKILLS (.claude/skills/)")
        return

    if mcp:
        servers = get_mcp_servers()
        if servers:
            typer.echo("MCP SERVERS")
            for name, cfg in servers.items():
                if isinstance(cfg, dict):
                    cmd = cfg.get("command", "")
                    args = " ".join(str(a) for a in cfg.get("args", []))
                    typer.echo(f"  {name}: {cmd} {args}".rstrip())
                else:
                    typer.echo(f"  {name}: {cfg}")
        else:
            typer.echo("No MCP servers configured.")
        return

    if available:
        # Show skills in dev-suite not yet installed
        cf_bin = Path(__file__).parent
        # Try to find the dev-suite relative to this package install
        dev_suite = _find_dev_suite()
        if dev_suite is None:
            typer.echo("Cannot find dev-suite. Is claudefiles installed?")
            return
        typer.echo("AVAILABLE IN CLAUDEFILES (not yet installed)")
        found_any = False
        for skill_md in sorted(dev_suite.rglob("SKILL.md")):
            name = _read_skill_name(skill_md)
            if not name:
                continue
            # Check if installed in user skills
            installed = any(
                True for f in user_skills.rglob("SKILL.md")
                if _read_skill_name(f) == name
            ) if user_skills.exists() else False
            if not installed:
                typer.echo(f"  • {name}  [not installed]")
                found_any = True
        if not found_any:
            typer.echo("  (all claudefiles skills are installed)")
        return

    if not global_ and not project:
        # Full overview
        typer.echo("=== CLAUDE AGENTS OVERVIEW ===\n")

        plugins = get_plugin_info()
        if plugins:
            typer.echo("PLUGINS")
            for p in plugins:
                typer.echo(f"  {p.get('name', '?')} ({p.get('version', '?')})")
            typer.echo("")

        render_tree(user_skills, "USER SKILLS")
        render_tree(project_skills, "PROJECT SKILLS")

        servers = get_mcp_servers()
        if servers:
            typer.echo("\nMCP SERVERS")
            for name in servers:
                typer.echo(f"  {name}")

        tools = get_tools_data()
        if tools:
            typer.echo("\nCLI TOOLS")
            for t in tools:
                if t.get("type") == "external":
                    status = "✓" if shutil.which(t["name"]) else "✗"
                    typer.echo(f"  {status} {t['name']}")
    elif global_:
        render_tree(user_skills, "USER SKILLS (~/.claude/skills/)")
    elif project:
        render_tree(project_skills, "PROJECT SKILLS (.claude/skills/)")


def _find_dev_suite() -> Optional[Path]:
    """Try to locate the dev-suite directory from common install locations."""
    candidates = [
        Path.home() / ".claudefiles" / "dev-suite",
        Path.home() / ".local" / "share" / "claudefiles-src" / "dev-suite",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None
