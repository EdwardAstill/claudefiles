import pytest
from typer.testing import CliRunner
from af.main import app

runner = CliRunner()

def test_context_output_contains_headers(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["context"])
    assert result.exit_code == 0
    assert "# PROJECT CONTEXT" in result.output
    assert "RUNTIME" in result.output
    assert "GIT" in result.output

def test_context_detects_python(git_repo, monkeypatch):
    (git_repo / "pyproject.toml").write_text("[project]\nname = 'test'")
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["context"])
    assert "Python" in result.output

def test_context_write_creates_file(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    runner.invoke(app, ["context", "--write"])
    assert (git_repo / ".agentfiles" / "context.md").exists()
