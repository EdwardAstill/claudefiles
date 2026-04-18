"""af audit — manifest consistency audit, scoped to the agentfiles repo.

Runs the full set of consistency checks defined in the `audit` subagent
(agentfiles/agents/audit.md). Emits a structured per-check report.

Checks:
  1. skill dirs → manifest
  2. manifest → skill dirs
  3. agent files → manifest
  4. manifest → agent files
  5. skill cli → [cli.*]
  6. [cli.*] → skill reference
  7. cli tools in PATH
  8. skills/ registry symlinks are valid and complete
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import typer

app = typer.Typer(help="Audit the agentfiles manifest for consistency.")


_TOML_SECTION_RE = re.compile(r"^\[(skills|agents|cli)\.([^\]]+)\]")
_CLI_LIST_RE = re.compile(r'cli\s*=\s*\[([^\]]+)\]')


def _find_repo_root() -> Path:
    for p in (Path.cwd(), *Path.cwd().parents):
        if (p / "manifest.toml").is_file() and (p / "agentfiles").is_dir():
            return p
    typer.echo("error: not inside an agentfiles repo (no manifest.toml + agentfiles/)", err=True)
    raise typer.Exit(code=2)


def _parse_manifest(path: Path) -> dict[str, set[str]]:
    sections: dict[str, set[str]] = {"skills": set(), "agents": set(), "cli": set()}
    declared_cli: set[str] = set()
    for line in path.read_text().splitlines():
        m = _TOML_SECTION_RE.match(line.strip())
        if m:
            sections[m.group(1)].add(m.group(2))
            continue
        cli_m = _CLI_LIST_RE.search(line)
        if cli_m:
            for name in re.findall(r'"([^"]+)"', cli_m.group(1)):
                declared_cli.add(name)
    sections["declared_cli"] = declared_cli
    return sections


def _skills_on_disk(agentfiles_dir: Path) -> set[str]:
    names: set[str] = set()
    for skill_md in agentfiles_dir.rglob("SKILL.md"):
        # Skip agents/ dir (not a skill dir)
        if "agents" in skill_md.parent.parts:
            continue
        for line in skill_md.read_text().splitlines():
            if line.startswith("name:"):
                names.add(line.split(":", 1)[1].strip())
                break
    return names


def _agents_on_disk(agentfiles_dir: Path) -> set[str]:
    agents_dir = agentfiles_dir / "agents"
    if not agents_dir.is_dir():
        return set()
    names: set[str] = set()
    for md in agents_dir.glob("*.md"):
        for line in md.read_text().splitlines():
            if line.startswith("name:"):
                names.add(line.split(":", 1)[1].strip())
                break
        else:
            names.add(md.stem)
    return names


def _registry_symlinks(repo_root: Path) -> tuple[set[str], list[str]]:
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        return set(), []
    names: set[str] = set()
    problems: list[str] = []
    for entry in skills_dir.iterdir():
        if entry.name.startswith("."):
            continue
        if not entry.is_symlink():
            problems.append(f"skills/{entry.name} — not a symlink (real file/dir, should be ../agentfiles/...)")
            continue
        target = entry.resolve()
        if not target.exists():
            problems.append(f"skills/{entry.name} — broken symlink → {entry.readlink()}")
            continue
        names.add(entry.name)
    return names, problems


@app.callback(invoke_without_command=True)
def audit():
    """Run the full manifest consistency audit."""
    repo_root = _find_repo_root()
    agentfiles_dir = repo_root / "agentfiles"
    manifest_path = repo_root / "manifest.toml"

    manifest = _parse_manifest(manifest_path)
    disk_skills = _skills_on_disk(agentfiles_dir)
    disk_agents = _agents_on_disk(agentfiles_dir)
    registry_skills, registry_problems = _registry_symlinks(repo_root)

    issues: list[str] = []
    passed: list[str] = []

    # Check 1: skill dirs → manifest
    missing_in_manifest = disk_skills - manifest["skills"]
    if missing_in_manifest:
        for n in sorted(missing_in_manifest):
            issues.append(f"  ✗ skill '{n}' on disk — add [skills.{n}] entry to manifest.toml")
        passed.append(f"CHECK 1 (skill dirs → manifest): {len(disk_skills) - len(missing_in_manifest)}/{len(disk_skills)} ok, {len(missing_in_manifest)} missing")
    else:
        passed.append(f"CHECK 1 (skill dirs → manifest): ✓ all {len(disk_skills)} registered")

    # Check 2: manifest → skill dirs
    orphan_skill_entries = manifest["skills"] - disk_skills
    if orphan_skill_entries:
        for n in sorted(orphan_skill_entries):
            issues.append(f"  ✗ manifest [skills.{n}] has no SKILL.md — create or remove the entry")

    # Check 3: agent files → manifest
    missing_agent_entries = disk_agents - manifest["agents"]
    if missing_agent_entries:
        for n in sorted(missing_agent_entries):
            issues.append(f"  ✗ agent '{n}' on disk — add [agents.{n}] entry to manifest.toml")

    # Check 4: manifest → agent files
    orphan_agent_entries = manifest["agents"] - disk_agents
    if orphan_agent_entries:
        for n in sorted(orphan_agent_entries):
            issues.append(f"  ✗ manifest [agents.{n}] has no .md file — create or remove the entry")

    # Check 5: skill cli → [cli.*]
    declared = manifest["declared_cli"]
    registered = manifest["cli"]
    undeclared_cli = declared - registered
    if undeclared_cli:
        for n in sorted(undeclared_cli):
            issues.append(f"  ✗ CLI '{n}' referenced by a skill but [cli.{n}] missing from manifest")

    # Check 6: [cli.*] → skill reference
    orphan_cli = registered - declared
    if orphan_cli:
        for n in sorted(orphan_cli):
            issues.append(f"  ✗ [cli.{n}] registered but no skill declares cli = [\"{n}\"]")

    # Check 7: cli tools on PATH
    missing_cli = [n for n in sorted(registered) if shutil.which(n) is None]
    if missing_cli:
        for n in missing_cli:
            issues.append(f"  ✗ CLI '{n}' not on PATH — see [cli.{n}] install hint in manifest.toml")

    # Check 8: registry symlinks
    if registry_problems:
        for p in registry_problems:
            issues.append(f"  ✗ {p}")
    missing_registry = disk_skills - registry_skills
    if missing_registry:
        for n in sorted(missing_registry):
            issues.append(f"  ✗ agentfiles skill '{n}' has no skills/{n} registry symlink — af install won't see it")

    # Render
    for line in passed:
        typer.echo(line)
    if issues:
        typer.echo("")
        typer.echo("Issues:")
        for line in issues:
            typer.echo(line)

    total_checks = 8
    failed_checks = sum([
        bool(missing_in_manifest),
        bool(orphan_skill_entries),
        bool(missing_agent_entries),
        bool(orphan_agent_entries),
        bool(undeclared_cli),
        bool(orphan_cli),
        bool(missing_cli),
        bool(registry_problems or missing_registry),
    ])
    typer.echo("")
    typer.echo(f"SUMMARY: {total_checks - failed_checks}/{total_checks} checks passed, {len(issues)} issue(s)")
    if failed_checks:
        raise typer.Exit(code=1)
