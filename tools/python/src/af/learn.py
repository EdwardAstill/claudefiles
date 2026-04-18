"""af learn — extract skill drafts from recent session traces.

Reads ~/.claude/logs/sessions/session-*.jsonl and heuristically surfaces
coherent multi-step tool sequences as skill-draft markdown under
docs/skills-drafts/. 'promote' only prints shell commands — never moves files.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Extract skill-draft candidates from session logs.")

SESSION_LOG_DIR = Path.home() / ".claude" / "logs" / "sessions"
REPO_ROOT = Path(__file__).resolve().parents[4]
DRAFTS_DIR = REPO_ROOT / "docs" / "skills-drafts"
MIN_RUN = 5
RECENT_SESSIONS = 5
EXPLORE = {"Read", "Glob", "Grep"}
BASH = {"Bash", "run_shell_command"}
WRITEY = {"Write", "Edit", "replace"}


def _session_files() -> list[Path]:
    if not SESSION_LOG_DIR.exists():
        return []
    return sorted(SESSION_LOG_DIR.glob("session-*.jsonl"),
                  key=lambda f: f.stat().st_mtime, reverse=True)


def _load(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def _sid(path: Path) -> str:
    m = re.match(r"session-(.+)\.jsonl$", path.name)
    return m.group(1) if m else path.stem


def _success(entries: list[dict]) -> bool:
    for e in reversed(entries[-15:]):
        tool, inp = e.get("tool", ""), e.get("input", {}) or {}
        out = str(e.get("output", ""))
        if tool in BASH:
            cmd = inp.get("command", "")
            if ("git commit" in cmd or "pytest" in cmd or " test" in cmd) \
                    and "error" not in out.lower() and "FAILED" not in out.upper():
                return True
        if tool in WRITEY:
            return True
    return False


def _runs(entries: list[dict]) -> list[list[int]]:
    """Consecutive non-explore tool calls, each run >=MIN_RUN."""
    runs, cur = [], []
    for i, e in enumerate(entries):
        if e.get("tool", "") in EXPLORE:
            if len(cur) >= MIN_RUN:
                runs.append(cur)
            cur = []
            continue
        cur.append(i)
    if len(cur) >= MIN_RUN:
        runs.append(cur)
    return runs


def _step(e: dict) -> str:
    tool, inp = e.get("tool", "?"), e.get("input", {}) or {}
    if tool in BASH:
        return f"Bash: `{inp.get('command', '').splitlines()[0][:110]}`"
    if tool in WRITEY | {"Read"}:
        return f"{tool}: `{inp.get('file_path', '?')}`"
    return f"{tool}({','.join(sorted(inp.keys())[:3])})"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "session-run"


def _title(entries: list[dict], idx: list[int]) -> tuple[str, str]:
    kw: list[str] = []
    for i in idx[:6]:
        e = entries[i]
        inp = e.get("input", {}) or {}
        if e.get("tool") in BASH:
            kw.extend(inp.get("command", "").split()[:2])
        elif "file_path" in inp:
            kw.append(Path(inp["file_path"]).stem)
    text = " ".join(kw)[:80] or "session run"
    return _slug(text), text.strip()


def _patterns(limit: int = RECENT_SESSIONS) -> list[tuple[str, int]]:
    c: Counter[str] = Counter()
    for sf in _session_files()[:limit]:
        for e in _load(sf):
            tool, inp = e.get("tool", ""), e.get("input", {}) or {}
            head = ""
            if tool in BASH:
                head = (inp.get("command", "").split() or [""])[0]
            elif "file_path" in inp:
                head = Path(inp["file_path"]).suffix or Path(inp["file_path"]).name
            if head:
                c[f"{tool} {head}"] += 1
    return [(k, v) for k, v in c.most_common(8) if v >= 3]


def _unique(base: Path) -> Path:
    if not base.exists():
        return base
    n = 2
    while (cand := base.with_name(f"{base.stem}-{n}{base.suffix}")).exists():
        n += 1
    return cand


def _write_draft(sf: Path, entries: list[dict], idx: list[int],
                 patterns: list[tuple[str, int]]) -> Path:
    slug, title = _title(entries, idx)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _unique(DRAFTS_DIR / f"{today}-{slug}.md")
    sid = _sid(sf)
    trigger = (title or "a recurring multi-step workflow")[:160]
    steps = [f"{i + 1}. {_step(entries[j])}" for i, j in enumerate(idx[:12])]

    md = [
        "---", f"name: {slug}", "description: >",
        f"  Draft extracted from session {sid[:8]}. Trigger: {trigger}.",
        "source:", f"  session: {sid}", f"  extracted: {today}", "---",
        f"# {title.title() or slug}", "",
        "## When to use",
        f"- Task looks like: {trigger}",
        f"- Session contained a coherent {len(idx)}-step tool run.",
        "", "## Procedure", *steps,
    ]
    if len(idx) > 12:
        md.append(f"... ({len(idx) - 12} more steps — see source log)")
    md += ["", "## Anti-patterns",
           "- Do not blindly replay commands; reconfirm paths and flags.",
           "- Review draft before promoting — extractor is heuristic.", ""]
    if patterns:
        md.append("## Related cross-session patterns")
        md += [f"- `{k}` seen {v}x across recent sessions" for k, v in patterns]
        md.append("")
    md += ["## Source session", f"- {sf}", ""]
    path.write_text("\n".join(md))
    return path


@app.command()
def propose(session: Optional[str] = typer.Option(None, "--session",
                                                  help="Session ID (default: latest).")):
    """Analyze a session and emit a skill draft under docs/skills-drafts/."""
    if session:
        target = SESSION_LOG_DIR / f"session-{session}.jsonl"
        if not target.exists():
            typer.echo(f"No session file: {target}")
            raise typer.Exit(1)
    else:
        files = _session_files()
        if not files:
            typer.echo("No session logs found.")
            raise typer.Exit(1)
        target = files[0]

    entries = _load(target)
    if not entries:
        typer.echo(f"Session {target.name} is empty.")
        raise typer.Exit(1)

    runs = _runs(entries)
    if not runs and len(entries) >= MIN_RUN:
        runs = [list(range(len(entries)))]
    if not runs:
        typer.echo(f"No coherent runs (>={MIN_RUN} steps) in {target.name}.")
        raise typer.Exit(0)

    longest = max(runs, key=len)
    patterns = _patterns()
    path = _write_draft(target, entries, longest, patterns)

    typer.echo(f"Draft written: {path}")
    typer.echo(f"  session: {_sid(target)}")
    typer.echo(f"  steps captured: {len(longest)} (of {len(entries)} total)")
    typer.echo(f"  success-signal: {'yes' if _success(entries) else 'weak'}")
    if patterns:
        typer.echo(f"  cross-session patterns: {len(patterns)}")


@app.command(name="list")
def list_drafts():
    """List all skill drafts under docs/skills-drafts/."""
    if not DRAFTS_DIR.exists():
        typer.echo(f"(no drafts dir at {DRAFTS_DIR})")
        return
    drafts = sorted(DRAFTS_DIR.glob("*.md"))
    if not drafts:
        typer.echo("(no drafts yet)")
        return
    for d in drafts:
        typer.echo(f"{d.name}\t{d.stat().st_size}B")


@app.command()
def promote(draft: str = typer.Argument(..., help="Draft filename under docs/skills-drafts/")):
    """Print shell commands to move draft into skills/ + register. Does NOT execute."""
    path = DRAFTS_DIR / draft
    if not path.exists():
        alt = DRAFTS_DIR / f"{draft}.md"
        if alt.exists():
            path = alt
        else:
            typer.echo(f"Draft not found: {path}")
            raise typer.Exit(1)
    slug = path.stem.split("-", 3)[-1]
    typer.echo("# Review the draft, then run (manually):")
    typer.echo(f"mkdir -p {REPO_ROOT}/skills/{slug}")
    typer.echo(f"mv {path} {REPO_ROOT}/skills/{slug}/SKILL.md")
    typer.echo("# then register in manifest.toml and commit:")
    typer.echo(f"$EDITOR {REPO_ROOT}/manifest.toml")
    typer.echo(f"git -C {REPO_ROOT} add skills/{slug} manifest.toml && "
               f"git -C {REPO_ROOT} commit -m 'skill: promote {slug} from draft'")
