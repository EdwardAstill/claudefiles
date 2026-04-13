import pytest
from typer.testing import CliRunner
from pathlib import Path
from af.main import app

runner = CliRunner()


def make_skill(path: Path, name: str):
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}")


def test_check_passes_when_in_sync(tmp_path, monkeypatch):
    suite = tmp_path / "agentfiles"
    cat = suite / "coding"
    make_skill(cat / "git-expert", "git-expert")
    (cat / "REGION.md").write_text("### git-expert\nDoes git things\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "in sync" in result.output


def test_check_fails_when_missing(tmp_path, monkeypatch):
    suite = tmp_path / "agentfiles"
    cat = suite / "coding"
    make_skill(cat / "git-expert", "git-expert")
    (cat / "REGION.md").write_text("# empty\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 1
    assert "git-expert" in result.output
