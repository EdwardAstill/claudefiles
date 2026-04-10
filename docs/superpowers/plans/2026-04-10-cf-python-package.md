# cf Python Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `cf` Python Typer package that ports all existing bash scripts to `cf <subcommand>` form, adds stubs for `cf github` and `cf browser`, and installs globally via `uv tool install -e`.

**Architecture:** Single Typer app in `tools/python/src/cf/`, one module per subcommand, shared utilities in `lib.py`. Tests use `typer.testing.CliRunner` with temp git repos as fixtures.

**Tech Stack:** Python 3.11+, Typer, pytest, uv

---

## File Map

**Create:**
- `tools/python/pyproject.toml` — package metadata, entrypoint, dependencies
- `tools/python/src/cf/__init__.py` — empty
- `tools/python/src/cf/main.py` — root Typer app, registers all sub-apps
- `tools/python/src/cf/lib.py` — shared: `git_root()`, `bus()`, `ensure_bus()`, `bus_exists()`, `gitignore_bus()`
- `tools/python/src/cf/context.py` — `cf context [--write]`
- `tools/python/src/cf/status.py` — `cf status [--write]`
- `tools/python/src/cf/versions.py` — `cf versions [--write]`
- `tools/python/src/cf/routes.py` — `cf routes [--write]`
- `tools/python/src/cf/note.py` — `cf note <message> [--agent] [--read] [--clear]`
- `tools/python/src/cf/read.py` — `cf read [file]`
- `tools/python/src/cf/init.py` — `cf init [--dry-run]`
- `tools/python/src/cf/worktree.py` — `cf worktree <branch> [base]`
- `tools/python/src/cf/agents.py` — `cf agents [--global] [--project] [--tree] [--available] [--mcp]`
- `tools/python/src/cf/check.py` — `cf check [--verbose]`
- `tools/python/src/cf/setup.py` — `cf setup [--write]`
- `tools/python/src/cf/github.py` — `cf github` stub
- `tools/python/src/cf/browser.py` — `cf browser` stub
- `tools/python/src/cf/install.py` — `cf install [--global] [--local] [--skill] [--category] [--from] [--dry-run] [--remove]`
- `tools/python/src/cf/tools_cmd.py` — `cf tools [--json]`
- `tools/python/src/cf/data/tools.json` — unified tool registry (bundled as package data; single source of truth)
- `tools/python/tests/conftest.py` — shared fixtures
- `tools/python/tests/test_lib.py`
- `tools/python/tests/test_context.py`
- `tools/python/tests/test_status.py`
- `tools/python/tests/test_note.py`
- `tools/python/tests/test_versions.py`
- `tools/python/tests/test_check.py`
- `tools/python/tests/test_setup.py`
- `tools/python/tests/test_install.py`
- `migrate.sh` — one-time repo rename script
- Updated `bootstrap.sh` — replaces `install.sh`

**Modify:**
- `hooks/session-start` — update skill file path from `dev-suite/...` to `skills/...` (after rename)
- `manifest.toml` — remove `[bin]` section after all scripts verified

---

## Task 1: Package scaffold

**Files:**
- Create: `tools/python/pyproject.toml`
- Create: `tools/python/src/cf/__init__.py`
- Create: `tools/python/src/cf/main.py`
- Create: `tools/python/tests/conftest.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p tools/python/src/cf tools/python/tests
touch tools/python/src/cf/__init__.py tools/python/tests/__init__.py
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cf"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
]

[project.scripts]
cf = "cf.main:app"

[tool.hatch.build.targets.wheel]
packages = ["src/cf"]
include = ["src/cf/data/*.json"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Write `main.py`**

```python
import typer

app = typer.Typer(no_args_is_help=True)

def _register():
    from cf import context, status, versions, routes, note, read, init, worktree, agents, check, setup, github, browser, install, tools_cmd
    app.add_typer(context.app,   name="context")
    app.add_typer(status.app,    name="status")
    app.add_typer(versions.app,  name="versions")
    app.add_typer(routes.app,    name="routes")
    app.add_typer(note.app,      name="note")
    app.add_typer(read.app,      name="read")
    app.add_typer(init.app,      name="init")
    app.add_typer(worktree.app,  name="worktree")
    app.add_typer(agents.app,    name="agents")
    app.add_typer(check.app,     name="check")
    app.add_typer(setup.app,     name="setup")
    app.add_typer(github.app,    name="github")
    app.add_typer(browser.app,   name="browser")
    app.add_typer(install.app,   name="install")
    app.add_typer(tools_cmd.app, name="tools")

