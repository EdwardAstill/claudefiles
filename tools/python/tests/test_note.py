from typer.testing import CliRunner
from af.main import app

runner = CliRunner()

def test_note_appends_message(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["note", "hello world"])
    assert result.exit_code == 0
    notes = (git_repo / ".agentfiles" / "notes.md").read_text()
    assert "hello world" in notes

def test_note_read_empty(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["note", "--read"])
    assert result.exit_code == 0
    assert "no notes" in result.output.lower()

def test_note_read_after_write(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    runner.invoke(app, ["note", "my note"])
    result = runner.invoke(app, ["note", "--read"])
    assert "my note" in result.output

def test_note_agent_tag(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    runner.invoke(app, ["note", "--agent", "research", "finding"])
    notes = (git_repo / ".agentfiles" / "notes.md").read_text()
    assert "[research]" in notes

def test_read_dumps_all(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    (git_repo / ".agentfiles").mkdir()
    (git_repo / ".agentfiles" / "context.md").write_text("ctx content")
    result = runner.invoke(app, ["read"])
    assert "ctx content" in result.output

def test_read_single_file(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    (git_repo / ".agentfiles").mkdir()
    (git_repo / ".agentfiles" / "notes.md").write_text("notes content")
    result = runner.invoke(app, ["read", "notes"])
    assert "notes content" in result.output
