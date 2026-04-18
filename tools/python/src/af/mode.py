"""af mode — activate / deactivate / list behavioral modes.

Behavioral modes are cross-cutting operating postures (token-efficient,
caveman, etc.) implemented as `agentfiles/modes/<name>/MODE.md` files and
re-injected each turn by `hooks/modes.py`.

State lives in `~/.claude/modes/`, one file per active mode. Filename =
mode name, contents = active level (default `on`).

CLI surface:

    af mode list                 catalogue + active marker
    af mode list --active        active only
    af mode on <name> [--level]  activate (default level = first in MODE.md levels list)
    af mode off <name>           deactivate
    af mode status               active only (alias of `list --active`)

See `agentfiles/modes/README.md` for the authoring guide.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import typer

app = typer.Typer(help="Toggle behavioral modes (token-efficient, caveman, ...).")


# ── Paths ─────────────────────────────────────────────────────────────────────

def state_dir() -> Path:
    """Directory holding one file per active mode.

    Override with $AF_MODES_STATE_DIR (used by tests).
    """
    override = os.environ.get("AF_MODES_STATE_DIR")
    if override:
        return Path(override)
    return Path.home() / ".claude" / "modes"


def find_repo_root(start: Path | None = None) -> Path | None:
    """Walk upward looking for a repo with `agentfiles/modes/` or manifest.toml."""
    p = (start or Path.cwd()).resolve()
    for candidate in [p, *p.parents]:
        if (candidate / "agentfiles" / "modes").is_dir():
            return candidate
        if (candidate / "manifest.toml").exists() and (candidate / "agentfiles").is_dir():
            return candidate
    return None


def modes_root(start: Path | None = None) -> Path | None:
    """Return agentfiles/modes/ in the discovered repo, or the vendored copy.

    Override with $AF_MODES_DIR for tests.
    """
    override = os.environ.get("AF_MODES_DIR")
    if override:
        return Path(override)
    root = find_repo_root(start)
    if root is None:
        # Fall back to the installed repo (dev install is editable so this
        # resolves to the checkout).
        here = Path(__file__).resolve()
        for p in [here, *here.parents]:
            if (p / "agentfiles" / "modes").is_dir():
                return p / "agentfiles" / "modes"
        return None
    return root / "agentfiles" / "modes"


# ── Frontmatter parsing ───────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def _split_frontmatter(text: str) -> tuple[str, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return "", text
    return m.group(1), m.group(2)


def _parse_scalar(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def _parse_inline_list(value: str) -> list[str]:
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1]
        if not inner.strip():
            return []
        return [_parse_scalar(x) for x in inner.split(",") if x.strip()]
    return [_parse_scalar(v)] if v else []


@dataclass
class ModeSpec:
    """Parsed MODE.md frontmatter. Body is ignored — it's human doc."""

    name: str
    description: str = ""
    category: str = "communication"
    levels: list[str] = field(default_factory=lambda: ["on"])
    reminder: str = ""
    reminders: dict[str, str] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)
    conflicts_with: list[str] = field(default_factory=list)
    auto_clarity: bool = False

    def default_level(self) -> str:
        return self.levels[0] if self.levels else "on"

    def canonical_level(self, level: str) -> str | None:
        """Resolve user-supplied level (maybe an alias) to a canonical one."""
        lvl = level.strip().lower()
        if lvl in self.levels:
            return lvl
        if lvl in self.aliases:
            canon = self.aliases[lvl]
            if canon in self.levels:
                return canon
        return None

    def reminder_for(self, level: str) -> str:
        if level in self.reminders and self.reminders[level]:
            return self.reminders[level]
        return self.reminder


_CATEGORY_PRIORITY = {
    "rigor": 0,
    "research": 1,
    "communication": 2,
    "planning": 3,
    "novelty": 4,
}


def category_rank(cat: str) -> int:
    return _CATEGORY_PRIORITY.get(cat, 5)


# ── Minimal YAML-ish parser ───────────────────────────────────────────────────

