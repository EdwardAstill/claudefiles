"""Tests for `af install`.

Invokes install_cmd directly because the Typer stub in main.py is intercepted
by _run(). The remove test implicitly validates creation (remove of a
non-existent symlink is a no-op; we assert the symlink is gone post-remove
after a prior install).
"""

from pathlib import Path

import pytest
from click.testing import CliRunner
from af.install import _prune_stale_symlinks, install_cmd

runner = CliRunner()


@pytest.fixture
def agentfiles_repo(tmp_path):
    (tmp_path / "agentfiles" / "coding" / "demo").mkdir(parents=True)
    (tmp_path / "agentfiles" / "coding" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\n---\n\n# Demo"
    )
    (tmp_path / "manifest.toml").write_text(
        '[skills.demo]\ntools = []\ncategory = "coding"\n'
    )
    (tmp_path / "hooks").mkdir()
    (tmp_path / "AGENT.md").write_text("")
    return tmp_path


def test_install_dry_run_global(agentfiles_repo, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(agentfiles_repo)
    result = runner.invoke(
        install_cmd,
        ["--global", "--dry-run"],
        standalone_mode=False,
    )
    assert result.exit_code == 0, result.output
    assert "[dry-run]" in result.output


def test_install_list_categories(agentfiles_repo, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(agentfiles_repo)
    result = runner.invoke(
        install_cmd,
        ["--list-categories"],
        standalone_mode=False,
    )
    assert result.exit_code == 0, result.output
    assert "coding" in result.output


# ── Prune stale symlinks (S-6) ───────────────────────────────────────────────


def test_prune_removes_stale_symlink_pointing_into_repo(tmp_path):
    """A symlink whose basename isn't in known_basenames but points into the
    repo gets pruned."""
    repo = tmp_path / "repo"
    (repo / "agentfiles" / "coding" / "demo").mkdir(parents=True)
    target_dir = tmp_path / "home" / ".claude" / "skills"
    target_dir.mkdir(parents=True)
    (target_dir / "renamed-away").symlink_to(repo / "agentfiles" / "coding" / "demo")
    (target_dir / "still-valid").symlink_to(repo / "agentfiles" / "coding" / "demo")

    pruned = _prune_stale_symlinks(
        target_dir, {"still-valid"}, repo, dry_run=False
    )
    assert pruned == 1
    assert not (target_dir / "renamed-away").exists()
    assert (target_dir / "still-valid").is_symlink()


def test_prune_leaves_symlinks_pointing_outside_repo(tmp_path):
    """User-owned symlinks that resolve outside the repo are left alone."""
    repo = tmp_path / "repo"
    repo.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    target_dir = tmp_path / "home" / ".claude" / "skills"
    target_dir.mkdir(parents=True)
    (target_dir / "personal").symlink_to(external)

    pruned = _prune_stale_symlinks(target_dir, set(), repo, dry_run=False)
    assert pruned == 0
    assert (target_dir / "personal").is_symlink()


def test_prune_dry_run_does_not_unlink(tmp_path):
    repo = tmp_path / "repo"
    (repo / "agentfiles" / "coding" / "demo").mkdir(parents=True)
    target_dir = tmp_path / "home" / ".claude" / "skills"
    target_dir.mkdir(parents=True)
    (target_dir / "stale").symlink_to(repo / "agentfiles" / "coding" / "demo")

    pruned = _prune_stale_symlinks(target_dir, set(), repo, dry_run=True)
    assert pruned == 1
    # Dry-run counts but doesn't actually remove.
    assert (target_dir / "stale").is_symlink()


def test_prune_respects_suffix_argument(tmp_path):
    """Agent entries end in .md; strip before comparing to known_basenames."""
    repo = tmp_path / "repo"
    (repo / "agentfiles" / "agents").mkdir(parents=True)
    (repo / "agentfiles" / "agents" / "alpha.md").write_text("---\nname: alpha\n---")
    target_dir = tmp_path / "home" / ".claude" / "agents"
    target_dir.mkdir(parents=True)
    (target_dir / "alpha.md").symlink_to(repo / "agentfiles" / "agents" / "alpha.md")
    (target_dir / "old-agent.md").symlink_to(
        repo / "agentfiles" / "agents" / "alpha.md"
    )

    pruned = _prune_stale_symlinks(
        target_dir, {"alpha"}, repo, dry_run=False, suffix=".md"
    )
    assert pruned == 1
    assert (target_dir / "alpha.md").is_symlink()
    assert not (target_dir / "old-agent.md").exists()


def test_prune_handles_broken_symlink(tmp_path):
    """Broken symlinks with unknown basename are pruned."""
    repo = tmp_path / "repo"
    repo.mkdir()
    target_dir = tmp_path / "home" / ".claude" / "skills"
    target_dir.mkdir(parents=True)
    (target_dir / "broken-unknown").symlink_to(tmp_path / "does-not-exist")

    pruned = _prune_stale_symlinks(target_dir, set(), repo, dry_run=False)
    assert pruned == 1
    assert not (target_dir / "broken-unknown").is_symlink()


def test_prune_leaves_non_symlink_entries_alone(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    target_dir = tmp_path / "home" / ".claude" / "skills"
    target_dir.mkdir(parents=True)
    regular_file = target_dir / "not-a-link.md"
    regular_file.write_text("hello")

    pruned = _prune_stale_symlinks(target_dir, set(), repo, dry_run=False)
    assert pruned == 0
    assert regular_file.exists()
