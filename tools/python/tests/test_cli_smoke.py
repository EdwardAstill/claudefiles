"""Smoke tests for the `af` CLI subcommands.

Confirms that each subcommand's Click/Typer wiring loads and returns a
non-crashing exit code on basic read-only invocations. These are not
behavior tests — they catch import errors, broken Typer registration,
and obvious regressions in top-level command plumbing.

Commands that need real FS / git context run from the agentfiles repo
root (resolved from this test file's location). Commands that need
network are marked with `pytest.mark.network` and skipped unless
`AF_RUN_NETWORK_TESTS=1` is set.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from click.testing import CliRunner
from typer.main import get_command

from af.agent_knowledge import app as ak_app
from af.archetype import app as archetype_app
from af.audit import app as audit_app
from af.caveman import app as caveman_app
from af.context import app as context_app
from af.log import app as log_app
from af.skill_usage import app as skill_usage_app
from af.status import app as status_app
from af.terminal import app as terminal_app
from af.tree import app as tree_app
from af.versions import app as versions_app
from af.webscraper import app as webscraper_app
from af.youtube import app as youtube_app

# tests/test_cli_smoke.py → tools/python/tests → tools/python → tools → agentfiles
REPO = Path(__file__).parent.parent.parent.parent

runner = CliRunner()

_NETWORK = pytest.mark.skipif(
    os.environ.get("AF_RUN_NETWORK_TESTS") != "1",
    reason="Network-dependent; set AF_RUN_NETWORK_TESTS=1 to enable.",
)


# ── context / status ─────────────────────────────────────────────────────────

def test_context_default(monkeypatch):
    monkeypatch.chdir(REPO)
    result = runner.invoke(get_command(context_app), [])
    assert result.exit_code == 0, result.output
    assert "PROJECT CONTEXT" in result.output


def test_context_help():
    result = runner.invoke(get_command(context_app), ["--help"])
    assert result.exit_code == 0, result.output


def test_status_default(monkeypatch):
    monkeypatch.chdir(REPO)
    result = runner.invoke(get_command(status_app), [])
    assert result.exit_code == 0, result.output


# ── agent knowledge (ak) ─────────────────────────────────────────────────────

def test_ak_list(monkeypatch):
    monkeypatch.chdir(REPO)
    result = runner.invoke(get_command(ak_app), ["list"])
    assert result.exit_code == 0, result.output
    # At least one known page should appear.
    assert "context-engineering" in result.output


def test_ak_show_known_page(monkeypatch):
    monkeypatch.chdir(REPO)
    result = runner.invoke(get_command(ak_app), ["show", "context-engineering"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() != ""


def test_ak_help():
    result = runner.invoke(get_command(ak_app), ["--help"])
    assert result.exit_code == 0, result.output


# ── archetype ────────────────────────────────────────────────────────────────

def test_archetype_list(monkeypatch):
    monkeypatch.chdir(REPO)
    result = runner.invoke(get_command(archetype_app), ["list"])
    assert result.exit_code == 0, result.output


def test_archetype_match(monkeypatch):
    monkeypatch.chdir(REPO)
    result = runner.invoke(
        get_command(archetype_app), ["match", "build a new feature"]
    )
    assert result.exit_code == 0, result.output


# ── audit ────────────────────────────────────────────────────────────────────

def test_audit_runs(monkeypatch):
    """Audit may report issues (exit 1) but must not crash."""
    monkeypatch.chdir(REPO)
    result = runner.invoke(get_command(audit_app), [])
    assert result.exit_code in (0, 1), (
        f"audit crashed (exit {result.exit_code}): {result.output}"
    )


# ── skill-usage ──────────────────────────────────────────────────────────────

def test_skill_usage_summary(monkeypatch):
    """Reads ~/.claude/logs/agentfiles.jsonl; exit 0 if present, 2 if absent."""
    monkeypatch.chdir(REPO)
    result = runner.invoke(
        get_command(skill_usage_app), ["summary", "--days", "1"]
    )
    assert result.exit_code in (0, 2), result.output


def test_skill_usage_help():
    result = runner.invoke(get_command(skill_usage_app), ["--help"])
    assert result.exit_code == 0, result.output


# ── tree ─────────────────────────────────────────────────────────────────────

def test_tree_help():
    result = runner.invoke(get_command(tree_app), ["--help"])
    assert result.exit_code == 0, result.output


def test_tree_shallow(monkeypatch, tmp_path):
    """Run tree in an empty tmp dir so output is small and safe."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(get_command(tree_app), ["--depth", "1"])
    assert result.exit_code == 0, result.output


# ── --help coverage for more subcommands ─────────────────────────────────────

def test_versions_help():
    result = runner.invoke(get_command(versions_app), ["--help"])
    assert result.exit_code == 0, result.output


def test_log_help():
    result = runner.invoke(get_command(log_app), ["--help"])
    assert result.exit_code == 0, result.output


def test_caveman_help():
    result = runner.invoke(get_command(caveman_app), ["--help"])
    assert result.exit_code == 0, result.output


def test_terminal_help():
    result = runner.invoke(get_command(terminal_app), ["--help"])
    assert result.exit_code == 0, result.output


def test_webscraper_help():
    result = runner.invoke(get_command(webscraper_app), ["--help"])
    assert result.exit_code == 0, result.output


def test_youtube_help():
    result = runner.invoke(get_command(youtube_app), ["--help"])
    assert result.exit_code == 0, result.output


# ── network-gated ────────────────────────────────────────────────────────────

@_NETWORK
def test_youtube_search_network():
    result = runner.invoke(
        get_command(youtube_app),
        ["search", "test query", "--limit", "1"],
    )
    assert result.exit_code == 0, result.output
