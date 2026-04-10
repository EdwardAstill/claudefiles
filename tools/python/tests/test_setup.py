from typer.testing import CliRunner
from cf.main import app

runner = CliRunner()


def test_setup_no_skills_dir(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["setup"])
    assert result.exit_code == 0
    assert "No project skills" in result.output or "No skills found" in result.output or "skills" in result.output.lower()


def test_setup_with_skills(git_repo, monkeypatch):
    skills_dir = git_repo / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "git-expert").mkdir()
    (skills_dir / "git-expert" / "SKILL.md").write_text("---\nname: git-expert\n---")
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["setup"])
    assert result.exit_code == 0
    assert "git-expert" in result.output


def test_setup_write_creates_deps(git_repo, monkeypatch):
    skills_dir = git_repo / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "git-expert").mkdir()
    (skills_dir / "git-expert" / "SKILL.md").write_text("---\nname: git-expert\n---")
    monkeypatch.chdir(git_repo)
    runner.invoke(app, ["setup", "--write"])
    assert (git_repo / ".claudefiles" / "deps.md").exists()


def test_setup_write_deps_content(git_repo, monkeypatch):
    skills_dir = git_repo / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "git-expert").mkdir()
    (skills_dir / "git-expert" / "SKILL.md").write_text("---\nname: git-expert\n---")
    monkeypatch.chdir(git_repo)
    runner.invoke(app, ["setup", "--write"])
    content = (git_repo / ".claudefiles" / "deps.md").read_text()
    assert "git-expert" in content


def test_setup_explicit_skills(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["setup", "--skills", "git-expert,docs-agent"])
    assert result.exit_code == 0
    assert "git-expert" in result.output or "docs-agent" in result.output
