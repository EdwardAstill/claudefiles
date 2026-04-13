from typer.testing import CliRunner
from af.main import app

runner = CliRunner()

def test_versions_pyproject(git_repo, monkeypatch):
    (git_repo / "pyproject.toml").write_text(
        '[project]\nname="x"\ndependencies=["typer>=0.12","pytest"]'
    )
    (git_repo / "uv.lock").write_text(
        '[[package]]\nname = "typer"\nversion = "0.12.0"\n\n'
        '[[package]]\nname = "pytest"\nversion = "8.0.0"\n'
    )
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["versions"])
    assert result.exit_code == 0
    assert "typer" in result.output
    assert "0.12.0" in result.output

def test_versions_write(git_repo, monkeypatch):
    (git_repo / "pyproject.toml").write_text('[project]\nname="x"')
    monkeypatch.chdir(git_repo)
    runner.invoke(app, ["versions", "--write"])
    assert (git_repo / ".agentfiles" / "versions.md").exists()

def test_routes_finds_express(git_repo, monkeypatch):
    src = git_repo / "src"
    src.mkdir()
    (src / "app.ts").write_text('app.get("/users", handler)\napp.post("/users", handler)')
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["routes"])
    assert result.exit_code == 0
    assert "/users" in result.output

def test_routes_write(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    runner.invoke(app, ["routes", "--write"])
    assert (git_repo / ".agentfiles" / "routes.md").exists()
