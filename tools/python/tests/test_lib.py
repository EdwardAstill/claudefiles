import os, subprocess
from pathlib import Path
import pytest
from af.lib import git_root, bus, ensure_bus, bus_exists, gitignore_bus

def test_git_root_returns_repo_root(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    assert git_root() == git_repo

def test_git_root_from_subdir(git_repo, monkeypatch):
    sub = git_repo / "sub"
    sub.mkdir()
    monkeypatch.chdir(sub)
    assert git_root() == git_repo

def test_git_root_outside_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert git_root() == tmp_path

def test_bus_path(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    assert bus() == git_repo / ".agentfiles"

def test_ensure_bus_creates_dir(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    b = ensure_bus()
    assert b.exists()
    assert b == git_repo / ".agentfiles"

def test_bus_exists(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    assert not bus_exists()
    ensure_bus()
    assert bus_exists()

def test_gitignore_bus_adds_entry(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    gitignore_bus()
    assert ".agentfiles/" in (git_repo / ".gitignore").read_text()

def test_gitignore_bus_idempotent(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    gitignore_bus()
    gitignore_bus()
    text = (git_repo / ".gitignore").read_text()
    assert text.count(".agentfiles/") == 1