_register()

if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Write `tests/conftest.py`**

```python
import subprocess
import pytest
from pathlib import Path

@pytest.fixture
def git_repo(tmp_path):
    """Minimal git repo for testing."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "README.md").write_text("# test")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path
```

- [ ] **Step 5: Install package in editable mode**

```bash
cd tools/python && uv tool install -e .
```

Expected: `cf --help` shows subcommands (they'll fail until implemented, but the command exists)

- [ ] **Step 6: Commit**

```bash
git add tools/python/ && git commit -m "feat: scaffold cf Python package"
```

---

## Task 2: lib.py — shared utilities

**Files:**
- Create: `tools/python/src/cf/lib.py`
- Create: `tools/python/tests/test_lib.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_lib.py
import os, subprocess
from pathlib import Path
import pytest
from cf.lib import git_root, bus, ensure_bus, bus_exists, gitignore_bus

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
    assert bus() == git_repo / ".claudefiles"

def test_ensure_bus_creates_dir(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    b = ensure_bus()
    assert b.exists()
    assert b == git_repo / ".claudefiles"

def test_bus_exists(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    assert not bus_exists()
    ensure_bus()
    assert bus_exists()

def test_gitignore_bus_adds_entry(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    gitignore_bus()
    assert ".claudefiles/" in (git_repo / ".gitignore").read_text()

def test_gitignore_bus_idempotent(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    gitignore_bus()
    gitignore_bus()
    text = (git_repo / ".gitignore").read_text()
    assert text.count(".claudefiles/") == 1
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd tools/python && uv run pytest tests/test_lib.py -v
```

Expected: `ImportError` or `ModuleNotFoundError`

- [ ] **Step 3: Write `lib.py`**

```python
from pathlib import Path
import subprocess

def git_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return Path(result.stdout.strip())
    return Path.cwd()

def bus() -> Path:
    return git_root() / ".claudefiles"

def ensure_bus() -> Path:
    b = bus()
    b.mkdir(exist_ok=True)
    return b

def bus_exists() -> bool:
    return bus().is_dir()

def gitignore_bus() -> None:
    root = git_root()
    ignore = root / ".gitignore"
    entry = ".claudefiles/"
    if ignore.exists() and entry in ignore.read_text().splitlines():
        return
    with ignore.open("a") as f:
        f.write(f"\n{entry}\n" if ignore.exists() else f"{entry}\n")
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd tools/python && uv run pytest tests/test_lib.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tools/python/src/cf/lib.py tools/python/tests/test_lib.py
git commit -m "feat: add cf/lib.py shared utilities"
```

---

## Task 3: cf context

**Files:**
- Create: `tools/python/src/cf/context.py`
- Create: `tools/python/tests/test_context.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_context.py
import pytest
from typer.testing import CliRunner
from cf.main import app

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
    assert (git_repo / ".claudefiles" / "context.md").exists()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd tools/python && uv run pytest tests/test_context.py -v
```

- [ ] **Step 3: Write `context.py`**

Port the bash script logic to Python. Key sections: runtime detection (check for `package.json`, `Cargo.toml`, `pyproject.toml`, etc.), package manager detection, framework detection from file contents, git state (branch, dirty count, unpushed commits).

```python
import typer
from datetime import datetime
from pathlib import Path
import subprocess
from cf.lib import git_root, bus_exists, bus, ensure_bus

app = typer.Typer(invoke_without_command=True)

@app.callback(invoke_without_command=True)
def main(write: bool = typer.Option(False, "--write")):
    root = git_root()
    lines = []
    line = lines.append

    line(f"# PROJECT CONTEXT")
    line(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    line(f"# Root: {root}")
    line("")

    # Runtime detection
    langs = []
    if (root / "package.json").exists():   langs.append("Node.js")
    if (root / "bun.lock").exists() or (root / "bun.lockb").exists(): langs.append("Bun")
    if (root / "Cargo.toml").exists():     langs.append("Rust")
    if (root / "go.mod").exists():         langs.append("Go")
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists(): langs.append("Python")
    if (root / "Gemfile").exists():        langs.append("Ruby")

    line("RUNTIME")
    line(f"  languages:    {', '.join(langs) if langs else 'unknown'}")

    # Package manager
    pkg_mgr = "none"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists(): pkg_mgr = "bun"
    elif (root / "pnpm-lock.yaml").exists(): pkg_mgr = "pnpm"
    elif (root / "yarn.lock").exists():      pkg_mgr = "yarn"
    elif (root / "package-lock.json").exists() and pkg_mgr == "none": pkg_mgr = "npm"
    elif (root / "Cargo.lock").exists():     pkg_mgr = "cargo"
    elif (root / "uv.lock").exists():        pkg_mgr = "uv"
    elif (root / "poetry.lock").exists():    pkg_mgr = "poetry"
    line(f"  package mgr:  {pkg_mgr}")

    # Framework detection
    frameworks = []
    pkg_json = root / "package.json"
    if pkg_json.exists():
        text = pkg_json.read_text()
        for fw, key in [("Next.js","\"next\""),("React","\"react\""),("Vue","\"vue\""),
                        ("Express","\"express\""),("Fastify","\"fastify\""),("Hono","\"hono\"")]:
            if key in text: frameworks.append(fw)
    cargo = root / "Cargo.toml"
    if cargo.exists():
        text = cargo.read_text()
        for fw in ["axum","actix","rocket"]:
            if fw in text: frameworks.append(fw.capitalize())
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text()
        for fw in ["fastapi","django","flask"]:
            if fw in text: frameworks.append(fw.capitalize())
    if frameworks:
        line(f"  frameworks:   {', '.join(frameworks)}")
    line("")

    # Git state
    def git(*args):
        r = subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""

    branch = git("symbolic-ref", "--short", "HEAD") or "detached"
    dirty = len([l for l in git("status", "--short").splitlines() if l])
    ahead = git("rev-list", "--count", "@{upstream}..HEAD") or "0"

    line("GIT")
    line(f"  branch:       {branch}")
    line(f"  uncommitted:  {dirty} file(s)")
    if int(ahead) > 0:
        line(f"  unpushed:     {ahead} commit(s)")

    bus_dir = bus()
    if bus_dir.exists():
        files = " ".join(f.name for f in sorted(bus_dir.iterdir()))
        line(f"  .claudefiles: {files}")
    line("")

    line("KEY FILES")
    for f in ["README.md","CLAUDE.md",".env",".env.example","tsconfig.json","Makefile","Dockerfile"]:
        if (root / f).exists():
            line(f"  {f}")
    line("")

    out = "\n".join(lines)
    typer.echo(out, nl=False)

    if write:
        b = ensure_bus()
        (b / "context.md").write_text(out)
        typer.echo(f"# Written to {b}/context.md", err=True)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd tools/python && uv run pytest tests/test_context.py -v
```

- [ ] **Step 5: Verify against bash version**

```bash
cd /tmp && git init test-repo && cd test-repo && git commit --allow-empty -m "init"
cf context  # should match cf-context output structurally
```

- [ ] **Step 6: Commit**

```bash
git add tools/python/src/cf/context.py tools/python/tests/test_context.py
git commit -m "feat: port cf-context to cf context"
```

---

## Task 4: cf note + cf read

**Files:**
- Create: `tools/python/src/cf/note.py`
- Create: `tools/python/src/cf/read.py`
- Create: `tools/python/tests/test_note.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_note.py
from typer.testing import CliRunner
from cf.main import app

runner = CliRunner()

def test_note_appends_message(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["note", "hello world"])
    assert result.exit_code == 0
    notes = (git_repo / ".claudefiles" / "notes.md").read_text()
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
    notes = (git_repo / ".claudefiles" / "notes.md").read_text()
    assert "[research]" in notes

def test_read_dumps_all(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    (git_repo / ".claudefiles").mkdir()
    (git_repo / ".claudefiles" / "context.md").write_text("ctx content")
    result = runner.invoke(app, ["read"])
    assert "ctx content" in result.output

def test_read_single_file(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    (git_repo / ".claudefiles").mkdir()
    (git_repo / ".claudefiles" / "notes.md").write_text("notes content")
    result = runner.invoke(app, ["read", "notes"])
    assert "notes content" in result.output
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd tools/python && uv run pytest tests/test_note.py -v
```

- [ ] **Step 3: Write `note.py`**

```python
import typer
from datetime import datetime
from typing import Optional
from cf.lib import bus, ensure_bus

app = typer.Typer(invoke_without_command=True)

@app.callback(invoke_without_command=True)
def main(
    message: Optional[str] = typer.Argument(None),
    agent: str = typer.Option("agent", "--agent"),
    read: bool = typer.Option(False, "--read"),
    clear: bool = typer.Option(False, "--clear"),
):
    notes_file = bus() / "notes.md"

    if read:
        if notes_file.exists():
            typer.echo(notes_file.read_text(), nl=False)
        else:
            typer.echo("(no notes yet)")
        return

    if clear:
        if not notes_file.exists():
            typer.echo("Nothing to clear.")
            return
        notes_file.unlink()
        typer.echo("Cleared.")
        return

    if not message:
        typer.echo("Usage: cf note [--agent <name>] <message>", err=True)
        raise typer.Exit(1)

    ensure_bus()
    if not notes_file.exists():
        notes_file.write_text("# SESSION NOTES\n# .claudefiles/notes.md\n\n")

    ts = datetime.now().strftime("%H:%M:%S")
    with notes_file.open("a") as f:
        f.write(f"[{ts}] [{agent}]\n{message}\n\n")
    typer.echo(f"Note appended to {notes_file}")
```

- [ ] **Step 4: Write `read.py`**

```python
import typer
from typing import Optional
from cf.lib import bus

app = typer.Typer(invoke_without_command=True)

FILE_MAP = {
    "context": "context.md",
    "versions": "versions.md",
    "routes": "routes.md",
    "repo-map": "repo-map.md",
    "notes": "notes.md",
}
DIVIDER = "─" * 60

@app.callback(invoke_without_command=True)
def main(target: Optional[str] = typer.Argument(None)):
    b = bus()
    if not b.exists():
        typer.echo("No .claudefiles/ bus found. Run: cf init")
        raise typer.Exit(1)

    def print_file(name):
        p = b / name
        if p.exists():
            typer.echo(DIVIDER)
            typer.echo(p.read_text(), nl=False)

    if target:
        filename = FILE_MAP.get(target)
        if not filename:
            typer.echo(f"Unknown file: {target}. Valid: {', '.join(FILE_MAP)}", err=True)
            raise typer.Exit(1)
        print_file(filename)
    else:
        for name in FILE_MAP.values():
            print_file(name)
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd tools/python && uv run pytest tests/test_note.py -v
```

- [ ] **Step 6: Commit**

```bash
git add tools/python/src/cf/note.py tools/python/src/cf/read.py tools/python/tests/test_note.py
git commit -m "feat: port cf-note and cf-read"
```

---

## Task 5: cf versions + cf routes

**Files:**
- Create: `tools/python/src/cf/versions.py`
- Create: `tools/python/src/cf/routes.py`

- [ ] **Step 1: Write failing test for versions**

```python
# tests/test_versions.py
from typer.testing import CliRunner
from cf.main import app

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
    assert (git_repo / ".claudefiles" / "versions.md").exists()
```

- [ ] **Step 2: Implement `versions.py`** — port the lockfile/manifest parsing logic from `cf-versions`. Use `re` for toml parsing (no external toml dep needed for this simple case).

- [ ] **Step 3: Write failing test for routes**

```python
# tests/test_routes.py
from typer.testing import CliRunner
from cf.main import app

runner = CliRunner()

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
    assert (git_repo / ".claudefiles" / "routes.md").exists()
```

- [ ] **Step 4: Implement `routes.py`** — port grep patterns from `cf-routes` using Python's `re` module. Walk the tree with `pathlib`, skip `node_modules`, `target`, `.git`, `dist`, `__pycache__`.

- [ ] **Step 5: Run all tests**

```bash
cd tools/python && uv run pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
git add tools/python/src/cf/versions.py tools/python/src/cf/routes.py tools/python/tests/
git commit -m "feat: port cf-versions and cf-routes"
```

---

## Task 6: cf status

**Files:**
- Create: `tools/python/src/cf/status.py`
- Create: `tools/python/tests/test_status.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_status.py
from typer.testing import CliRunner
from cf.main import app

runner = CliRunner()

def test_status_output_headers(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "# REPO MAP" in result.output
    assert "TRUNK" in result.output

def test_status_write(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    runner.invoke(app, ["status", "--write"])
    assert (git_repo / ".claudefiles" / "repo-map.md").exists()
```

- [ ] **Step 2: Implement `status.py`** — port branch/worktree topology logic. Use `subprocess` for all git commands (`git worktree list --porcelain`, `git branch`, `git rev-list`, etc.).

- [ ] **Step 3: Run tests**

```bash
cd tools/python && uv run pytest tests/test_status.py -v
```

- [ ] **Step 4: Commit**

```bash
git add tools/python/src/cf/status.py tools/python/tests/test_status.py
git commit -m "feat: port cf-status"
```

---

## Task 7: cf init + cf worktree

**Files:**
- Create: `tools/python/src/cf/init.py`
- Create: `tools/python/src/cf/worktree.py`

- [ ] **Step 1: Write failing test for init**

```python
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
```

- [ ] **Step 2: Implement `init.py`** — calls `context`, `versions`, `routes`, `status` subcommands with `--write` by invoking their `main()` functions directly.

- [ ] **Step 3: Implement `worktree.py`** — port branch/path/terminal launch logic. For port finding, use Python's `socket` module to find a free port (replaces `lib/port-finder.sh`).

```python
import socket

def find_free_port(start: int = 3000) -> int:
    for port in range(start, start + 100):
        with socket.socket() as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    return start
```

- [ ] **Step 4: Run tests**

```bash
cd tools/python && uv run pytest tests/ -v
```

- [ ] **Step 5: Commit**

```bash
git add tools/python/src/cf/init.py tools/python/src/cf/worktree.py
git commit -m "feat: port cf-init and cf-worktree"
```

---

## Task 8: cf check

**Files:**
- Create: `tools/python/src/cf/check.py`
- Create: `tools/python/tests/test_check.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_check.py
import pytest
from typer.testing import CliRunner
from pathlib import Path
from cf.main import app

runner = CliRunner()

def make_skill(path: Path, name: str):
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}")

def test_check_passes_when_in_sync(tmp_path, monkeypatch):
    suite = tmp_path / "dev-suite"
    cat = suite / "coding"
    make_skill(cat / "git-expert", "git-expert")
    (cat / "REGION.md").write_text("### git-expert\nDoes git things\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "in sync" in result.output

def test_check_fails_when_missing(tmp_path, monkeypatch):
    suite = tmp_path / "dev-suite"
    cat = suite / "coding"
    make_skill(cat / "git-expert", "git-expert")
    (cat / "REGION.md").write_text("# empty\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 1
    assert "git-expert" in result.output
```

- [ ] **Step 2: Implement `check.py`** — port the SKILL.md scanning logic. Find the skills root by checking for `skills/` first, then `dev-suite/` as fallback (supports both pre- and post-migration). Walk recursively, find leaf skills (no child SKILL.md), check `REGION.md` for `### <name>` entry. The test fixture creates `dev-suite/` since migration hasn't run yet; the real repo will use whichever exists.

- [ ] **Step 3: Run tests**

```bash
cd tools/python && uv run pytest tests/test_check.py -v
```

- [ ] **Step 4: Commit**

```bash
git add tools/python/src/cf/check.py tools/python/tests/test_check.py
git commit -m "feat: port cf-check"
```

---

## Task 9: cf agents + cf setup

**Files:**
- Create: `tools/python/src/cf/agents.py`
- Create: `tools/python/src/cf/setup.py`

- [ ] **Step 1: Implement `agents.py`**

Port from `cf-agents` bash script. Key sections:
- Read `~/.claude/plugins/installed_plugins.json` for plugin list
- Walk `~/.claude/skills/` for user skills (use existing `render_tree` logic in Python)
- Walk `.claude/skills/` for project skills
- Read `.mcp.json` for MCP servers
- Read `tools/tools.json` via `importlib.resources` for CLI tool status
- `--tree` mode: print skill hierarchy only
- `--available`: show dev-suite skills not yet installed

No test required for agents (reads live system state — test via manual smoke test).

- [ ] **Step 2: Smoke test agents**

```bash
cf agents --tree   # should show skill hierarchy
cf agents          # full overview
```

- [ ] **Step 3: Write failing tests for `setup.py`** (`tests/test_setup.py`)

```python
from typer.testing import CliRunner
from cf.main import app

runner = CliRunner()

def test_setup_no_skills_dir(git_repo, monkeypatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["setup"])
    assert result.exit_code == 0
    assert "No skills found" in result.output or "No project skills" in result.output

def test_setup_write_creates_deps(git_repo, monkeypatch):
    skills_dir = git_repo / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "git-expert").mkdir()
    (skills_dir / "git-expert" / "SKILL.md").write_text("---\nname: git-expert\n---")
    monkeypatch.chdir(git_repo)
    runner.invoke(app, ["setup", "--write"])
    assert (git_repo / ".claudefiles" / "deps.md").exists()
```

- [ ] **Step 4: Implement `setup.py`**

Port `cf-setup`. Read `[skills.*]` entries from `manifest.toml` (still lives there per spec). For CLI tool status, read from `src/cf/data/tools.json` via `importlib.resources` — NOT from `[cli.*]` in `manifest.toml` (that section is removed). Writes `.claudefiles/deps.md`.

- [ ] **Step 4: Commit**

```bash
git add tools/python/src/cf/agents.py tools/python/src/cf/setup.py
git commit -m "feat: port cf-agents and cf-setup"
```

---

## Task 10: cf github + cf browser stubs + cf install + cf tools

**Files:**
- Create: `tools/python/src/cf/github.py`
- Create: `tools/python/src/cf/browser.py`
- Create: `tools/python/src/cf/install.py`
- Create: `tools/python/src/cf/tools_cmd.py`
- Create: `tools/tools.json`

- [ ] **Step 1: Write stubs for github and browser**

```python
# github.py
import typer
app = typer.Typer(help="GitHub — PRs, issues, branches (coming soon)")

@app.callback(invoke_without_command=True)
def main():
    typer.echo("cf github: coming soon. Subcommands will be added here.")
```

Same pattern for `browser.py`.

- [ ] **Step 2: Write `tools_cmd.py`**

Reads `tools.json` via `importlib.resources`, checks PATH for external tools, outputs formatted list or JSON.

```python
import typer, json, shutil
import importlib.resources as pkg_resources
app = typer.Typer(invoke_without_command=True)

@app.callback(invoke_without_command=True)
def main(as_json: bool = typer.Option(False, "--json")):
    data = json.loads(pkg_resources.files("cf").joinpath("data/tools.json").read_text())
    if as_json:
        typer.echo(json.dumps(data, indent=2))
        return
    for tool in data["tools"]:
        if tool["type"] == "external":
            status = "installed" if shutil.which(tool["name"]) else "missing"
            typer.echo(f"\n### {tool['name']}  [external — {status}]")
        else:
            typer.echo(f"\n### {tool['name']}  [internal]")
        typer.echo(tool["description"])
        typer.echo(f"Usage: {tool['usage']}")
```

- [ ] **Step 3: Create `tools/python/src/cf/data/` and write `tools.json` directly there**

```bash
mkdir -p tools/python/src/cf/data
```

`src/cf/data/tools.json` is the single source of truth — no copy, no symlink. The `cf tools` command reads it via `importlib.resources`. Verify `pyproject.toml` includes `src/cf/data/*.json` in the wheel.

- [ ] **Step 4: Write `tools/python/src/cf/data/tools.json`** with all current tools:

```json
{
  "tools": [
    {"name": "context",  "type": "internal", "package": "cf", "description": "Fingerprint the current project — language, stack, git state", "usage": "cf context [--write]"},
    {"name": "status",   "type": "internal", "package": "cf", "description": "Full repo branch/worktree topology", "usage": "cf status [--write]"},
    {"name": "versions", "type": "internal", "package": "cf", "description": "Dependency versions from lockfiles", "usage": "cf versions [--write]"},
    {"name": "routes",   "type": "internal", "package": "cf", "description": "Scan codebase for API route definitions", "usage": "cf routes [--write]"},
    {"name": "note",     "type": "internal", "package": "cf", "description": "Shared scratchpad for cross-agent communication", "usage": "cf note <message> [--agent <name>] [--read] [--clear]"},
    {"name": "read",     "type": "internal", "package": "cf", "description": "Dump .claudefiles/ bus state", "usage": "cf read [context|versions|routes|repo-map|notes]"},
    {"name": "init",     "type": "internal", "package": "cf", "description": "Bootstrap .claudefiles/ in current project", "usage": "cf init [--dry-run]"},
    {"name": "worktree", "type": "internal", "package": "cf", "description": "Create git worktree and open Claude Code in new terminal", "usage": "cf worktree <branch> [base]"},
    {"name": "agents",   "type": "internal", "package": "cf", "description": "Inventory of skills, plugins, MCP servers, and tool status", "usage": "cf agents [--tree] [--global] [--project] [--available]"},
    {"name": "check",    "type": "internal", "package": "cf", "description": "Verify all leaf skills have entries in their category REGION.md", "usage": "cf check [--verbose]"},
    {"name": "github",   "type": "internal", "package": "cf", "description": "GitHub integration — PRs, issues, branches", "usage": "cf github <subcommand>"},
    {"name": "browser",  "type": "internal", "package": "cf", "description": "Browser automation via Playwright — screenshot, scrape, navigate", "usage": "cf browser <subcommand>"},
    {"name": "qmd",      "type": "external", "manager": "bun", "package": "@tobilu/qmd", "description": "Local markdown search — BM25 + vector + LLM reranking", "usage": "qmd <query> [--dir <path>]", "examples": ["qmd 'authentication flow'"]},
    {"name": "pyright",  "type": "external", "manager": "bun", "package": "pyright", "description": "Python type checker and language server", "usage": "pyright [path]"},
    {"name": "typescript-language-server", "type": "external", "manager": "bun", "install": "bun install -g typescript typescript-language-server", "description": "TypeScript/JavaScript language server", "usage": "typescript-language-server --stdio"},
    {"name": "rust-analyzer", "type": "external", "manager": "rustup", "install": "rustup component add rust-analyzer", "description": "Rust language server", "usage": "rust-analyzer"},
    {"name": "tinymist", "type": "external", "manager": "cargo", "install": "cargo install tinymist", "description": "Typst language server", "usage": "tinymist"}
  ]
}
```

- [ ] **Step 5: Write failing tests for `install.py`** (`tests/test_install.py`)

```python
from typer.testing import CliRunner
from cf.main import app
from pathlib import Path
import pytest

runner = CliRunner()

@pytest.fixture
def claudefiles_repo(tmp_path):
    """Fake claudefiles repo with a skills/ dir."""
    skills = tmp_path / "skills" / "coding"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\nname: coding\n---")
    return tmp_path

def test_install_dry_run_global(claudefiles_repo, tmp_path, monkeypatch):
    target = tmp_path / ".claude" / "skills"
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["install", "--global", "--dry-run",
                                  "--source", str(claudefiles_repo)])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert not target.exists()

def test_install_global_creates_symlinks(claudefiles_repo, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    result = runner.invoke(app, ["install", "--global",
                                  "--source", str(claudefiles_repo)])
    assert result.exit_code == 0
    skill_link = tmp_path / ".claude" / "skills" / "coding"
    assert skill_link.is_symlink() or skill_link.exists()

def test_install_remove(claudefiles_repo, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    runner.invoke(app, ["install", "--global", "--source", str(claudefiles_repo)])
    result = runner.invoke(app, ["install", "--global", "--remove",
                                  "--source", str(claudefiles_repo)])
    assert result.exit_code == 0
    assert not (tmp_path / ".claude" / "skills" / "coding").exists()
```

- [ ] **Step 6: Implement `install.py`** — symlink `skills/` subdirectories to `~/.claude/skills/`. Support `--global`, `--local <path>`, `--skill <name>`, `--category <name>`, `--from <github:owner/repo>` (clone to `~/.local/share/claudefiles-src/`), `--dry-run`, `--remove`. Add `--source <path>` for tests to override the claudefiles repo path (defaults to `CLAUDE_PLUGIN_ROOT` or the package's own location).

- [ ] **Step 6: Reinstall package to pick up data file**

```bash
cd tools/python && uv tool install -e .
cf tools  # should list all tools
```

- [ ] **Step 7: Commit**

```bash
git add tools/ && git commit -m "feat: add cf tools, cf install, stubs for github/browser, tools.json"
```

---

## Task 11: Final wiring + smoke test

- [ ] **Step 1: Run full test suite**

```bash
cd tools/python && uv run pytest tests/ -v
```

Expected: all PASS

- [ ] **Step 2: Smoke test every subcommand**

```bash
cf context
cf status
cf versions
cf routes
cf note "test note"
cf note --read
cf read
cf agents --tree
cf check
cf tools
cf github
cf browser
cf install --dry-run --global
```

- [ ] **Step 3: Update `hooks/session-start`** to point at `skills/` path (post-migration path). Add a fallback for `dev-suite/` so the hook works before migration:

```bash
# In hooks/session-start, update skill path:
SKILL_FILE="$PLUGIN_ROOT/skills/management/orchestration/task-analyser/SKILL.md"
# Fallback:
[[ ! -f "$SKILL_FILE" ]] && SKILL_FILE="$PLUGIN_ROOT/dev-suite/management/orchestration/task-analyser/SKILL.md"
```

- [ ] **Step 4: Final commit**

```bash
git add -A && git commit -m "feat: complete cf Python package implementation"
```

---

## Task 12: migrate.sh + bootstrap.sh

**Files:**
- Create: `migrate.sh`
- Modify: `bootstrap.sh`

- [ ] **Step 1: Write `migrate.sh`**

```bash
#!/usr/bin/env bash
# migrate.sh — one-time repo migration from old structure to new
set -euo pipefail

echo "Step 1: Rename dev-suite/ → skills/"
git mv dev-suite/ skills/

echo "Step 2: Move bin/ → tools/scripts/ (kept for reference during port)"
mkdir -p tools
git mv bin/ tools/scripts/

echo "Step 3: Update skill file references: cf-X → cf X"
find skills/ -name "SKILL.md" -exec sed -i \
  -e 's/`cf-check`/`cf check`/g' \
  -e 's/`cf-agents`/`cf agents`/g' \
  -e 's/`cf-context`/`cf context`/g' \
  -e 's/`cf-status`/`cf status`/g' \
  -e 's/`cf-versions`/`cf versions`/g' \
  -e 's/`cf-routes`/`cf routes`/g' \
  -e 's/`cf-note`/`cf note`/g' \
  -e 's/`cf-read`/`cf read`/g' \
  -e 's/`cf-init`/`cf init`/g' \
  -e 's/`cf-worktree`/`cf worktree`/g' \
  -e 's/`cf-setup`/`cf setup`/g' \
  -e 's/`cf-brief`/`cf brief`/g' \
  {} +

echo "Step 4: Grep for lib/ references in skills/ (manual review needed)"
grep -r "lib/common.sh\|lib/port-finder.sh" skills/ || echo "  (none found)"

echo "Step 5: Update CLAUDE.md path references"
sed -i \
  -e 's|dev-suite/|skills/|g' \
  -e 's|bin/|tools/scripts/|g' \
  CLAUDE.md

echo "Step 6: Remove [cli.*] and [bin] from manifest.toml"
python3 - <<'PYEOF'
import re
with open("manifest.toml") as f:
    content = f.read()
# Remove [bin] section and [cli.*] sections
content = re.sub(r'\[bin\].*?(?=\n\[|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'\[cli\.[^\]]+\].*?(?=\n\[|\Z)', '', content, flags=re.DOTALL)
# Remove cli-specific comment block
content = re.sub(r'# ── CLI tool registry.*?(?=\n\[|\Z)', '', content, flags=re.DOTALL)
with open("manifest.toml", "w") as f:
    f.write(content.strip() + "\n")
PYEOF

echo ""
echo "Migration complete. Review changes with: git diff --cached"
echo "Commit with: git commit -m 'chore: migrate repo structure to new layout'"
```

- [ ] **Step 2: Make executable and run**

```bash
chmod +x migrate.sh
./migrate.sh
git diff --cached   # review
git commit -m "chore: migrate repo structure (dev-suite→skills, bin→tools/scripts)"
```

- [ ] **Step 3: Update `bootstrap.sh`** to use `cf install` instead of `install.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
CLONE_DIR="$HOME/.local/share/claudefiles-src"
git clone https://github.com/EdwardAstill/claudefiles "$CLONE_DIR" 2>/dev/null \
  || git -C "$CLONE_DIR" pull --ff-only
[[ -d "$HOME/.claudefiles" && ! -L "$HOME/.claudefiles" ]] && \
  echo "Note: old ~/.claudefiles/ clone detected — safe to remove after verifying bootstrap succeeded."
uv tool install -e "$CLONE_DIR/tools/python/"
export PATH="$(uv tool dir --bin):$PATH"
cf install --global "$@"
```

- [ ] **Step 4: Update `hooks/session-start`** — add fallback path now that `skills/` is the canonical location:

```bash
SKILL_FILE="$PLUGIN_ROOT/skills/management/orchestration/task-analyser/SKILL.md"
[[ ! -f "$SKILL_FILE" ]] && SKILL_FILE="$PLUGIN_ROOT/dev-suite/management/orchestration/task-analyser/SKILL.md"
```

- [ ] **Step 5: Delete `install.sh`**

```bash
git rm install.sh
git commit -m "chore: remove install.sh, replaced by cf install + bootstrap.sh"
```

- [ ] **Step 6: Update CLAUDE.md** — replace `install.sh` references with `bootstrap.sh` / `cf install`, and `dev-suite/` with `skills/`

- [ ] **Step 7: Commit**

```bash
git add bootstrap.sh hooks/session-start CLAUDE.md
git commit -m "chore: update bootstrap and hooks for new repo structure"
```
