import json
from typer.testing import CliRunner
from af.main import app

runner = CliRunner()


def test_no_evals_creates_template(git_repo, monkeypatch):
    """When no evals.json exists, create a template."""
    monkeypatch.chdir(git_repo)
    (git_repo / "tests").mkdir()
    result = runner.invoke(app, ["test-skill", "dsa-expert"])
    assert result.exit_code == 0
    template = git_repo / "tests" / "dsa-expert" / "evals.json"
    assert template.exists()
    data = json.loads(template.read_text())
    assert data["skill_name"] == "dsa-expert"
    assert data["version"] == 1
    assert len(data["evals"]) == 0
    assert "template" in result.output.lower() or "created" in result.output.lower()


def test_existing_evals_creates_workspace(git_repo, monkeypatch):
    """When evals.json exists, create iteration-N workspace."""
    monkeypatch.chdir(git_repo)
    skill_dir = git_repo / "tests" / "dsa-expert"
    skill_dir.mkdir(parents=True)
    evals = {
        "version": 1,
        "skill_name": "dsa-expert",
        "skill_path": "agentfiles/coding/dsa/SKILL.md",
        "evals": [
            {"id": 0, "name": "test-eval", "prompt": "test", "reference_answer": "answer"}
        ]
    }
    (skill_dir / "evals.json").write_text(json.dumps(evals))
    result = runner.invoke(app, ["test-skill", "dsa-expert"])
    assert result.exit_code == 0
    assert (skill_dir / "iteration-1").is_dir()
    assert "iteration-1" in result.output


def test_increments_iteration(git_repo, monkeypatch):
    """When iteration-1 exists, create iteration-2."""
    monkeypatch.chdir(git_repo)
    skill_dir = git_repo / "tests" / "dsa-expert"
    skill_dir.mkdir(parents=True)
    (skill_dir / "iteration-1").mkdir()
    evals = {
        "version": 1,
        "skill_name": "dsa-expert",
        "skill_path": "agentfiles/coding/dsa/SKILL.md",
        "evals": [{"id": 0, "name": "test-eval", "prompt": "test", "reference_answer": "answer"}]
    }
    (skill_dir / "evals.json").write_text(json.dumps(evals))
    result = runner.invoke(app, ["test-skill", "dsa-expert"])
    assert result.exit_code == 0
    assert (skill_dir / "iteration-2").is_dir()
    assert "iteration-2" in result.output


def test_empty_evals_warns(git_repo, monkeypatch):
    """When evals.json exists but has no evals, warn the user."""
    monkeypatch.chdir(git_repo)
    skill_dir = git_repo / "tests" / "dsa-expert"
    skill_dir.mkdir(parents=True)
    evals = {
        "version": 1,
        "skill_name": "dsa-expert",
        "skill_path": "agentfiles/coding/dsa/SKILL.md",
        "evals": []
    }
    (skill_dir / "evals.json").write_text(json.dumps(evals))
    result = runner.invoke(app, ["test-skill", "dsa-expert"])
    assert result.exit_code == 0
    assert "no evals" in result.output.lower() or "empty" in result.output.lower()


def test_no_tests_dir_creates_it(git_repo, monkeypatch):
    """When tests/ doesn't exist at all, create it."""
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["test-skill", "my-skill"])
    assert result.exit_code == 0
    assert (git_repo / "tests" / "my-skill" / "evals.json").exists()
