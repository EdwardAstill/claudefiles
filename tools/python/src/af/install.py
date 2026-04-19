"""af install — install agentfiles skills, hooks, and CLI tools.

This is the main installer. install.sh is just a minimal bootstrap that installs
the af CLI and the agentfiles-manager skill. Everything else goes through here.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click


def _find_repo_root() -> Path:
    """Locate the agentfiles repo root."""
    import af

    repo_root = Path(af.__file__).resolve().parent.parent.parent.parent.parent
    if (repo_root / "manifest.toml").is_file():
        return repo_root

    env_root = os.environ.get("AGENT_PLUGIN_ROOT")
    if env_root:
        p = Path(env_root)
        if (p / "manifest.toml").is_file():
            return p

    # Try the standard clone location
    clone = Path.home() / ".local" / "share" / "agentfiles-src"
    if (clone / "manifest.toml").is_file():
        return clone

    raise FileNotFoundError(
        f"Cannot find agentfiles repo (searched {repo_root}, $AGENT_PLUGIN_ROOT, {clone})"
    )


# ── Manifest parsing ────────────────────────────────────────────────────────


def _parse_manifest(manifest_path: Path) -> tuple[dict, dict]:
    """Parse manifest.toml, return (skills_data, cli_data)."""
    skills_data: dict = {}
    cli_data: dict = {}
    current_section: Optional[str] = None
    current_key: Optional[str] = None

    for raw_line in manifest_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[skills.") and line.endswith("]"):
            current_section = "skills"
            current_key = line[8:-1]
            skills_data[current_key] = {"tools": [], "mcp": [], "cli": [], "category": ""}
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
            val = val.strip()
            if key == "category":
                skills_data[current_key]["category"] = val.strip('"')
            else:
                items = [v.strip().strip('"') for v in val.lstrip("[").rstrip("]").split(",") if v.strip().strip('"')]
                if key in ("tools", "mcp", "cli"):
                    skills_data[current_key][key] = items
        elif current_section == "cli" and current_key and "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if key == "install" and val.startswith("["):
                # Parse as array: install = ["cmd1", "cmd2"]
                items = [v.strip().strip('"') for v in val.lstrip("[").rstrip("]").split(",") if v.strip().strip('"')]
                cli_data[current_key]["install"] = items
            elif key in ("manager", "package", "description", "install"):
                cli_data[current_key][key] = val.strip('"')

    return skills_data, cli_data


# ── Skill discovery ─────────────────────────────────────────────────────────


def _discover_all_skills(agentfiles_dir: Path) -> dict[str, Path]:
    """Return {skill_name: skill_dir} for all skills in the agentfiles tree."""
    skills: dict[str, Path] = {}
    for skill_md in agentfiles_dir.rglob("SKILL.md"):
        for line in skill_md.read_text().splitlines():
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
                skills[name] = skill_md.parent
                break
    return skills


def _skills_in_category(all_skills: dict[str, Path], category: str) -> dict[str, Path]:
    """Filter skills whose path contains the given category."""
    result: dict[str, Path] = {}
    for name, path in all_skills.items():
        # Category matches if any part of the path matches
        parts = path.parts
        if category in parts:
            result[name] = path
    return result


def _list_categories(agentfiles_dir: Path) -> list[str]:
    """Return available top-level categories."""
    cats = set()
    for d in agentfiles_dir.iterdir():
        if d.is_dir() and not d.name.startswith(".") and d.name != "agents":
            cats.add(d.name)
    return sorted(cats)


# ── Agent discovery ─────────────────────────────────────────────────────────


def _discover_all_agents(agentfiles_dir: Path) -> dict[str, Path]:
    """Return {agent_name: agent_md_path} for all subagent defs in agentfiles/agents/."""
    agents_dir = agentfiles_dir / "agents"
    if not agents_dir.is_dir():
        return {}
    agents: dict[str, Path] = {}
    for md_path in sorted(agents_dir.glob("*.md")):
        for line in md_path.read_text().splitlines():
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
                agents[name] = md_path
                break
        else:
            # No name frontmatter — fall back to filename
            agents[md_path.stem] = md_path
    return agents


# ── Symlink helpers ──────────────────────────────────────────────────────────


def _do_symlink(src: Path, dst: Path, dry_run: bool) -> None:
    if dry_run:
        click.echo(f"  [dry-run] symlink: {dst} → {src}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink():
        dst.unlink()
    dst.symlink_to(src)
    click.echo(f"  [link] {dst} → {src}")


def _do_remove(dst: Path, dry_run: bool) -> None:
    if dry_run:
        click.echo(f"  [dry-run] remove: {dst}")
        return
    if dst.is_symlink():
        dst.unlink()
        click.echo(f"  [removed] {dst}")


def _prune_stale_symlinks(
    target_dir: Path,
    known_basenames: set[str],
    repo_root: Path,
    dry_run: bool,
    suffix: str = "",
) -> int:
    """Remove symlinks in target_dir that point into the agentfiles repo
    but whose basename is no longer in known_basenames.

    Only removes entries that both (a) are symlinks and (b) resolve to a path
    under repo_root — manual user symlinks from elsewhere are left alone.

    Returns the number of pruned entries.

    Args:
        suffix: file suffix to strip before comparing to known_basenames
                (e.g. ".md" for agents dir).
    """
    if not target_dir.is_dir():
        return 0

    pruned = 0
    repo_root = repo_root.resolve()
    for entry in sorted(target_dir.iterdir()):
        if not entry.is_symlink():
            continue

        basename = entry.name
        if suffix and basename.endswith(suffix):
            basename = basename[: -len(suffix)]
        if basename in known_basenames:
            continue

        # Broken symlink: prune (we know the name isn't registered and the
        # target is gone — can't do anything else useful with it).
        if not entry.exists():
            if dry_run:
                click.echo(f"  [dry-run] prune (broken): {entry}")
            else:
                entry.unlink()
                click.echo(f"  [pruned] {entry} (broken symlink)")
            pruned += 1
            continue

        # Live symlink: only prune if it points INTO the agentfiles repo.
        # Symlinks the user created by hand to external sources are left alone.
        resolved = entry.resolve()
        try:
            resolved.relative_to(repo_root)
        except ValueError:
            continue

        if dry_run:
            click.echo(f"  [dry-run] prune: {entry} (no longer in manifest)")
        else:
            entry.unlink()
            click.echo(f"  [pruned] {entry} (no longer in manifest)")
        pruned += 1

    return pruned


# ── CLI tool installation ────────────────────────────────────────────────────


def _install_cli_tools(cli_data: dict, dry_run: bool) -> None:
    """Install all missing CLI tools from manifest."""
    missing = []
    for cli_name, info in sorted(cli_data.items()):
        if not shutil.which(cli_name):
            missing.append((cli_name, info))

    if not missing:
        click.echo("  All CLI tools already installed.")
        return

    click.echo(f"  Installing {len(missing)} missing tool(s)...\n")
    failed = []
    for cli_name, info in missing:
        mgr = info.get("manager", "?")
        pkg = info.get("package", cli_name)
        raw_install = info.get("install", "")

        # Normalize to a list of commands to try in order
        if isinstance(raw_install, list):
            cmds = raw_install
        elif raw_install:
            cmds = [raw_install]
        else:
            cmds = [f"{mgr} install -g {pkg}"]

        if not shutil.which(mgr):
            click.echo(f"  ✗  {cli_name}: package manager '{mgr}' not found, skipping")
            failed.append(cli_name)
            continue

        if dry_run:
            click.echo(f"  [dry-run] {cli_name}: {cmds[0]}")
            if len(cmds) > 1:
                for alt in cmds[1:]:
                    click.echo(f"             fallback: {alt}")
        else:
            installed = False
            for i, cmd in enumerate(cmds):
                label = "→" if i == 0 else "↻"
                click.echo(f"  {label}  {cli_name}: {cmd}")
                result = subprocess.run(cmd, shell=True)
                if result.returncode == 0:
                    click.echo(f"  ✓  {cli_name} installed\n")
                    installed = True
                    break
                elif i < len(cmds) - 1:
                    click.echo(f"     failed, trying next...\n")
            if not installed:
                click.echo(f"  ✗  {cli_name} failed (all {len(cmds)} method(s) exhausted)\n")
                failed.append(cli_name)

    if failed:
        click.echo(f"\n  {len(failed)} tool(s) failed: {', '.join(failed)}")


# ── Hook wiring ──────────────────────────────────────────────────────────────


def _wire_hooks(repo_root: Path, targets: list[Path], dry_run: bool) -> None:
    """Symlink hooks and wire them into settings."""
    hooks_src = repo_root / "hooks"

    for target in targets:
        _do_symlink(hooks_src, target / "hooks", dry_run)

    # Claude hooks
    claude_hook_script = repo_root / "hooks" / "install-hooks.sh"
    if claude_hook_script.is_file():
        args = ["bash", str(claude_hook_script)]
        if dry_run:
            args.append("--dry-run")
        subprocess.run(args)

    # Gemini hooks
    gemini_hook_script = repo_root / "hooks" / "install-gemini-hooks.sh"
    if gemini_hook_script.is_file():
        gemini_target = str(Path.home() / ".gemini")
        if dry_run:
            click.echo(f"  [dry-run] would configure Gemini hooks in {gemini_target}")
        else:
            subprocess.run(["bash", str(gemini_hook_script), "--target", gemini_target])


# ── Agent config (AGENT.md → CLAUDE.md / GEMINI.md) ─────────────────────────


_MARKER_START = "# BEGIN agentfiles"
_MARKER_END = "# END agentfiles"

_AGENT_CONFIG_TARGETS = [
    Path.home() / ".claude" / "CLAUDE.md",
    Path.home() / ".gemini" / "GEMINI.md",
]


def _apply_agent_config(repo_root: Path, dry_run: bool) -> None:
    """Append AGENT.md contents to ~/.claude/CLAUDE.md and ~/.gemini/GEMINI.md.

    Uses markers to replace the block on reinstall instead of duplicating it.
    """
    agent_md = repo_root / "AGENT.md"
    if not agent_md.is_file():
        return

    content = agent_md.read_text().strip()
    block = f"{_MARKER_START}\n{content}\n{_MARKER_END}\n"

    click.echo("\nAgent config (AGENT.md):")
    for config_path in _AGENT_CONFIG_TARGETS:
        if dry_run:
            click.echo(f"  [dry-run] write to {config_path}")
            continue

        existing = config_path.read_text() if config_path.exists() else ""

        if _MARKER_START in existing:
            # Replace existing block in-place
            new_text = re.sub(
                rf"{re.escape(_MARKER_START)}.*?{re.escape(_MARKER_END)}\n?",
                block,
                existing,
                flags=re.DOTALL,
            )
            config_path.write_text(new_text)
            click.echo(f"  [updated] {config_path}")
        else:
            # Append with a blank line separator
            config_path.parent.mkdir(parents=True, exist_ok=True)
            sep = "\n" if existing and not existing.endswith("\n\n") else ""
            with config_path.open("a") as f:
                f.write(sep + block)
            click.echo(f"  [appended] {config_path}")


# ── GitHub source ────────────────────────────────────────────────────────────


def _resolve_github_source(repo_spec: str) -> Path:
    """Clone or update a GitHub repo, return its path."""
    clone_dir = Path.home() / ".local" / "share" / "agentfiles-src"

    if (clone_dir / ".git").is_dir():
        click.echo(f"  Updating from github.com/{repo_spec} ...")
        subprocess.run(["git", "-C", str(clone_dir), "pull", "--ff-only", "--quiet"], check=True)
    else:
        click.echo(f"  Cloning github.com/{repo_spec} → {clone_dir} ...")
        clone_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", f"https://github.com/{repo_spec}", str(clone_dir)], check=True)

    return clone_dir


# ── Main command ─────────────────────────────────────────────────────────────


@click.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option("--global", "global_mode", is_flag=True, default=False, help="Install globally to ~/.claude/skills/")
@click.option("--local", "local_mode", is_flag=True, default=False, help="Install to current project")
@click.option("--project", "local_mode", is_flag=True, default=False, hidden=True)
@click.option("--skill", "skill_name", default=None, help="Install a single skill by name")
@click.option("--category", default=None, help="Install all skills in a category")
@click.option("--remove", is_flag=True, default=False, help="Remove installed symlinks")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without making changes")
@click.option("--list-categories", is_flag=True, default=False, help="Show available categories")
@click.option("--from", "from_source", default=None, help="Source: github:owner/repo")
@click.argument("project_path", required=False, default=None)
def install_cmd(
    global_mode: bool,
    local_mode: bool,
    skill_name: Optional[str],
    category: Optional[str],
    remove: bool,
    dry_run: bool,
    list_categories: bool,
    from_source: Optional[str],
    project_path: Optional[str],
) -> None:
    """Install agentfiles skills, hooks, and CLI tools."""
    # Resolve source
    if from_source:
        if not from_source.startswith("github:"):
            click.echo(f"Error: unknown --from value '{from_source}'. Expected: github:<owner>/<repo>", err=True)
            raise SystemExit(1)
        repo_root = _resolve_github_source(from_source[7:])
    else:
        try:
            repo_root = _find_repo_root()
        except FileNotFoundError as e:
            click.echo(str(e), err=True)
            raise SystemExit(1)

    agentfiles_dir = repo_root / "agentfiles"
    manifest_path = repo_root / "manifest.toml"

    # List categories
    if list_categories:
        click.echo("Available categories:")
        for cat in _list_categories(agentfiles_dir):
            click.echo(f"  {cat}")
        raise SystemExit(0)

    # Default to global if neither specified
    if not global_mode and not local_mode:
        global_mode = True

    # Resolve targets
    if global_mode:
        targets = [
            Path.home() / ".claude" / "skills",
            Path.home() / ".gemini" / "skills",
        ]
        agent_targets = [Path.home() / ".claude" / "agents"]
    else:
        project = Path(project_path) if project_path else Path.cwd()
        targets = [
            project / ".claude" / "skills",
            project / ".gemini" / "skills",
        ]
        agent_targets = [project / ".claude" / "agents"]

    # Discover skills and agents
    all_skills = _discover_all_skills(agentfiles_dir)
    all_agents = _discover_all_agents(agentfiles_dir)

    # Determine which skills to install/remove
    if skill_name:
        if skill_name not in all_skills:
            click.echo(f"Error: skill '{skill_name}' not found in agentfiles", err=True)
            raise SystemExit(1)
        selected = {skill_name: all_skills[skill_name]}
    elif category:
        selected = _skills_in_category(all_skills, category)
        if not selected:
            click.echo(f"Error: no skills found in category '{category}'", err=True)
            raise SystemExit(1)
    else:
        selected = all_skills

    # Remove mode
    if remove:
        scope = "globally" if global_mode else "from project"
        click.echo(f"Removing {len(selected)} skill(s) {scope}...")
        for target in targets:
            for name in sorted(selected):
                _do_remove(target / name, dry_run)
            _do_remove(target / "hooks", dry_run)
        if not skill_name and not category:
            click.echo(f"Removing {len(all_agents)} agent(s) {scope}...")
            for agent_target in agent_targets:
                for name in sorted(all_agents):
                    _do_remove(agent_target / f"{name}.md", dry_run)
        raise SystemExit(0)

    # Install mode
    scope = "globally" if global_mode else "to project"
    click.echo(f"Installing {len(selected)} skill(s) {scope}...")

    for target in targets:
        # Ensure target directory exists
        if target.is_symlink() and not target.is_dir():
            target.unlink()
        target.mkdir(parents=True, exist_ok=True)

        for name in sorted(selected):
            skill_dir = selected[name]
            _do_symlink(skill_dir, target / name, dry_run)

    # Prune stale skill symlinks — only on full install (no --skill / --category).
    # Preserve non-skill entries that install.py itself creates (hooks, etc.).
    if not skill_name and not category:
        preserved = {"hooks", "commands"}
        keep = set(all_skills) | preserved
        for target in targets:
            pruned = _prune_stale_symlinks(
                target, keep, repo_root, dry_run
            )
            if pruned:
                click.echo(
                    f"  {pruned} stale skill symlink(s) pruned from {target}"
                )

    # Agents (only on full install — skill_name and category scopes skip agents)
    if all_agents and not skill_name and not category:
        click.echo(f"\nInstalling {len(all_agents)} subagent(s) {scope}...")
        for agent_target in agent_targets:
            if agent_target.is_symlink() and not agent_target.is_dir():
                agent_target.unlink()
            agent_target.mkdir(parents=True, exist_ok=True)
            for name in sorted(all_agents):
                _do_symlink(all_agents[name], agent_target / f"{name}.md", dry_run)

        # Prune stale agent symlinks.
        for agent_target in agent_targets:
            pruned = _prune_stale_symlinks(
                agent_target, set(all_agents), repo_root, dry_run, suffix=".md"
            )
            if pruned:
                click.echo(
                    f"  {pruned} stale agent symlink(s) pruned from {agent_target}"
                )

    # Hooks (global only, unless explicitly installing per-project)
    if global_mode:
        click.echo("\nHooks:")
        _wire_hooks(repo_root, targets, dry_run)

    # Agent config — append AGENT.md to ~/.claude/CLAUDE.md etc.
    if global_mode:
        _apply_agent_config(repo_root, dry_run)

    # CLI tools (global only, full install only)
    if global_mode and not skill_name and not category:
        click.echo("\nCLI Tools:")
        if manifest_path.is_file():
            _, cli_data = _parse_manifest(manifest_path)
            _install_cli_tools(cli_data, dry_run)
        else:
            click.echo("  manifest.toml not found, skipping CLI tools")

    # Gitignore for project installs
    if local_mode:
        project = Path(project_path) if project_path else Path.cwd()
        gitignore = project / ".gitignore"
        entry = ".agentfiles/"
        if dry_run:
            click.echo(f"\n  [dry-run] add {entry} to {gitignore}")
        else:
            if not gitignore.exists() or entry not in gitignore.read_text().splitlines():
                with gitignore.open("a") as f:
                    f.write(f"{entry}\n")

    click.echo("\nDone.")
