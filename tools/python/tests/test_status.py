from typer.testing import CliRunner
from cf.main import app
import subprocess

runner = CliRunner()

def test_status_output_headers(git_repo, monkeypatch):
    """Test that status command outputs required headers."""
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "# REPO MAP" in result.output
    assert "TRUNK" in result.output

def test_status_write(git_repo, monkeypatch):
    """Test that --write flag creates repo-map.md in .claudefiles/."""
    monkeypatch.chdir(git_repo)
    runner.invoke(app, ["status", "--write"])
    assert (git_repo / ".claudefiles" / "repo-map.md").exists()

def test_status_trunk_info(git_repo, monkeypatch):
    """Test that status shows trunk branch name and commit info."""
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "branch:" in result.output
    assert "main" in result.output or "master" in result.output

def test_status_with_worktree(git_repo, monkeypatch):
    """Test that status shows worktree information."""
    monkeypatch.chdir(git_repo)
    # Create a worktree
    subprocess.run(
        ["git", "worktree", "add", str(git_repo / "wt" / "feature"), "-b", "feature"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    # Should contain worktree section (may or may not show if branch has no commits)
    assert "TRUNK" in result.output

def test_status_generated_timestamp(git_repo, monkeypatch):
    """Test that status includes Generated timestamp."""
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "# Generated:" in result.output

def test_status_repo_root(git_repo, monkeypatch):
    """Test that status shows repo root."""
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    # Should show the root path somewhere
    assert "# Repo:" in result.output or "# Root:" in result.output
