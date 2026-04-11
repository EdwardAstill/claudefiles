"""cf setup — check tool dependencies for skills installed in this project."""

import shutil
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(invoke_without_command=True)


def _find_manifest() -> Optional[Path]:
    """Locate manifest.toml from common install locations."""
    candidates = [
        Path.home() / ".claudefiles" / "manifest.toml",
        Path(__file__).parent.parent.parent.parent.parent / "manifest.toml",
        Path.home() / ".local" / "share" / "claudefiles-src" / "manifest.toml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _parse_manifest(manifest_path: Path) -> tuple[dict, dict]:
    """Parse manifest.toml, return (skills_data, cli_data).

    skills_data: {skill_name: {tools: [], mcp: [], cli: []}}
    cli_data: {cli_name: {manager, package, description, install}}
    """
    skills_data: dict = {}
    cli_data: dict = {}
    current_section = None
    current_key = None

    try:
        for raw_line in manifest_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[skills.") and line.endswith("]"):
                current_section = "skills"
                current_key = line[8:-1]
                skills_data[current_key] = {"tools": [], "mcp": [], "cli": []}
            elif line.startswith("[cli.") and line.endswith("]"):
                current_section = "cli"
                current_key = line[5:-1]
                cli_data[current_key] = {"manager": "?", "package": current_key, "description": "", "install": ""}
            elif line.startswith("["):
                current_section = None
                current_key = None
            elif current_section == "skills" and current_key and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                # Parse TOML array: tools = ["Bash", "Read"]
                val = val.strip().lstrip("[").rstrip("]")
                items = [v.strip().strip('"') for v in val.split(",") if v.strip().strip('"')]
                if key == "tools":
                    skills_data[current_key]["tools"] = items
                elif key == "mcp":
                    skills_data[current_key]["mcp"] = items
                elif key == "cli":
                    skills_data[current_key]["cli"] = items
            elif current_section == "cli" and current_key and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"')
                if key in ("manager", "package", "description", "install"):
                    cli_data[current_key][key] = val
    except Exception as e:
        import sys
        print(f"Warning: failed to parse manifest {manifest_path}: {e}", file=sys.stderr)

    return skills_data, cli_data


def _read_skill_name(skill_md: Path) -> Optional[str]:
    for line in skill_md.read_text().splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def _discover_project_skills(project_skills_dir: Path) -> list[str]:
    """Return list of skill names found in the given directory."""
    names = []
    if not project_skills_dir.exists():
        return names
    for skill_md in sorted(project_skills_dir.rglob("SKILL.md")):
        name = _read_skill_name(skill_md)
        if name:
            names.append(name)
    return names


def _build_report(skill_names: list[str], skills_data: dict, cli_data: dict) -> list[str]:
    """Build a list of output lines for the dependency report."""
    lines = []
    lines.append("# Project Skill Dependencies")
    lines.append("")

    # Collect which package managers are needed
    used_mgrs: set[str] = set()
    for name in skill_names:
        if name in skills_data:
            for cli_name in skills_data[name].get("cli", []):
                mgr = cli_data.get(cli_name, {}).get("manager", "?")
                if mgr != "?":
                    used_mgrs.add(mgr)

    mgr_install_cmds = {
        "bun": "curl -fsSL https://bun.sh/install | bash",
        "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "cargo": "curl https://sh.rustup.rs -sSf | sh",
        "rustup": "curl https://sh.rustup.rs -sSf | sh",
    }

    # Package manager section (only if any needed)
    relevant_mgrs = [m for m in ["bun", "uv", "cargo", "rustup"] if m in used_mgrs]
    if relevant_mgrs:
        lines.append("## Package managers")
        for mgr in relevant_mgrs:
            if shutil.which(mgr):
                lines.append(f"  ✓  {mgr}")
            else:
                lines.append(f"  ✗  {mgr}   not installed")
                if mgr in mgr_install_cmds:
                    lines.append(f"       {mgr_install_cmds[mgr]}")
        lines.append("")

    any_missing = False

    for name in sorted(skill_names):
        lines.append(f"## {name}")
        if name not in skills_data:
            lines.append("  (not declared in manifest.toml)")
            lines.append("")
            continue

        skill_info = skills_data[name]
        tools = skill_info.get("tools", [])
        mcp_servers = skill_info.get("mcp", [])
        cli_tools = skill_info.get("cli", [])

        if tools:
            lines.append(f"  Claude tools : {', '.join(tools)}")
        if mcp_servers:
            lines.append(f"  MCP servers  : {', '.join(mcp_servers)}")

        for cli_name in cli_tools:
            info = cli_data.get(cli_name, {})
            mgr = info.get("manager", "?")
            pkg = info.get("package", cli_name)
            desc = info.get("description", "")
            inst = info.get("install", "") or f"{mgr} install -g {pkg}"

            if shutil.which(cli_name):
                lines.append(f"  ✓  {cli_name}  [{mgr}]  installed")
            else:
                any_missing = True
                lines.append(f"  ✗  {cli_name}  [{mgr}]  MISSING")
                if desc:
                    lines.append(f"       {desc}")
                if shutil.which(mgr):
                    lines.append(f"       Install: {inst}")
                else:
                    mgr_cmd = mgr_install_cmds.get(mgr, f"install {mgr}")
                    lines.append(f"       Install {mgr} first ({mgr_cmd}), then: {inst}")

        lines.append("")

    if not any_missing:
        lines.append("All dependencies satisfied.")

    return lines


@app.callback(invoke_without_command=True)
def main(
    write: bool = typer.Option(False, "--write", help="Write dependency report to .claudefiles/deps.md"),
    skills: Optional[str] = typer.Option(None, "--skills", help="Comma-separated list of skill names to check"),
) -> None:
    """Check tool dependencies for skills installed in this project."""
    project_skills_dir = Path(".claude") / "skills"

    # Determine which skills to check
    if skills:
        skill_names = [s.strip() for s in skills.split(",") if s.strip()]
    else:
        skill_names = _discover_project_skills(project_skills_dir)
        if not skill_names:
            typer.echo("No project skills found. Run this inside a project with skills installed.")
            typer.echo("Install skills with: cf install --project")
            return

    # Find and parse manifest
    manifest_path = _find_manifest()
    if manifest_path:
        skills_data, cli_data = _parse_manifest(manifest_path)
    else:
        skills_data, cli_data = {}, {}

    # Build report
    report_lines = _build_report(skill_names, skills_data, cli_data)
    output = "\n".join(report_lines)

    typer.echo(output)

    if write:
        bus_dir = Path(".claudefiles")
        bus_dir.mkdir(exist_ok=True)
        deps_file = bus_dir / "deps.md"
        deps_file.write_text(output + "\n")
        typer.echo(f"\n  Written to {deps_file}")
