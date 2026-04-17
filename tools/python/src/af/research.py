"""af research — scaffold a deep-research session.

Creates an output directory with a pre-built PROMPT.md that instructs Claude
to use the research-agent, docs-agent, web-scraper, sci-hub, and youtube
skills to investigate a topic. Depth controls how aggressive the pull should
be. The CLI does not invoke Claude — it produces the prompt, the human or
Claude Code takes it from there.

Usage:
    af research <topic> [--depth quick|medium|deep] [--out <dir>]
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import typer

_DEPTH_HINTS = {
    "quick": (
        "- Stay at survey depth. Read 3-5 high-signal web sources, skim 1-2 papers.\n"
        "- No YouTube transcripts unless a source is video-only.\n"
        "- Target output: 400-600 word synthesis + source list."
    ),
    "medium": (
        "- Download 5 papers via `sci-hub`, scrape 5-10 web pages via `web-scraper`.\n"
        "- Pull transcripts for any directly-relevant YouTube talks (use `af youtube transcript`).\n"
        "- Target output: 1200-2000 word report with citations + contradiction map."
    ),
    "deep": (
        "- Download 10+ papers via `sci-hub`, scrape 15-25 sources via `web-scraper`.\n"
        "- Transcribe any relevant YouTube talks or channel playlists (`af youtube transcript`).\n"
        "- Run `kb-critic` over the pulled material for contradictions and evidence tiers.\n"
        "- Target output: full report (3000+ words), notes per source in `notes/`, and a wiki-ready summary."
    ),
}


def _slug(topic: str) -> str:
    s = topic.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "untitled"


def _prompt_text(topic: str, depth: str, out_dir: Path) -> str:
    hints = _DEPTH_HINTS[depth]
    return f"""# Research: {topic}

**Depth:** {depth}
**Output directory:** {out_dir}
**Started:** {date.today().isoformat()}

## Task

Produce a well-sourced research brief on the topic above. Route through the
`research` category dispatcher and use these skills in combination:

- `research-agent` — trade-offs, consensus, risks. Start here to frame the question.
- `docs-agent` — exact API / library references if the topic is technical.
- `web-scraper` — structured pulls from sites where data is in HTML or JSON.
- `sci-hub` — academic papers by title or DOI.
- `youtube` — transcripts of relevant talks, lectures, or channel content.
- `note-taker` — write each source up as a dense markdown note.
- `kb-critic` — audit the synthesised view for weak evidence and contradictions (required at `deep`, recommended otherwise).

## Depth-specific plan

{hints}

## Process

1. **Scope** — restate the question in one sentence. List the sub-questions
   you will answer. Note which sub-questions each skill is best placed to hit.
2. **Gather** — dispatch the gathering skills in parallel where possible.
   Save raw pulls into `{out_dir}/sources/` (papers, scraped HTML/markdown,
   transcripts). One file per source.
3. **Note** — use `note-taker` (LLM-optimized mode) to produce one dense
   `.md` per source in `{out_dir}/notes/` with YAML frontmatter and wikilinks.
4. **Synthesise** — write `{out_dir}/REPORT.md` with: TL;DR, key findings,
   open questions, contradictions, sources. Cite every non-trivial claim.
5. **Feed back** — if findings belong in the personal knowledge base, mirror
   the notes into `~/projects/agentfiles/wiki/research/` with consistent
   frontmatter so `knowledge-base` (via `mks`) can index them.

## Deliverables

- `{out_dir}/REPORT.md` — the final synthesis.
- `{out_dir}/sources/` — raw material.
- `{out_dir}/notes/` — one dense markdown note per source.
- (optional at `deep`) `{out_dir}/contradictions.md` from `kb-critic`.

## Guardrails

- Cite every non-trivial claim. No paraphrasing without a source link.
- Prefer primary sources (papers, official docs) over blog summaries.
- If a source is behind a paywall, try `sci-hub` before giving up.
- Flag one-source claims explicitly — they are weak until corroborated.
"""


def run(
    topic: str,
    depth: str = "medium",
    out: Path | None = None,
) -> Path:
    """Scaffold the research directory. Returns the output path."""
    if depth not in _DEPTH_HINTS:
        typer.echo(f"[research] invalid depth: {depth}. Use quick | medium | deep.", err=True)
        raise typer.Exit(1)

    slug = _slug(topic)
    if out is None:
        out = Path.home() / "research" / f"{date.today().isoformat()}-{slug}"

    out = out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "sources").mkdir(exist_ok=True)
    (out / "notes").mkdir(exist_ok=True)

    (out / "PROMPT.md").write_text(_prompt_text(topic, depth, out), encoding="utf-8")
    (out / "TOPIC.md").write_text(topic + "\n", encoding="utf-8")

    return out


def cli(argv: list[str]) -> None:
    """Click-free arg parser invoked directly from main._run().

    We bypass Typer's group-parsing issue (positional arg + add_typer treats
    the sub-app as a group expecting a COMMAND token). Simple argparse works
    perfectly for the three inputs we need.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="af research",
        description="Scaffold a deep-research session for Claude Code. Creates <out>/PROMPT.md and <out>/TOPIC.md; does NOT invoke Claude.",
    )
    parser.add_argument("topic", nargs="+", help="Research topic (free text; quotes optional).")
    parser.add_argument(
        "--depth", "-d", default="medium", choices=sorted(_DEPTH_HINTS.keys()),
        help="Depth of research (default: medium).",
    )
    parser.add_argument(
        "--out", "-o", type=Path, default=None,
        help="Output directory (default: ~/research/<YYYY-MM-DD>-<slug>/).",
    )
    args = parser.parse_args(argv)
    topic = " ".join(args.topic)
    out = run(topic, depth=args.depth, out=args.out)

    try:
        typer.echo(str(out))
        typer.echo("")
        typer.echo("Next steps:")
        typer.echo(f"  cd {out}")
        typer.echo("  # then either paste PROMPT.md into Claude Code,")
        typer.echo("  # or run:  claude < PROMPT.md")
    except BrokenPipeError:
        # Caller (e.g. `af research ... | head -n1`) closed the pipe early. Fine.
        pass
