from typer.testing import CliRunner
from cf.main import app

runner = CliRunner()

def test_init_creates_bus_and_gitignore(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (git_repo / ".claudefiles").exists()
    assert ".claudefiles/" in (git_repo / ".gitignore").read_text()

def test_init_dry_run(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["init", "--dry-run"])
    assert result.exit_code == 0
    assert not (git_repo / ".claudefiles").exists()
    assert "[dry-run]" in result.output
