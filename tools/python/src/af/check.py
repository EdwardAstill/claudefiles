import typer
from pathlib import Path
import re
import sys

app = typer.Typer(invoke_without_command=True)


def find_skills_root(cwd: Path) -> Path | None:
    """Find skills root: check for 'skills/' first, then 'agentfiles/' as fallback."""
    for name in ("skills", "agentfiles"):
        p = cwd / name
        if p.is_dir():
            return p
    return None


def is_leaf_skill(path: Path) -> bool:
    """A leaf skill has SKILL.md and no children with SKILL.md."""
    if not (path / "SKILL.md").exists():
        return False
    return not any(
        child.is_dir() and (child / "SKILL.md").exists()
        for child in path.iterdir()
    )


def get_skill_name(skill_path: Path) -> str:
    """Extract skill name from SKILL.md frontmatter."""
    text = (skill_path / "SKILL.md").read_text()
    m = re.search(r'^name:\s*(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else skill_path.name


@app.callback(invoke_without_command=True)
def main(verbose: bool = typer.Option(False, "--verbose")):
    cwd = Path.cwd()
    root = find_skills_root(cwd)

    if root is None:
        typer.echo("No skills/ or agentfiles/ directory found in current directory.")
        raise typer.Exit(0)

    issues = []

    for category in sorted(root.iterdir()):
        if not category.is_dir():
            continue
        region_file = category / "REGION.md"
        region_text = region_file.read_text() if region_file.exists() else ""

        # Walk recursively for leaf skills in this category
        for skill_path in sorted(category.rglob("*")):
            if not skill_path.is_dir():
                continue
            if not is_leaf_skill(skill_path):
                continue
            name = get_skill_name(skill_path)
            if verbose:
                typer.echo(f"  checking: {name}")
            if f"### {name}" not in region_text:
                issues.append(f"  MISSING in {category.name}/REGION.md: ### {name}")

    if issues:
        typer.echo("af check: REGION.md out of sync:")
        for issue in issues:
            typer.echo(issue)
        raise typer.Exit(1)
    else:
        typer.echo("af check: all leaf skills are in sync with REGION.md files.")
