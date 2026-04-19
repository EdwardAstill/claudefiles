import typer
from pathlib import Path
import re

from af import plan_exec

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
    same user intent and dilute routing accuracy (see
    research/knowledge/context-engineering.md on tool-RAG distinguishability).
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


# ---------------------------------------------------------------------------
# `af check plans` — YAML <-> prose drift watchdog
# ---------------------------------------------------------------------------


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_TASK_HEADING_RE = re.compile(r"^###\s+Task\s+(\d+)\s*[:.]", re.MULTILINE)
_SLUG_STRIP_RE = re.compile(r"[^a-z0-9\s-]+")
_SLUG_SPACE_RE = re.compile(r"[\s_]+")


def _slugify(heading: str) -> str:
    """Return a GitHub-style lowercased kebab-case slug of a heading.

    `## Task 3: Step 2` -> `task-3-step-2`. Drops punctuation, collapses
    whitespace, lowercases. Used to match `prose_ref` anchors against the
    actual markdown headings.
    """
    s = heading.lower().strip()
    s = _SLUG_STRIP_RE.sub("", s)
    s = _SLUG_SPACE_RE.sub("-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _prose_anchors(md_text: str) -> set[str]:
    """Extract the set of anchor slugs from every ATX heading in the prose."""
    out: set[str] = set()
    for _hashes, title in _HEADING_RE.findall(md_text):
        out.add(_slugify(title))
    return out


def _prose_task_numbers(md_text: str) -> set[int]:
    """Return the set of Task N numbers found as `### Task N:` headings."""
    return {int(m) for m in _TASK_HEADING_RE.findall(md_text)}


def _collect_prose_refs(plan: plan_exec.Plan) -> list[tuple[str, str]]:
    """Return [(node_id, prose_ref), ...] for every node that sets prose_ref."""
    refs: list[tuple[str, str]] = []
    for n in plan.nodes:
        if n.prose_ref:
            refs.append((n.id, n.prose_ref))
        if isinstance(n, plan_exec.LoopNode):
            for inner in n.body:
                if inner.prose_ref:
                    refs.append((inner.id, inner.prose_ref))
    return refs


def _implement_node_count(plan: plan_exec.Plan) -> int:
    """Count implement-type nodes (top-level plus loop body)."""
    count = 0
    for n in plan.nodes:
        if isinstance(n, plan_exec.ImplementNode):
            count += 1
        if isinstance(n, plan_exec.LoopNode):
            for inner in n.body:
                if isinstance(inner, plan_exec.ImplementNode):
                    count += 1
    return count


def check_plan_pair(yaml_path: Path, md_path: Path) -> list[str]:
    """Return list of drift issues for a single (yaml, md) pair. Empty = clean."""
    issues: list[str] = []

    try:
        plan = plan_exec.load(yaml_path)
    except plan_exec.PlanParseError as e:
        return [f"parse error: {e}"]

    try:
        md_text = md_path.read_text()
    except OSError as e:
        return [f"could not read prose {md_path}: {e}"]

    anchors = _prose_anchors(md_text)

    # (1) Every prose_ref must resolve to an anchor slug in the .md.
    for node_id, ref in _collect_prose_refs(plan):
        if ref not in anchors:
            issues.append(
                f"node '{node_id}' prose_ref '{ref}' does not match any "
                f"heading slug in {md_path.name}"
            )

    # (2) Every `### Task N:` in the prose needs at least one implement node
    # in the YAML. If the YAML has fewer implement nodes than prose tasks, we
    # flag the count mismatch so the author can reconcile.
    prose_tasks = _prose_task_numbers(md_text)
    impl_count = _implement_node_count(plan)
    if len(prose_tasks) > impl_count:
        missing = sorted(prose_tasks)
        issues.append(
            f"prose has {len(prose_tasks)} `### Task N:` heading(s) "
            f"({missing}) but YAML has only {impl_count} implement node(s) — "
            f"extra markdown task(s) unclaimed"
        )

    return issues


@app.command("plans")
def plans_cmd(
    plans_dir: Path = typer.Option(
        Path("docs/plans"),
        "--dir",
        help="Directory containing plan .yaml + .md pairs.",
    ),
):
    """Check YAML plan <-> prose drift.

    For every `.yaml` in `docs/plans/` with a sibling `.md`, verify:
      - Every `prose_ref` anchor resolves to a heading slug in the prose.
      - Every `### Task N:` heading has at least one matching implement node.

    Exit 0 on clean, exit 1 on drift.
    """
    plans_dir = Path(plans_dir)
    if not plans_dir.is_dir():
        typer.echo(f"af check plans: {plans_dir} not found (nothing to check).")
        return

    pairs: list[tuple[Path, Path]] = []
    for yaml_path in sorted(plans_dir.glob("*.yaml")):
        md_path = yaml_path.with_suffix(".md")
        if md_path.exists():
            pairs.append((yaml_path, md_path))

    if not pairs:
        typer.echo(
            f"af check plans: no yaml+md plan pairs in {plans_dir}. Clean."
        )
        return

    total_issues = 0
    for yaml_path, md_path in pairs:
        issues = check_plan_pair(yaml_path, md_path)
        if issues:
            total_issues += len(issues)
            typer.echo(f"{yaml_path.name}:")
            for msg in issues:
                typer.echo(f"  {msg}")

    if total_issues:
        typer.echo(
            f"\naf check plans: {total_issues} drift issue(s) across "
            f"{len(pairs)} pair(s)."
        )
        raise typer.Exit(1)

    typer.echo(
        f"af check plans: {len(pairs)} plan pair(s) clean — no drift."
    )


# ── modes validator ─────────────────────────────────────────────────────────


_MODE_REQUIRED_FIELDS = {"name", "description", "category", "levels", "reminder"}


def _normalize_level(value) -> str:
    """Map YAML-1.1-boolean-aliased level values back to strings."""
    if value is True:
        return "on"
    if value is False:
        return "off"
    return value


def check_mode_file(mode_md: Path) -> list[str]:
    """Validate a single MODE.md file. Return list of issues (empty = clean)."""
    try:
        import yaml
    except ImportError:
        return [f"{mode_md.name}: yaml package missing — cannot validate"]

    text = mode_md.read_text()
    m = re.search(r"^---\s*\n(.*?)\n---", text, flags=re.DOTALL | re.MULTILINE)
    if not m:
        return [f"{mode_md.name}: no YAML frontmatter block"]

    try:
        front = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        return [f"{mode_md.name}: frontmatter YAML parse error — {exc}"]

    if not isinstance(front, dict):
        return [f"{mode_md.name}: frontmatter must be a mapping, got {type(front).__name__}"]

    issues: list[str] = []

    missing = _MODE_REQUIRED_FIELDS - set(front)
    for field in sorted(missing):
        issues.append(f"{mode_md.name}: missing required field '{field}'")

    dir_name = mode_md.parent.name
    name = front.get("name")
    if name and name != dir_name:
        issues.append(
            f"{mode_md.name}: name '{name}' does not match directory '{dir_name}'"
        )

    levels = front.get("levels")
    if levels is not None:
        if not isinstance(levels, list) or not levels:
            issues.append(f"{mode_md.name}: levels must be a non-empty list")
        else:
            # YAML 1.1 parses unquoted on/off/yes/no as booleans. The hook
            # parser (hooks/modes.py) treats them as strings, so accept bools
            # here and normalize for downstream checks.
            levels = [_normalize_level(lvl) for lvl in levels]
            for lvl in levels:
                if not isinstance(lvl, str) or not lvl:
                    issues.append(
                        f"{mode_md.name}: levels contains non-string or empty entry"
                    )

    category = front.get("category")
    if category is not None and (not isinstance(category, str) or not category.strip()):
        issues.append(f"{mode_md.name}: category must be a non-empty string")

    description = front.get("description")
    if description is not None and not (isinstance(description, str) and description.strip()):
        issues.append(f"{mode_md.name}: description must be a non-empty string")

    # Multi-level modes need per-level reminders; single-level modes use `reminder`.
    reminders = front.get("reminders")
    if isinstance(levels, list) and len(levels) > 1:
        if not isinstance(reminders, dict) or not reminders:
            issues.append(
                f"{mode_md.name}: multi-level mode (levels={levels}) needs a "
                f"'reminders' mapping with one entry per level"
            )
        else:
            missing_keys = [
                lvl for lvl in levels if isinstance(lvl, str) and lvl not in reminders
            ]
            for lvl in missing_keys:
                issues.append(
                    f"{mode_md.name}: reminders missing entry for level '{lvl}'"
                )

    reminder = front.get("reminder")
    if reminder is not None and not (isinstance(reminder, str) and reminder.strip()):
        issues.append(f"{mode_md.name}: reminder must be a non-empty string")

    conflicts = front.get("conflicts_with")
    if conflicts is not None and not isinstance(conflicts, list):
        issues.append(f"{mode_md.name}: conflicts_with must be a list")

    return issues


@app.command("modes")
def modes_cmd(
    modes_dir: Path = typer.Option(
        Path("agentfiles/modes"),
        "--dir",
        help="Directory containing mode subdirectories with MODE.md files.",
    ),
):
    """Validate MODE.md frontmatter across all behavioral modes.

    Required fields: name, description, category, levels, reminder.
    Multi-level modes (`levels` has >1 entry) must include a
    `reminders` mapping with one entry per level. `name` must match
    the parent directory.

    Also checks for duplicate mode names across the directory.

    Exit 0 on clean, exit 1 on any issue.
    """
    modes_dir = Path(modes_dir)
    if not modes_dir.is_dir():
        typer.echo(f"af check modes: {modes_dir} not found (nothing to check).")
        return

    mode_files = sorted(modes_dir.glob("*/MODE.md"))
    if not mode_files:
        typer.echo(f"af check modes: no MODE.md files under {modes_dir}. Clean.")
        return

    total_issues = 0
    seen_names: dict[str, Path] = {}

    for mode_md in mode_files:
        issues = check_mode_file(mode_md)
        if issues:
            total_issues += len(issues)
            typer.echo(f"{mode_md.parent.name}:")
            for msg in issues:
                typer.echo(f"  ✗ {msg}")

        try:
            import yaml
            text = mode_md.read_text()
            m = re.search(r"^---\s*\n(.*?)\n---", text, flags=re.DOTALL | re.MULTILINE)
            if m:
                front = yaml.safe_load(m.group(1)) or {}
                name = front.get("name")
                if isinstance(name, str) and name:
                    if name in seen_names:
                        total_issues += 1
                        typer.echo(
                            f"{mode_md.parent.name}:\n  ✗ duplicate mode name "
                            f"'{name}' (also defined at {seen_names[name].parent.name})"
                        )
                    else:
                        seen_names[name] = mode_md
        except Exception:
            pass

    if total_issues:
        typer.echo(
            f"\naf check modes: {total_issues} issue(s) across "
            f"{len(mode_files)} mode file(s)."
        )
        raise typer.Exit(1)

    typer.echo(
        f"af check modes: {len(mode_files)} mode(s) clean — all frontmatter valid."
    )
