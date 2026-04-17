import typer
from pathlib import Path
import re

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


def get_skill_description(skill_path: Path) -> str:
    """Extract the description field from SKILL.md frontmatter."""
    text = (skill_path / "SKILL.md").read_text()
    fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not fm_match:
        return ""
    fm = fm_match.group(1)
    m = re.search(
        r"^description:\s*(?:>[-+]?)?\s*\n((?:[ \t]+.*\n)+)|^description:\s*(.+)$",
        fm,
        re.MULTILINE,
    )
    if not m:
        return ""
    if m.group(1):
        return " ".join(line.strip() for line in m.group(1).splitlines())
    return m.group(2).strip()


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "to", "of", "in", "on", "at", "for",
    "with", "by", "from", "as", "is", "are", "was", "be", "this", "that", "it",
    "use", "used", "using", "when", "where", "what", "which", "who", "how",
    "user", "users", "skill", "task", "code", "also",
}


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower())
            if t not in _STOPWORDS and len(t) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, verbose: bool = typer.Option(False, "--verbose")):
    if ctx.invoked_subcommand is not None:
        return
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


@app.command("distinct")
def distinct_cmd(
    threshold: float = typer.Option(
        0.35, "--threshold", "-t",
        help="Flag pairs whose description Jaccard similarity is at or above this.",
    ),
    top: int = typer.Option(
        15, "--top", "-n",
        help="Show at most this many pairs (highest similarity first).",
    ),
):
    """Score skill-description distinctiveness — similar pairs confuse routing.

    Computes Jaccard similarity between every pair of skill descriptions. Pairs
    at or above the threshold are worth reviewing: they likely compete for the
    same user intent and dilute routing accuracy (see wiki/research/context-
    engineering.md on tool-RAG distinguishability).
    """
    cwd = Path.cwd()
    root = find_skills_root(cwd)
    if root is None:
        typer.echo("No skills/ or agentfiles/ directory found.", err=True)
        raise typer.Exit(2)

    skills: list[tuple[str, set[str], str]] = []
    for skill_path in root.rglob("*"):
        if not skill_path.is_dir() or not is_leaf_skill(skill_path):
            continue
        name = get_skill_name(skill_path)
        desc = get_skill_description(skill_path)
        if not desc:
            continue
        skills.append((name, _tokens(desc), desc))

    pairs: list[tuple[float, str, str]] = []
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            score = _jaccard(skills[i][1], skills[j][1])
            if score >= threshold:
                pairs.append((score, skills[i][0], skills[j][0]))
    pairs.sort(key=lambda x: x[0], reverse=True)

    if not pairs:
        typer.echo(
            f"af check distinct: no pairs ≥ {threshold:.2f} across "
            f"{len(skills)} skills. Routing quality looks healthy."
        )
        return

    typer.echo(
        f"af check distinct: {len(pairs)} pair(s) above threshold "
        f"{threshold:.2f} (of {len(skills)} skills). Showing top {min(top, len(pairs))}:"
    )
    for score, a, b in pairs[:top]:
        typer.echo(f"  {score:.2f}  {a}  <->  {b}")
    typer.echo(
        "\nReview: tighten the descriptions so the trigger conditions don't overlap, "
        "or merge skills that truly cover the same ground."
    )
