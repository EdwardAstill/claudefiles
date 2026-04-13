"""af agents — overview of all Agentic skills and MCP servers across every scope."""

import json
import shutil
import tomllib
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


def _load_manifest_categories() -> dict[str, str]:
    """Load skill -> category mappings from manifest.toml. Returns empty dict if not found."""
    candidates = [
        Path("./manifest.toml"),
        Path.home() / ".local" / "share" / "agentfiles-src" / "manifest.toml",
        Path.home() / ".agentfiles" / "manifest.toml",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                data = tomllib.loads(candidate.read_text())
                skills = data.get("skills", {})
                return {
                    name: info["category"]
                    for name, info in skills.items()
                    if isinstance(info, dict) and "category" in info
                }
            except Exception:
                pass
    return {}


def render_grouped(skills_dir: Path, title: str) -> None:
    """Render skills grouped by category in a compact format."""
    if not skills_dir.exists():
        typer.echo(f"{title}: (none)")
        return

    # Collect all skill names from the skills directory
    skill_names: list[str] = []
    for item in sorted(skills_dir.iterdir()):
        if item.is_dir() or item.is_symlink():
            skill_names.append(item.name)

    if not skill_names:
        typer.echo(f"{title}: (none)")
        return

    # Load category mappings
    categories = _load_manifest_categories()

    # Group skills by category
    grouped: dict[str, list[str]] = {}
    for name in skill_names:
        cat = categories.get(name, "(uncategorized)")
        grouped.setdefault(cat, []).append(name)

    # Sort categories, putting (uncategorized) last
    sorted_cats = sorted(k for k in grouped if k != "(uncategorized)")
    if "(uncategorized)" in grouped:
        sorted_cats.append("(uncategorized)")

    typer.echo(f"\n{title}\n")

    col_width = 28
    wrap_at = 100

    for cat in sorted_cats:
        skills = grouped[cat]
        prefix = f"  {cat:<{col_width}}"
        line = prefix
        for skill in skills:
            candidate = line + skill + "  "
            if len(candidate) > wrap_at and line != prefix:
                typer.echo(line.rstrip())
                line = " " * (col_width + 2) + skill + "  "
            else:
                line = candidate
        typer.echo(line.rstrip())


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
        data_text = pkg_resources.files("af").joinpath("data/tools.json").read_text()
        data = json.loads(data_text)
        return data.get("tools", [])
    except Exception:
        return []


@app.callback(invoke_without_command=True)
def main(
    tree: bool = typer.Option(False, "--tree", help="Print skill hierarchy as indented tree"),
    global_: bool = typer.Option(False, "--global", help="User-level skills only"),
    project: bool = typer.Option(False, "--project", help="Project-level skills only"),
    available: bool = typer.Option(False, "--available", help="Skills in agentfiles not yet installed"),
    mcp: bool = typer.Option(False, "--mcp", help="MCP servers only"),
) -> None:
    """Overview of all Agentic skills and MCP servers across every scope."""
    claude_user_skills = Path.home() / ".claude" / "skills"
    claude_project_skills = Path(".claude") / "skills"
    gemini_user_skills = Path.home() / ".gemini" / "skills"
    gemini_project_skills = Path(".gemini") / "skills"

    if tree:
        if claude_user_skills.exists():
            render_tree(claude_user_skills, "CLAUDE USER SKILLS (~/.claude/skills/)")
        if gemini_user_skills.exists():
            render_tree(gemini_user_skills, "GEMINI USER SKILLS (~/.gemini/skills/)")
        if claude_project_skills.exists():
            render_tree(claude_project_skills, "CLAUDE PROJECT SKILLS (.claude/skills/)")
        if gemini_project_skills.exists():
            render_tree(gemini_project_skills, "GEMINI PROJECT SKILLS (.gemini/skills/)")
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
        # Show skills in agentfiles not yet installed
        # Try to find the agentfiles relative to this package install
        agentfiles = _find_agentfiles()
        if agentfiles is None:
            typer.echo("Cannot find agentfiles. Is agentfiles installed?")
            return
        typer.echo("AVAILABLE IN AGENTFILES (not yet installed)")
        found_any = False
        
        # Collect all installed skill names across all scopes
        installed_names = set()
        for p in [claude_user_skills, claude_project_skills, gemini_user_skills, gemini_project_skills]:
            if p.exists():
                for f in p.rglob("SKILL.md"):
                    name = _read_skill_name(f)
                    if name:
                        installed_names.add(name)

        for skill_md in sorted(agentfiles.rglob("SKILL.md")):
            name = _read_skill_name(skill_md)
            if not name:
                continue
            if name not in installed_names:
                typer.echo(f"  • {name}  [not installed]")
                found_any = True
        if not found_any:
            typer.echo("  (all agentfiles skills are installed)")
        return

    if not global_ and not project:
        # Full overview
        typer.echo("=== AGENTIC AGENTS OVERVIEW ===\n")

        plugins = get_plugin_info()
        if plugins:
            typer.echo("PLUGINS (Claude)")
            for p in plugins:
                typer.echo(f"  {p.get('name', '?')} ({p.get('version', '?')})")
            typer.echo("")

        if claude_user_skills.exists():
            render_grouped(claude_user_skills, "CLAUDE USER SKILLS")
        if gemini_user_skills.exists():
            render_grouped(gemini_user_skills, "GEMINI USER SKILLS")
        if claude_project_skills.exists():
            render_grouped(claude_project_skills, "CLAUDE PROJECT SKILLS")
        if gemini_project_skills.exists():
            render_grouped(gemini_project_skills, "GEMINI PROJECT SKILLS")

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
        if claude_user_skills.exists():
            render_grouped(claude_user_skills, "CLAUDE USER SKILLS (~/.claude/skills/)")
        if gemini_user_skills.exists():
            render_grouped(gemini_user_skills, "GEMINI USER SKILLS (~/.gemini/skills/)")
    elif project:
        if claude_project_skills.exists():
            render_grouped(claude_project_skills, "CLAUDE PROJECT SKILLS (.claude/skills/)")
        if gemini_project_skills.exists():
            render_grouped(gemini_project_skills, "GEMINI PROJECT SKILLS (.gemini/skills/)")


def _find_agentfiles() -> Optional[Path]:
    """Try to locate the agentfiles directory from common install locations."""
    candidates = [
        Path.home() / ".agentfiles" / "agentfiles",
        Path.home() / ".local" / "share" / "agentfiles-src" / "agentfiles",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None
