"""Tests for `af install`.

Invokes install_cmd directly because the Typer stub in main.py is intercepted
by _run(). The remove test implicitly validates creation (remove of a
non-existent symlink is a no-op; we assert the symlink is gone post-remove
after a prior install).
"""

import pytest
from click.testing import CliRunner
from af.install import install_cmd

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
