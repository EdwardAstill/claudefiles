"""Smoke tests for `af mode` and the generic modes hook.

Covers:
  - CLI wiring (`af mode list` is registered).
  - `af mode on/off/status` round-trips.
  - Multiple active modes concatenate reminders in category order.
  - Unknown modes / levels error cleanly.
  - Backwards-compat: `af caveman on full` writes to the new state dir.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from af import mode as mode_mod
from af.main import app

runner = CliRunner()


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _write_mode(root: Path, name: str, body: str) -> None:
    (root / name).mkdir(parents=True, exist_ok=True)
    (root / name / "MODE.md").write_text(body)


@pytest.fixture
def modes_env(tmp_path, monkeypatch):
    """Point `af mode` at a tmp modes dir + tmp state dir."""
    modes_dir = tmp_path / "modes"
    state_dir = tmp_path / "state"
    modes_dir.mkdir()

    _write_mode(
        modes_dir,
        "token-efficient",
        textwrap.dedent("""\
            ---
            name: token-efficient
            category: communication
            reminder: >
              token-efficient: skip preamble and postamble.
            ---

            body
        """),
    )
    _write_mode(
        modes_dir,
        "caveman",
        textwrap.dedent("""\
            ---
            name: caveman
            category: communication
            levels: [lite, full, actual-caveman]
            reminder: >
              caveman-full default reminder.
            reminders:
              lite: >
                caveman-lite: drop filler.
              full: >
                caveman-full: drop filler and articles.
              actual-caveman: >
                actual-caveman: grunt style.
            aliases:
              actual: actual-caveman
              cave: actual-caveman
            ---

            body
        """),
    )
    _write_mode(
        modes_dir,
        "verify-first",
        textwrap.dedent("""\
            ---
            name: verify-first
            category: rigor
            reminder: >
              verify-first: run the test and quote output.
            conflicts_with: []
            ---
        """),
    )

    monkeypatch.setenv("AF_MODES_DIR", str(modes_dir))
    monkeypatch.setenv("AF_MODES_STATE_DIR", str(state_dir))
    return tmp_path, modes_dir, state_dir


# ── Direct function tests ────────────────────────────────────────────────────

def test_list_modes_discovers_all(modes_env):
    specs = mode_mod.list_modes()
    names = {s.name for s in specs}
    assert names == {"token-efficient", "caveman", "verify-first"}


def test_parse_mode_pulls_levels_and_reminders(modes_env):
    spec = mode_mod.find_mode("caveman")
    assert spec is not None
    assert spec.levels == ["lite", "full", "actual-caveman"]
    assert spec.reminder_for("lite").startswith("caveman-lite")
    assert spec.reminder_for("full").startswith("caveman-full")
    # Alias resolution
    assert spec.canonical_level("actual") == "actual-caveman"
    assert spec.canonical_level("cave") == "actual-caveman"
    assert spec.canonical_level("bogus") is None


def test_activate_and_deactivate_round_trip(modes_env):
    _, _, state = modes_env
    mode_mod.activate("token-efficient", "on")
    assert mode_mod.active_modes() == {"token-efficient": "on"}
    mode_mod.deactivate("token-efficient")
    assert mode_mod.active_modes() == {}


# ── CLI smoke tests (match test_install / test_includes style) ──────────────

def test_cli_list_shows_catalogue(modes_env):
    result = runner.invoke(app, ["mode", "list"])
    assert result.exit_code == 0, result.output
    assert "token-efficient" in result.output
    assert "caveman" in result.output


def test_cli_on_and_status(modes_env):
    result = runner.invoke(app, ["mode", "on", "token-efficient"])
    assert result.exit_code == 0, result.output
    assert "mode on: token-efficient" in result.output

    result = runner.invoke(app, ["mode", "status"])
    assert result.exit_code == 0, result.output
    assert "token-efficient" in result.output


def test_cli_off(modes_env):
    runner.invoke(app, ["mode", "on", "token-efficient"])
    result = runner.invoke(app, ["mode", "off", "token-efficient"])
    assert result.exit_code == 0, result.output
    assert "mode off: token-efficient" in result.output
    status = runner.invoke(app, ["mode", "status"])
    assert "no active modes" in status.output


def test_cli_on_unknown_mode_errors(modes_env):
    result = runner.invoke(app, ["mode", "on", "does-not-exist"])
    assert result.exit_code == 2
    assert "unknown mode" in result.output


def test_cli_on_caveman_with_level(modes_env):
    result = runner.invoke(app, ["mode", "on", "caveman", "--level", "lite"])
    assert result.exit_code == 0, result.output
    assert "[lite]" in result.output


def test_cli_on_invalid_level_errors(modes_env):
    result = runner.invoke(app, ["mode", "on", "caveman", "--level", "bogus"])
    assert result.exit_code == 2
    assert "unknown level" in result.output


def test_cli_on_refuses_conflict(modes_env):
    _, modes_dir, _ = modes_env
    _write_mode(
        modes_dir,
        "rival",
        textwrap.dedent("""\
            ---
            name: rival
            category: communication
            reminder: rival reminder
            conflicts_with: [caveman]
            ---
        """),
    )
    runner.invoke(app, ["mode", "on", "caveman", "--level", "full"])
    result = runner.invoke(app, ["mode", "on", "rival"])
    assert result.exit_code == 1
    assert "conflicts with" in result.output


# ── Reminder assembly (priority order) ───────────────────────────────────────

def test_reminder_block_orders_by_category(modes_env):
    mode_mod.activate("token-efficient", "on")          # communication (rank 2)
    mode_mod.activate("verify-first", "on")             # rigor (rank 0)
    block = mode_mod.build_reminder_block()
    # rigor comes first
    rigor_idx = block.index("verify-first")
    comm_idx = block.index("token-efficient")
    assert rigor_idx < comm_idx


# ── Backwards-compat: `af caveman` still works ───────────────────────────────

def test_caveman_alias_writes_new_state(modes_env):
    result = runner.invoke(app, ["caveman", "on", "full"])
    assert result.exit_code == 0, result.output
    assert "caveman mode: ON (full)" in result.output
    assert mode_mod.active_modes() == {"caveman": "full"}

    result = runner.invoke(app, ["caveman", "off"])
    assert result.exit_code == 0, result.output
    assert mode_mod.active_modes() == {}


# ── Hook integration ─────────────────────────────────────────────────────────

HOOK = Path(__file__).resolve().parents[3] / "hooks" / "modes.py"


def test_hook_emits_additional_context_for_active_mode(modes_env):
    """Fire the hook with active modes and assert the payload shape."""
    _, modes_dir, state_dir = modes_env
    mode_mod.activate("token-efficient", "on")
    env = {
        "AF_MODES_DIR": str(modes_dir),
        "AF_MODES_STATE_DIR": str(state_dir),
        "PATH": "/usr/bin:/bin",
        "HOME": str(state_dir.parent),
    }
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="{}",
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip(), "hook emitted no payload"
    payload = json.loads(result.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "token-efficient" in ctx


def test_hook_silent_when_no_active_modes(modes_env):
    _, modes_dir, state_dir = modes_env
    # Ensure state dir exists but is empty.
    state_dir.mkdir(exist_ok=True)
    env = {
        "AF_MODES_DIR": str(modes_dir),
        "AF_MODES_STATE_DIR": str(state_dir),
        "PATH": "/usr/bin:/bin",
        "HOME": str(state_dir.parent),
    }
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="{}",
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", (
        f"hook should emit nothing when no modes active, got: {result.stdout!r}"
    )