def _parse_frontmatter(fm: str) -> dict:
    """Parse the subset of YAML we actually use in MODE.md.

    Supports:
        key: scalar
        key: [a, b]
        key:
          - a
          - b
        key:
          sub: scalar
        key: >
          folded
          block
    """
    out: dict = {}
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_\-]*\s*:", line):
            i += 1
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.rstrip()
        # Folded block scalar
        if rest.strip() in (">", ">-", "|", "|-"):
            i += 1
            collected = []
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                collected.append(lines[i].strip())
                i += 1
            out[key] = " ".join(x for x in collected if x).strip()
            continue
        # Inline value
        if rest.strip():
            value = rest.strip()
            if value.startswith("[") and value.endswith("]"):
                out[key] = _parse_inline_list(value)
            elif value.lower() in ("true", "false"):
                out[key] = value.lower() == "true"
            else:
                out[key] = _parse_scalar(value)
            i += 1
            continue
        # Block — peek next lines
        i += 1
        block_lines: list[str] = []
        while i < len(lines):
            ln = lines[i]
            if not ln.strip():
                block_lines.append(ln)
                i += 1
                continue
            if not ln.startswith((" ", "\t")):
                break
            block_lines.append(ln)
            i += 1
        # Determine: list (starts with "- ") or mapping (sub-key: val)
        stripped_block = [b for b in block_lines if b.strip()]
        if stripped_block and stripped_block[0].lstrip().startswith("- "):
            items: list[str] = []
            for b in stripped_block:
                s = b.lstrip()
                if s.startswith("- "):
                    items.append(_parse_scalar(s[2:]))
            out[key] = items
        else:
            mapping: dict[str, str] = {}
            for b in stripped_block:
                s = b.strip()
                if ":" not in s:
                    continue
                k, _, v = s.partition(":")
                v = v.strip()
                if v in (">", ">-", "|", "|-"):
                    # collect continuation lines from block_lines at greater indent
                    folded_parts: list[str] = []
                    # find position of this line in block_lines and continue
                    idx = block_lines.index(b)
                    j = idx + 1
                    while j < len(block_lines):
                        ln2 = block_lines[j]
                        if not ln2.strip():
                            j += 1
                            continue
                        # deeper indent than the key
                        base_indent = len(b) - len(b.lstrip())
                        ln_indent = len(ln2) - len(ln2.lstrip())
                        if ln_indent <= base_indent:
                            break
                        folded_parts.append(ln2.strip())
                        j += 1
                    mapping[k.strip()] = " ".join(folded_parts).strip()
                else:
                    mapping[k.strip()] = _parse_scalar(v)
            out[key] = mapping
    return out


def parse_mode(path: Path) -> ModeSpec:
    text = path.read_text()
    fm, _ = _split_frontmatter(text)
    data = _parse_frontmatter(fm)

    name = str(data.get("name") or path.parent.name).strip()
    description = str(data.get("description") or "").strip()
    category = str(data.get("category") or "communication").strip()
    levels = data.get("levels")
    if isinstance(levels, str):
        levels = _parse_inline_list(levels)
    if not isinstance(levels, list) or not levels:
        levels = ["on"]
    reminder = str(data.get("reminder") or "").strip()
    reminders_raw = data.get("reminders")
    reminders: dict[str, str] = {}
    if isinstance(reminders_raw, dict):
        reminders = {str(k): str(v).strip() for k, v in reminders_raw.items()}
    aliases_raw = data.get("aliases")
    aliases: dict[str, str] = {}
    if isinstance(aliases_raw, dict):
        aliases = {str(k): str(v) for k, v in aliases_raw.items()}
    conflicts = data.get("conflicts_with")
    if isinstance(conflicts, str):
        conflicts = _parse_inline_list(conflicts)
    if not isinstance(conflicts, list):
        conflicts = []
    auto_clarity = bool(data.get("auto_clarity", False))
    return ModeSpec(
        name=name,
        description=description,
        category=category,
        levels=[str(x) for x in levels],
        reminder=reminder,
        reminders=reminders,
        aliases=aliases,
        conflicts_with=[str(x) for x in conflicts],
        auto_clarity=auto_clarity,
    )


# ── Mode discovery ────────────────────────────────────────────────────────────

def list_modes(root: Path | None = None) -> list[ModeSpec]:
    base = root or modes_root()
    if base is None or not base.exists():
        return []
    specs: list[ModeSpec] = []
    for mode_dir in sorted(base.iterdir()):
        if not mode_dir.is_dir():
            continue
        md = mode_dir / "MODE.md"
        if not md.exists():
            continue
        try:
            specs.append(parse_mode(md))
        except Exception as e:  # noqa: BLE001 — best-effort catalogue
            typer.echo(f"warn: failed to parse {md}: {e}", err=True)
    return specs


def find_mode(name: str, root: Path | None = None) -> ModeSpec | None:
    for spec in list_modes(root):
        if spec.name == name:
            return spec
    return None


# ── State IO ──────────────────────────────────────────────────────────────────

