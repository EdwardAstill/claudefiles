from pathlib import Path

from typer.testing import CliRunner

from af.includes import (
    _parse_includes_list,
    _split_frontmatter,
    expand,
    list_fragments,
    missing_includes,
    read_fragment,
)
from af.main import app

runner = CliRunner()


def make_fragment(root: Path, slug: str, body: str) -> None:
    path = root / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {slug}\n---\n\n{body}\n")


def make_skill(path: Path, includes: list[str], extra_body: str = "body text") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", "name: demo-skill"]
    if includes:
        lines.append("includes:")
        for slug in includes:
            lines.append(f"  - {slug}")
    lines.append("---")
    lines.append("")
    lines.append("# Demo")
    lines.append("")
    lines.append(extra_body)
    path.write_text("\n".join(lines) + "\n")


def test_split_frontmatter():
    fm, body = _split_frontmatter("---\nname: x\n---\nhello")
    assert fm == "name: x"
    assert body == "hello"


def test_parse_includes_list_simple():
    fm = "name: demo\nincludes:\n  - a/b\n  - c/d\ndescription: foo\n"
    assert _parse_includes_list(fm) == ["a/b", "c/d"]


def test_parse_includes_list_absent():
    assert _parse_includes_list("name: demo\n") == []


def test_read_fragment_strips_frontmatter(tmp_path):
    root = tmp_path / "includes"
    make_fragment(root, "python/pyright", "# Pyright\n\nbody content")
    got = read_fragment("python/pyright", root)
    assert "---" not in got
    assert got.startswith("# Pyright")
    assert "body content" in got


def test_list_fragments(tmp_path):
    root = tmp_path / "includes"
    make_fragment(root, "python/pyright", "x")
    make_fragment(root, "python/uv", "y")
    make_fragment(root, "rust/clippy", "z")
    assert list_fragments(root) == ["python/pyright", "python/uv", "rust/clippy"]


def test_expand_no_includes_returns_unchanged(tmp_path):
    skill = tmp_path / "SKILL.md"
    make_skill(skill, includes=[])
    assert expand(skill, root=tmp_path / "includes") == skill.read_text()


def test_expand_appends_shared_conventions(tmp_path):
    root = tmp_path / "includes"
    make_fragment(root, "python/pyright", "Pyright body.")
    make_fragment(root, "python/uv", "uv body.")
    skill = tmp_path / "SKILL.md"
    make_skill(skill, includes=["python/pyright", "python/uv"])
    out = expand(skill, root=root)
    assert "## Shared Conventions" in out
    assert "<!-- include: python/pyright -->" in out
    assert "Pyright body." in out
    assert "<!-- include: python/uv -->" in out
    assert "uv body." in out
    # Original body still there.
    assert "# Demo" in out


def test_missing_includes_detects_bad_slug(tmp_path):
    root = tmp_path / "includes"
    make_fragment(root, "python/pyright", "ok")
    skill = tmp_path / "SKILL.md"
    make_skill(skill, includes=["python/pyright", "python/does-not-exist"])
    assert missing_includes(skill, root=root) == ["python/does-not-exist"]


def test_cli_show_prints_body(tmp_path, monkeypatch):
    root = tmp_path / "agentfiles" / "includes"
    make_fragment(root, "python/ruff", "ruff body line")
    monkeypatch.chdir(tmp_path)
    # Need a manifest.toml so find_repo_root accepts tmp_path.
    (tmp_path / "manifest.toml").write_text("")
    result = runner.invoke(app, ["include", "show", "python/ruff"])
    assert result.exit_code == 0
    assert "ruff body line" in result.output


def test_cli_list_sorts(tmp_path, monkeypatch):
    root = tmp_path / "agentfiles" / "includes"
    make_fragment(root, "rust/clippy", "c")
    make_fragment(root, "python/uv", "u")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "manifest.toml").write_text("")
    result = runner.invoke(app, ["include", "list"])
    assert result.exit_code == 0
    assert result.output.splitlines() == ["python/uv", "rust/clippy"]


def test_cli_check_passes(tmp_path, monkeypatch):
    root = tmp_path / "agentfiles" / "includes"
    make_fragment(root, "python/pyright", "x")
    skill = tmp_path / "SKILL.md"
    make_skill(skill, includes=["python/pyright"])
    monkeypatch.chdir(tmp_path)
    (tmp_path / "manifest.toml").write_text("")
    result = runner.invoke(app, ["include", "check", str(skill)])
    assert result.exit_code == 0


def test_cli_check_fails_on_missing(tmp_path, monkeypatch):
    root = tmp_path / "agentfiles" / "includes"
    make_fragment(root, "python/pyright", "x")
    skill = tmp_path / "SKILL.md"
    make_skill(skill, includes=["python/pyright", "does/not-exist"])
    monkeypatch.chdir(tmp_path)
    (tmp_path / "manifest.toml").write_text("")
    result = runner.invoke(app, ["include", "check", str(skill)])
    assert result.exit_code == 1
    assert "does/not-exist" in result.output
