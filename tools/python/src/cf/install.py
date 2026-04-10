import typer
import os
import subprocess
from pathlib import Path
from typing import Optional

app = typer.Typer(invoke_without_command=True)


def get_source_repo(source: Optional[str]) -> Path:
    if source:
        return Path(source)
    env_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_root:
        return Path(env_root)
    # Fall back to the package's own location
    import cf
    return Path(cf.__file__).parent.parent.parent.parent.parent  # src/cf -> src -> python -> tools -> repo root


def find_skill_by_name(skills_root: Path, name: str) -> Optional[Path]:
    for skill_dir in skills_root.rglob("SKILL.md"):
        parent = skill_dir.parent
        if parent.name == name:
            return parent
    return None


def get_skills_source(repo: Path) -> Optional[Path]:
    for name in ("skills", "dev-suite"):
        p = repo / name
        if p.is_dir():
            return p
    return None


@app.callback(invoke_without_command=True)
def main(
    global_: bool = typer.Option(False, "--global"),
    local: Optional[str] = typer.Option(None, "--local"),
    skill: Optional[str] = typer.Option(None, "--skill"),
    category: Optional[str] = typer.Option(None, "--category"),
    from_: Optional[str] = typer.Option(None, "--from"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    remove: bool = typer.Option(False, "--remove"),
    source: Optional[str] = typer.Option(None, "--source"),
):
    """Install claudefiles skills to ~/.claude/skills/ or project .claude/skills/."""
    # Handle --from (github clone)
    if from_:
        if from_.startswith("github:"):
            _, repo_path = from_.split(":", 1)
            clone_dir = Path.home() / ".local" / "share" / "claudefiles-src"
            url = f"https://github.com/{repo_path}"
            if clone_dir.exists():
                typer.echo(f"Pulling latest from {url} ...")
                if not dry_run:
                    subprocess.run(["git", "-C", str(clone_dir), "pull", "--ff-only"], check=True)
            else:
                typer.echo(f"Cloning {url} to {clone_dir} ...")
                if not dry_run:
                    subprocess.run(["git", "clone", url, str(clone_dir)], check=True)
            source = str(clone_dir)
        else:
            typer.echo(f"Unknown --from format: {from_}. Use github:owner/repo", err=True)
            raise typer.Exit(1)

    repo = get_source_repo(source)
    skills_src = get_skills_source(repo)

    if skills_src is None:
        typer.echo(f"No skills/ or dev-suite/ found in {repo}", err=True)
        raise typer.Exit(1)

    # Determine target directory
    if global_:
        target = Path.home() / ".claude" / "skills"
    elif local:
        target = Path(local) / ".claude" / "skills"
    else:
        target = Path(".claude") / "skills"

    # Determine what to install
    if skill:
        src_skill = find_skill_by_name(skills_src, skill)
        if not src_skill:
            typer.echo(f"Skill not found: {skill}", err=True)
            raise typer.Exit(1)
        to_install = [(src_skill, target / skill)]
    elif category:
        cat_dir = skills_src / category
        if not cat_dir.is_dir():
            typer.echo(f"Category not found: {category}", err=True)
            raise typer.Exit(1)
        to_install = [(cat_dir, target / category)]
    else:
        # Install all top-level category directories
        to_install = [
            (cat, target / cat.name)
            for cat in sorted(skills_src.iterdir())
            if cat.is_dir()
        ]

    if remove:
        for _, link in to_install:
            if link.is_symlink():
                typer.echo(f"Removing symlink: {link}")
                if not dry_run:
                    link.unlink()
            elif link.exists():
                typer.echo(f"Not a symlink, skipping: {link}")
        return

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for src, link in to_install:
        if dry_run:
            typer.echo(f"[dry-run] Would link: {link} -> {src}")
        else:
            if link.exists() or link.is_symlink():
                typer.echo(f"Already exists, skipping: {link}")
            else:
                link.symlink_to(src)
                typer.echo(f"Linked: {link} -> {src}")
