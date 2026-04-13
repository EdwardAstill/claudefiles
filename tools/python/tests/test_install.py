from typer.testing import CliRunner
from af.main import app
from pathlib import Path
import pytest

runner = CliRunner()


@pytest.fixture
def agentfiles_repo(tmp_path):
    """Fake agentfiles repo with a skills/ dir."""
    skills = tmp_path / "skills" / "coding"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\nname: coding\n---")
    return tmp_path


def test_install_dry_run_global(agentfiles_repo, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["install", "--global", "--dry-run",
                                  "--source", str(agentfiles_repo)])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output


def test_install_global_creates_symlinks(agentfiles_repo, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    result = runner.invoke(app, ["install", "--global",
                                  "--source", str(agentfiles_repo)])
    assert result.exit_code == 0
    skill_link = tmp_path / ".claude" / "skills" / "coding"
    assert skill_link.exists() or skill_link.is_symlink()


def test_install_remove(agentfiles_repo, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    runner.invoke(app, ["install", "--global", "--source", str(agentfiles_repo)])
    result = runner.invoke(app, ["install", "--global", "--remove",
                                  "--source", str(agentfiles_repo)])
    assert result.exit_code == 0
    assert not (tmp_path / ".claude" / "skills" / "coding").exists()