def active_modes(state: Path | None = None) -> dict[str, str]:
    """Return {mode_name: level} for every active mode."""
    s = state or state_dir()
    if not s.exists():
        return {}
    out: dict[str, str] = {}
    for f in sorted(s.iterdir()):
        if not f.is_file() or f.name.startswith("."):
            continue
        try:
            level = f.read_text().strip() or "on"
        except OSError:
            continue
        out[f.name] = level
    return out


def activate(name: str, level: str, state: Path | None = None) -> None:
    s = state or state_dir()
    s.mkdir(parents=True, exist_ok=True)
    (s / name).write_text(level + "\n")


def deactivate(name: str, state: Path | None = None) -> None:
    s = state or state_dir()
    f = s / name
    if f.exists():
        f.unlink()


# ── CLI ───────────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context):
    """Toggle behavioral modes. With no subcommand, runs `status`."""
    if ctx.invoked_subcommand is None:
        _status()


def _render_mode_line(spec: ModeSpec, active: dict[str, str]) -> str:
    marker = "*" if spec.name in active else " "
    level = active.get(spec.name)
    suffix = f" [{level}]" if level else ""
    levels = f" (levels: {', '.join(spec.levels)})" if spec.levels != ["on"] else ""
    return f"{marker} {spec.name:<20} {spec.category:<14}{levels}{suffix}"


@app.command("list")
def list_cmd(
    active_only: bool = typer.Option(
        False, "--active", help="Show only active modes."
    ),
):
    """List every mode in the catalogue (active marked with `*`)."""
    specs = list_modes()
    active = active_modes()
    if not specs:
        typer.echo("No modes found.", err=True)
        raise typer.Exit(2)
    shown = [s for s in specs if s.name in active] if active_only else specs
    shown.sort(key=lambda s: (category_rank(s.category), s.name))
    if not shown:
        typer.echo("(no active modes)")
        return
    for spec in shown:
        typer.echo(_render_mode_line(spec, active))


@app.command("status")
def status_cmd():
    """Show currently active modes."""
    _status()


def _status() -> None:
    specs = {s.name: s for s in list_modes()}
    active = active_modes()
    if not active:
        typer.echo("(no active modes)")
        return
    for name, level in active.items():
        spec = specs.get(name)
        if spec is None:
            typer.echo(f"* {name:<20} <unknown>     [{level}]")
            continue
        typer.echo(_render_mode_line(spec, active))


@app.command("on")
def on_cmd(
    name: str = typer.Argument(..., help="Mode name (e.g. token-efficient)."),
    level: str | None = typer.Option(
        None, "--level", "-l", help="Level to activate (see mode's `levels:`)."
    ),
):
    """Activate a mode. Defaults to the first level declared in MODE.md."""
    spec = find_mode(name)
    if spec is None:
        typer.echo(f"unknown mode: {name!r}", err=True)
        typer.echo("run `af mode list` to see available modes.", err=True)
        raise typer.Exit(2)

    if level is None:
        resolved = spec.default_level()
    else:
        resolved = spec.canonical_level(level)
        if resolved is None:
            typer.echo(
                f"unknown level {level!r} for mode {name!r}. "
                f"valid: {', '.join(spec.levels)}",
                err=True,
            )
            raise typer.Exit(2)

    # Conflict check against currently-active modes
    active = active_modes()
    for conflict in spec.conflicts_with:
        if conflict in active:
            typer.echo(
                f"refusing: mode {name!r} conflicts with active mode {conflict!r}. "
                f"run `af mode off {conflict}` first.",
                err=True,
            )
            raise typer.Exit(1)

    activate(name, resolved)
    typer.echo(f"mode on: {name} [{resolved}]")


@app.command("off")
def off_cmd(name: str = typer.Argument(..., help="Mode name to deactivate.")):
    """Deactivate a mode."""
    active = active_modes()
    if name not in active:
        typer.echo(f"mode {name!r} is not active.")
        return
    deactivate(name)
    typer.echo(f"mode off: {name}")


# ── Hook integration helper ──────────────────────────────────────────────────

def build_reminder_block() -> str:
    """Assemble the concatenated reminder string for all active modes.

    Ordered by category priority. Empty string if no active modes.
    """
    specs = {s.name: s for s in list_modes()}
    active = active_modes()
    if not active:
        return ""
    entries: list[tuple[int, str, str]] = []
    for name, level in active.items():
        spec = specs.get(name)
        if spec is None:
            continue
        reminder = spec.reminder_for(level)
        if not reminder:
            continue
        entries.append((category_rank(spec.category), name, reminder))
    entries.sort(key=lambda e: (e[0], e[1]))
    return "\n".join(f"Reminder: {r}" for _, _, r in entries)
