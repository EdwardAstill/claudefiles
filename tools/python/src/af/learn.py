"""af learn — extract skill drafts from recent session traces.

Reads ~/.claude/logs/sessions/session-*.jsonl and heuristically surfaces
coherent multi-step tool sequences as skill-draft markdown under
docs/skills-drafts/. 'promote' only prints shell commands — never moves files.
"""

from __future__ import annotations

import json
import os
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
    # Exclude the currently-active session (mid-write, moving target).
    active_sid = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    active_name = f"session-{active_sid}.jsonl" if active_sid else ""
    files = [p for p in SESSION_LOG_DIR.glob("session-*.jsonl") if p.name != active_name]
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


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


_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")
_STOP_TOKENS = {
    "ls", "cat", "cd", "rm", "mv", "cp", "wc", "echo", "grep", "head", "tail",
    # Shell redirection fragments: both fused (2>/dev/null) and split
    # (after whitespace-split: '2', '>', '/dev/null') forms.
    "2>", ">/dev/null", "2>/dev/null", "2>&1", ">&1", ">&2", "&>", "&>/dev/null",
    ">", "<", "|", "&", "2", "1", "dev", "null",
}
# Generic stem names that leak directory context rather than topic content.
_GENERIC_STEMS = {
    "skill", "readme", "index", "__init__", "init", "main", "agents",
    "region", "manifest", "pyproject", "setup", "conftest", "test",
    "notes", "log", "config", "makefile",
}
# Path-fragment tokens we never want in a slug (user-specific / filesystem noise).
_PATH_NOISE = {
    "home", "eastill", "projects", "agentfiles", "usr", "var", "tmp", "opt",
    "src", "tools", "python", "docs", "skills", "drafts", "tests",
    "claude", "logs", "sessions",
}
_SLUG_MAX = 32


def _slug(text: str) -> str:
    # Normalise: lowercase, replace non-alnum with hyphens, strip leading date
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    s = _DATE_PREFIX.sub("", s)
    # Dedupe tokens and drop path-noise fragments
    parts: list[str] = []
    for tok in s.split("-"):
        if not tok or tok in parts or tok in _PATH_NOISE:
            continue
        parts.append(tok)
    # Enforce <=_SLUG_MAX chars without cutting a token mid-word.
    out: list[str] = []
    used = 0
    for tok in parts:
        extra = len(tok) + (1 if out else 0)
        if used + extra > _SLUG_MAX:
            break
        out.append(tok)
        used += extra
    return "-".join(out) or "session-run"


def _clean_stem(file_path: str) -> str:
    """Return a meaningful basename stem for a path, or '' if generic/noise."""
    name = Path(file_path).name
    # Strip common extensions.
    stem = re.sub(r"\.(md|py|sh|txt|toml|yaml|yml|json|rst|ini|cfg)$", "", name, flags=re.IGNORECASE)
    stem = _DATE_PREFIX.sub("", stem)
    low = stem.lower()
    if not stem or low in _GENERIC_STEMS:
        return ""
    return stem


def _path_keywords(file_path: str) -> list[str]:
    """At most 2 meaningful tokens from a path: basename-stem + optional dir basename."""
    stem = _clean_stem(file_path)
    toks: list[str] = []
    if stem:
        toks.append(stem)
    else:
        # Generic filename — substitute parent directory basename as context.
        parent = Path(file_path).parent.name
        if parent and parent.lower() not in _PATH_NOISE:
            toks.append(parent)
    return toks[:2]


