"""Shared-fragment include system for agentfiles skills.

Fragments live in `agentfiles/includes/<slug>.md` and carry minimal
frontmatter (`name: <slug>`). Skills reference them via an `includes:`
list in their own frontmatter, e.g.

    ---
    name: python-expert
    includes:
      - python/pyright
      - python/uv
    ---

Two entry points:

- `expand(skill_md_path) -> str` — returns the full SKILL.md body with
  each fragment appended under a `## Shared Conventions` block. This is
  the preprocessor called at skill-invocation time (see the design plan
  in docs/plans/2026-04-18-includes-fragments.md, section 5).
- `af include show <slug>` / `af include list` — CLI surface for humans
  and skills that just want to read a fragment body directly.
"""

from __future__ import annotations

import re
from pathlib import Path

import typer

app = typer.Typer(help="Inspect and expand shared skill fragments.")


# ── Filesystem layout ─────────────────────────────────────────────────────────

def find_repo_root(start: Path | None = None) -> Path | None:
    """Walk upward looking for an `agentfiles/` dir containing `includes/`.

    Falls back to an `agentfiles/` dir alone, then any ancestor containing
    `manifest.toml`.
    """
    p = (start or Path.cwd()).resolve()
    for candidate in [p, *p.parents]:
        if (candidate / "agentfiles" / "includes").is_dir():
            return candidate
        if (candidate / "agentfiles").is_dir() and (candidate / "manifest.toml").exists():
            return candidate
    return None


def includes_root(start: Path | None = None) -> Path | None:
    root = find_repo_root(start)
    if root is None:
        return None
    return root / "agentfiles" / "includes"


# ── Fragment IO ───────────────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_body, rest). Empty frontmatter if not present."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return "", text
    return m.group(1), m.group(2)


def _parse_includes_list(fm: str) -> list[str]:
    """Pull `includes:` YAML-ish list from frontmatter text.

    Supports only the simple case we commit to in the plan:

        includes:
          - python/pyright
          - python/uv

    Returns [] if no `includes:` key is present.
    """
    lines = fm.splitlines()
    out: list[str] = []
    in_block = False
    for line in lines:
        if not in_block:
            if re.match(r"^includes:\s*$", line):
                in_block = True
            continue
        # In block: stop on a new top-level key (non-indented, non-dash).
        if line and not line.startswith((" ", "\t", "-")):
            break
        stripped = line.strip()
        if stripped.startswith("- "):
            out.append(stripped[2:].strip().strip('"').strip("'"))
        elif stripped == "":
            continue
        else:
            # Indented continuation that isn't a dash — stop.
            break
    return out


def fragment_path(slug: str, root: Path | None = None) -> Path:
    base = root or includes_root()
    if base is None:
        raise FileNotFoundError(
            "Could not locate agentfiles/includes/ — run from inside the repo."
        )
    return base / f"{slug}.md"


def read_fragment(slug: str, root: Path | None = None) -> str:
    """Return fragment body with frontmatter stripped."""
    path = fragment_path(slug, root)
    if not path.exists():
        raise FileNotFoundError(f"Unknown include fragment: {slug!r} ({path})")
    text = path.read_text()
    _, body = _split_frontmatter(text)
    return body.lstrip("\n").rstrip() + "\n"


def list_fragments(root: Path | None = None) -> list[str]:
    base = root or includes_root()
    if base is None or not base.exists():
        return []
    return sorted(
        str(p.relative_to(base).with_suffix(""))
        for p in base.rglob("*.md")
    )


# ── Skill expansion ───────────────────────────────────────────────────────────

def expand(skill_md_path: Path, root: Path | None = None) -> str:
    """Return the SKILL.md text with referenced fragments appended.

    Fragments are concatenated under a final `## Shared Conventions` block.
    If the skill has no `includes:` entry the input is returned unchanged.
    """
    text = skill_md_path.read_text()
    fm, body = _split_frontmatter(text)
    slugs = _parse_includes_list(fm)
    if not slugs:
        return text

    parts = [text.rstrip(), "", "## Shared Conventions", ""]
    for slug in slugs:
        fragment = read_fragment(slug, root)
        parts.append(f"<!-- include: {slug} -->")
        parts.append(fragment.rstrip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def missing_includes(skill_md_path: Path, root: Path | None = None) -> list[str]:
    """Return include slugs referenced by the skill but not present on disk."""
    text = skill_md_path.read_text()
    fm, _ = _split_frontmatter(text)
    slugs = _parse_includes_list(fm)
    base = root or includes_root()
    if base is None:
        return slugs
    return [s for s in slugs if not (base / f"{s}.md").exists()]


# ── CLI ───────────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("list")
def list_cmd():
    """List every fragment under agentfiles/includes/."""
    base = includes_root()
    if base is None:
        typer.echo("No agentfiles/includes/ directory found.", err=True)
        raise typer.Exit(2)
    fragments = list_fragments(base)
    if not fragments:
        typer.echo("(no fragments)")
        return
    for slug in fragments:
        typer.echo(slug)


@app.command("show")
def show_cmd(slug: str):
    """Print the body of a fragment (frontmatter stripped)."""
    try:
        typer.echo(read_fragment(slug), nl=False)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(2)


@app.command("expand")
def expand_cmd(skill_md: Path):
    """Expand a SKILL.md — prints it with fragments inlined."""
    if not skill_md.exists():
        typer.echo(f"no such file: {skill_md}", err=True)
        raise typer.Exit(2)
    typer.echo(expand(skill_md), nl=False)


@app.command("check")
def check_cmd(skill_md: Path):
    """Verify every `includes:` entry in a SKILL.md resolves to a fragment."""
    if not skill_md.exists():
        typer.echo(f"no such file: {skill_md}", err=True)
        raise typer.Exit(2)
    missing = missing_includes(skill_md)
    if missing:
        typer.echo("af include check: missing fragments referenced by " + str(skill_md))
        for slug in missing:
            typer.echo(f"  - {slug}")
        raise typer.Exit(1)
    typer.echo(f"af include check: {skill_md} — all includes resolve.")
