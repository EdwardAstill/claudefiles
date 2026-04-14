"""af hub — interactive TUI for active Claude Code terminals."""

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import typer

app = typer.Typer(help="Interactive overview of active Claude Code terminals.", invoke_without_command=True)

STATUS_DIR = Path.home() / ".claude" / "terminal-status"
STALE_SECONDS = 60 * 60  # 1 hour


# ── helpers ──────────────────────────────────────────────────────────────────

def _age_secs(ts: str) -> float:
    try:
        dt = datetime.fromisoformat(ts)
        return (datetime.now(timezone.utc) - dt).total_seconds()
    except (ValueError, TypeError):
        return float("inf")


def _age_label(ts: str) -> str:
    secs = int(_age_secs(ts))
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m"
    return f"{secs // 3600}h"


def _load_sessions() -> list[dict]:
    if not STATUS_DIR.exists():
        return []
    sessions = []
    for f in sorted(STATUS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text())
            data["_file"] = str(f)
            sessions.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return sessions


def _focus_pane(pane_id: str) -> bool:
    """Focus a WezTerm pane by ID. Returns True on success."""
    if not pane_id:
        return False
    # Look up the tab containing this pane so we can switch to it first
    result = subprocess.run(
        ["wezterm", "cli", "list", "--format", "json"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        try:
            panes = json.loads(result.stdout)
            for p in panes:
                if str(p.get("pane_id")) == str(pane_id):
                    tab_id = p.get("tab_id")
                    if tab_id is not None:
                        subprocess.run(
                            ["wezterm", "cli", "activate-tab", "--tab-id", str(tab_id)],
                            capture_output=True,
                        )
                    break
        except (json.JSONDecodeError, KeyError):
            pass
    r = subprocess.run(
        ["wezterm", "cli", "activate-pane", "--pane-id", str(pane_id)],
        capture_output=True,
    )
    return r.returncode == 0


# ── Textual TUI ───────────────────────────────────────────────────────────────

def _run_tui() -> None:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.widgets import DataTable, Footer, Header, Label
    from textual.reactive import reactive

    STATE_ICONS = {
        "idle":           ("✓", "green"),
        "needs_approval": ("!", "red"),
        "waiting_input":  ("?", "yellow"),
        "working":        ("…", "cyan"),
    }

    class HubApp(App):
        CSS = """
        Screen {
            background: $surface;
        }
        Header {
            background: $primary;
        }
        DataTable {
            height: 1fr;
        }
        DataTable > .datatable--header {
            text-style: bold;
        }
        #empty-msg {
            content-align: center middle;
            height: 1fr;
            color: $text-muted;
        }
        """

        BINDINGS = [
            Binding("q", "quit", "Quit"),
            Binding("r", "refresh", "Refresh"),
            Binding("f", "focus_pane", "Focus pane"),
            Binding("d", "dismiss_session", "Dismiss"),
        ]

        TITLE = "Claude Hub"
        SUB_TITLE = "Active terminals"

        _sessions: reactive[list[dict]] = reactive([], recompose=False)

        def compose(self) -> ComposeResult:
            yield Header()
            yield DataTable(id="sessions-table", cursor_type="row", zebra_stripes=True)
            yield Footer()

        def on_mount(self) -> None:
            table = self.query_one(DataTable)
            table.add_columns("", "State", "Session", "Age", "Working Directory", "Detail")
            self._load()
            self.set_interval(2, self._load)

        def _load(self) -> None:
            sessions = _load_sessions()
            table = self.query_one(DataTable)

            # Remember cursor position
            try:
                cursor_row = table.cursor_row
            except Exception:
                cursor_row = 0

            table.clear()

            if not sessions:
                self.sub_title = "No active sessions"
                return

            self.sub_title = f"{len(sessions)} session(s)"

            for s in sessions:
                state = s.get("state", "unknown")
                icon, color = STATE_ICONS.get(state, ("·", "white"))
                session_id = s.get("session_id", "?")[:12]
                age = _age_label(s.get("ts", ""))
                cwd = s.get("cwd", "—")
                stale = _age_secs(s.get("ts", "")) > STALE_SECONDS

                detail = ""
                if state == "needs_approval":
                    detail = f"tool: {s.get('tool', '?')}"

                from rich.text import Text

                icon_cell = Text(icon, style=f"bold {color}")
                state_cell = Text(state, style=f"{color}{'  dim' if stale else ''}")
                age_cell = Text(age, style="dim" if stale else "")
                cwd_cell = Text(cwd, style="dim" if stale else "")

                table.add_row(
                    icon_cell,
                    state_cell,
                    session_id,
                    age_cell,
                    cwd_cell,
                    detail,
                    key=s.get("session_id", ""),
                )

            # Restore cursor if still in range
            if cursor_row < table.row_count:
                table.move_cursor(row=cursor_row)

            self._sessions = sessions

        def _selected_session(self) -> dict | None:
            table = self.query_one(DataTable)
            if not table.row_count:
                return None
            idx = table.cursor_row
            if idx < len(self._sessions):
                return self._sessions[idx]
            return None

        def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
            self.action_focus_pane()

        def action_focus_pane(self) -> None:
            s = self._selected_session()
            if not s:
                return
            pane_id = s.get("wezterm_pane", "")
            if not pane_id:
                self.notify(
                    "No pane ID yet — will populate after next hook event in that terminal",
                    severity="warning",
                    timeout=4,
                )
                return
            ok = _focus_pane(str(pane_id))
            if ok:
                self.notify(f"Switched to pane {pane_id}", timeout=2)
            else:
                self.notify("wezterm cli activate-pane failed", severity="error", timeout=4)

        def action_dismiss_session(self) -> None:
            s = self._selected_session()
            if not s:
                return
            f = Path(s.get("_file", ""))
            if f.exists():
                f.unlink()
                self.notify("Session dismissed", severity="information")
                self._load()

        def action_refresh(self) -> None:
            self._load()

    HubApp().run()


# ── plain fallback ────────────────────────────────────────────────────────────

def _run_plain() -> None:
    sessions = _load_sessions()
    if not sessions:
        typer.echo(f"No active Claude Code sessions. (status dir: {STATUS_DIR})")
        return

    STATE_ICONS = {
        "idle": "✓",
        "needs_approval": "!",
        "waiting_input": "?",
        "working": "…",
    }
    width_cwd = 40
    typer.echo(f"{'':2} {'STATE':<14}  {'SESSION':<12}  {'AGE':>4}  {'CWD'}")
    typer.echo("─" * 74)
    for s in sessions:
        state = s.get("state", "unknown")
        icon = STATE_ICONS.get(state, "·")
        sid = s.get("session_id", "?")[:12]
        age = _age_label(s.get("ts", ""))
        cwd = s.get("cwd", "—")
        if len(cwd) > width_cwd:
            cwd = "…" + cwd[-(width_cwd - 1):]
        extra = f"  [{s.get('tool')}]" if state == "needs_approval" else ""
        typer.echo(f"{icon}  {state:<14}  {sid:<12}  {age:>4}  {cwd}{extra}")


# ── entry point ───────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def hub(
    ctx: typer.Context,
    plain: bool = typer.Option(False, "--plain", help="Plain table output, no TUI."),
    clean: bool = typer.Option(False, "--clean", help="Remove stale session files (>1h)."),
) -> None:
    """Interactive overview of active Claude Code terminals.

    Press Enter to focus the WezTerm pane, d to dismiss, q to quit.
    """
    if ctx.invoked_subcommand is not None:
        return

    if clean:
        removed = 0
        for f in STATUS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                if _age_secs(data.get("ts", "")) > STALE_SECONDS:
                    f.unlink()
                    removed += 1
            except (json.JSONDecodeError, OSError):
                f.unlink()
                removed += 1
        typer.echo(f"Removed {removed} stale session file(s).")
        return

    if plain:
        _run_plain()
        return

    _run_tui()