def _title(entries: list[dict], idx: list[int]) -> tuple[str, str]:
    kw: list[str] = []
    path_stems: list[str] = []  # remember meaningful stems; if many share a dir, collapse
    path_parents: list[str] = []
    for i in idx[:6]:
        e = entries[i]
        inp = e.get("input", {}) or {}
        if e.get("tool") in BASH:
            for tok in inp.get("command", "").split()[:3]:
                low = tok.lower()
                if tok.startswith("-"):
                    continue
                if low in _STOP_TOKENS:
                    continue
                # Apply the same noise-cleanup used for slugs to the raw title
                # text — stops path fragments ('/home/user/projects/foo') and
                # redirection garbage ('2>/dev/null') leaking into the
                # description field.
                if "/" in tok or tok.startswith((".", "~")):
                    # Treat as path: keep only a meaningful basename stem.
                    stem = _clean_stem(tok)
                    if stem and stem.lower() not in _PATH_NOISE:
                        kw.append(stem)
                    if len([k for k in kw if k]) >= 2:
                        break
                    continue
                if low in _PATH_NOISE:
                    continue
                kw.append(tok)
                if len([k for k in kw if k]) >= 2:
                    break
        elif "file_path" in inp:
            fp = inp["file_path"]
            parent = Path(fp).parent.name
            stem = _clean_stem(fp)
            if stem:
                path_stems.append(stem)
            if parent and parent.lower() not in _PATH_NOISE:
                path_parents.append(parent)

    # Collapse same-directory multi-file edits into the dir basename.
    if path_parents:
        parent_counts = Counter(path_parents)
        dominant_parent, dom_count = parent_counts.most_common(1)[0]
        if dom_count >= 2:
            kw.append(dominant_parent)
            # keep at most one distinct stem for extra flavor
            for s in path_stems[:1]:
                kw.append(s)
        else:
            # unique parents/stems — use up to 2 meaningful stems, else parents.
            picks = path_stems[:2] if path_stems else path_parents[:2]
            kw.extend(picks)
    else:
        kw.extend(path_stems[:2])

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
def promote(
    draft: str = typer.Argument(..., help="Draft filename under docs/skills-drafts/"),
    category: str = typer.Option("", "--category", "-c", help="Target category (e.g. research, coding/quality). Required unless --dry-run."),
    apply: bool = typer.Option(False, "--apply", help="Actually move + register + commit. Without this flag, prints commands only."),
):
    """Promote a draft into agentfiles/<category>/<slug>/ and register in manifest.

    Without --apply, prints the commands it would run (safe default). With
    --apply, moves the file, adds a [skills.<slug>] stub to manifest.toml, runs
    `af audit` to confirm consistency, and offers a commit message.
    """
    import subprocess
    path = DRAFTS_DIR / draft
    if not path.exists():
        alt = DRAFTS_DIR / f"{draft}.md"
        if alt.exists():
            path = alt
        else:
            typer.echo(f"Draft not found: {path}")
            raise typer.Exit(1)
    slug = path.stem.split("-", 3)[-1]

    if not apply:
        typer.echo(f"# Preview — re-run with --apply --category <cat> to execute")
        cat_seg = category or "<category>"
        target = REPO_ROOT / "agentfiles" / cat_seg / slug / "SKILL.md"
        typer.echo(f"mkdir -p {target.parent}")
        typer.echo(f"mv {path} {target}")
        typer.echo(f"ln -s ../agentfiles/{cat_seg}/{slug} {REPO_ROOT}/skills/{slug}")
        typer.echo(f"# manifest.toml: add [skills.{slug}] / tools = [] / category = \"{cat_seg}\"")
        typer.echo(f"af audit   # confirm consistency")
        typer.echo(f"git add . && git commit -m 'skill: promote {slug} from draft'")
        return

    if not category:
        typer.echo("error: --category is required when --apply", err=True)
        raise typer.Exit(code=2)

    target_dir = REPO_ROOT / "agentfiles" / category / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "SKILL.md"
    if target.exists():
        typer.echo(f"error: target already exists: {target}", err=True)
        raise typer.Exit(code=2)

    # Move the draft, rewriting the `name:` frontmatter field so it matches
    # the target slug — audit check 1 compares manifest keys to SKILL.md name:.
    body = path.read_text()
    body = re.sub(r"^name:\s*.+$", f"name: {slug}", body, count=1, flags=re.MULTILINE)
    target.write_text(body)
    path.unlink()
    typer.echo(f"  [moved] {path.name} → {target.relative_to(REPO_ROOT)} (name: → {slug})")

    # Create registry symlink
    registry = REPO_ROOT / "skills" / slug
    if not registry.exists():
        rel = Path("..") / "agentfiles" / category / slug
        registry.symlink_to(rel)
        typer.echo(f"  [linked] skills/{slug} → {rel}")

    # Append manifest entry (stub)
    manifest = REPO_ROOT / "manifest.toml"
    existing = manifest.read_text()
    if f"[skills.{slug}]" not in existing:
        insertion = f'\n[skills.{slug}]\ntools = []\ncategory = "{category}"\n'
        manifest.write_text(existing + insertion)
        typer.echo(f"  [manifest] appended [skills.{slug}]")

    # Run audit
    r = subprocess.run(["af", "audit"], capture_output=True, text=True)
    last = [ln for ln in r.stdout.splitlines() if "SUMMARY:" in ln]
    typer.echo(f"  [audit] {last[0] if last else 'no summary line'}")

    typer.echo("")
    typer.echo(f"Promoted. Review and commit:")
    typer.echo(f"  git -C {REPO_ROOT} add . && git -C {REPO_ROOT} commit -m 'skill: promote {slug} from draft'")
