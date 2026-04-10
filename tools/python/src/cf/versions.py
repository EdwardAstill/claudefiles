import re
import json
import typer
from datetime import datetime
from pathlib import Path
from cf.lib import bus, ensure_bus, git_root

app = typer.Typer(invoke_without_command=True)


def _parse_toml_lock_blocks(text: str) -> list[tuple[str, str]]:
    """Parse [[package]] blocks with name/version fields (uv.lock, Cargo.lock, poetry.lock)."""
    results = []
    name = version = None
    for line in text.splitlines():
        if line.startswith("[[package]]"):
            name = version = None
        elif line.startswith("name = "):
            name = line.split(" = ", 1)[1].strip().strip('"')
        elif line.startswith("version = "):
            version = line.split(" = ", 1)[1].strip().strip('"')
            if name and version:
                results.append((name, version))
    return sorted(results)


def _format_section(title: str, entries: list[tuple[str, str]]) -> str:
    lines = [f"## {title}", ""]
    for name, version in entries:
        lines.append(f"{name}: {version}")
    lines.append("")
    return "\n".join(lines)


def _scan_versions(root: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = [f"# DEPENDENCY VERSIONS\n# Generated: {now}\n# Root: {root}\n"]
    found = False

    # pyproject.toml
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        found = True
        uv_lock = root / "uv.lock"
        poetry_lock = root / "poetry.lock"
        if uv_lock.exists():
            entries = _parse_toml_lock_blocks(uv_lock.read_text())
            sections.append(_format_section("uv.lock", entries))
        elif poetry_lock.exists():
            entries = _parse_toml_lock_blocks(poetry_lock.read_text())
            sections.append(_format_section("poetry.lock", entries))
        else:
            # Parse pyproject.toml dependencies directly
            text = pyproject.read_text()
            deps = re.findall(r'"([^"]+)"', text)
            entries = [(d, "(unpinned)") for d in deps if d and not d.startswith("[")]
            sections.append(_format_section("pyproject.toml", entries))

    # requirements.txt (only if no pyproject.toml)
    req_txt = root / "requirements.txt"
    if not pyproject.exists() and req_txt.exists():
        found = True
        lines = [
            l.strip() for l in req_txt.read_text().splitlines()
            if l.strip() and not l.strip().startswith("#")
        ]
        entries = []
        for l in lines:
            m = re.match(r"([A-Za-z0-9_\-\.]+)\s*[=<>!~]+=?\s*([\S]+)?", l)
            if m:
                entries.append((m.group(1), l))
            else:
                entries.append((l, ""))
        sections.append(_format_section("requirements.txt", entries))

    # Cargo.toml / Cargo.lock
    cargo_toml = root / "Cargo.toml"
    if cargo_toml.exists():
        found = True
        cargo_lock = root / "Cargo.lock"
        if cargo_lock.exists():
            entries = _parse_toml_lock_blocks(cargo_lock.read_text())
            sections.append(_format_section("Cargo.lock", entries))
        else:
            text = cargo_toml.read_text()
            in_deps = False
            entries = []
            for line in text.splitlines():
                if re.match(r"^\[(dependencies|dev-dependencies|build-dependencies)\]", line):
                    in_deps = True
                elif line.startswith("["):
                    in_deps = False
                elif in_deps and "=" in line:
                    k, v = line.split("=", 1)
                    entries.append((k.strip(), v.strip().strip('"')))
            sections.append(_format_section("Cargo.toml", sorted(entries)))

    # go.mod
    go_mod = root / "go.mod"
    if go_mod.exists():
        found = True
        text = go_mod.read_text()
        entries = []
        in_require = False
        for line in text.splitlines():
            if line.startswith("require ("):
                in_require = True
            elif in_require and line.strip() == ")":
                in_require = False
            elif in_require:
                parts = line.strip().split()
                if len(parts) >= 2:
                    entries.append((parts[0], parts[1]))
            elif line.startswith("require "):
                parts = line[8:].strip().split()
                if len(parts) >= 2:
                    entries.append((parts[0], parts[1]))
        sections.append(_format_section("go.mod", sorted(entries)))

    # package.json
    pkg_json = root / "package.json"
    if pkg_json.exists():
        found = True
        try:
            data = json.loads(pkg_json.read_text())
        except json.JSONDecodeError:
            data = {}
        all_deps: dict = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            all_deps.update(data.get(key, {}))

        # Try lockfiles for pinned versions
        bun_lock = root / "bun.lock"
        pkg_lock = root / "package-lock.json"
        yarn_lock = root / "yarn.lock"

        pinned: dict[str, str] = {}
        if pkg_lock.exists():
            try:
                lock_data = json.loads(pkg_lock.read_text())
                for name, info in lock_data.get("packages", {}).items():
                    bare = name.lstrip("node_modules/")
                    if bare and isinstance(info, dict):
                        pinned[bare] = info.get("version", "")
                if not pinned:
                    # v1 lockfile format
                    for name, info in lock_data.get("dependencies", {}).items():
                        if isinstance(info, dict):
                            pinned[name] = info.get("version", "")
            except (json.JSONDecodeError, AttributeError):
                pass
        elif bun_lock.exists():
            # bun.lock: lines like `  "pkg@version": [`
            for m in re.finditer(r'"([^"@]+)@([^"]+)"', bun_lock.read_text()):
                pinned.setdefault(m.group(1), m.group(2))

        entries = []
        for name in sorted(all_deps):
            version = pinned.get(name, all_deps[name])
            entries.append((name, version))
        sections.append(_format_section("package.json", entries))

    # Gemfile.lock
    gemfile_lock = root / "Gemfile.lock"
    if gemfile_lock.exists():
        found = True
        text = gemfile_lock.read_text()
        in_gem = False
        entries = []
        for line in text.splitlines():
            if line.strip() == "GEM":
                in_gem = True
            elif in_gem and line.startswith("  specs:"):
                continue
            elif in_gem and re.match(r"^    \S", line):
                m = re.match(r"^\s+(\S+)\s+\(([^)]+)\)", line)
                if m:
                    entries.append((m.group(1), m.group(2)))
            elif in_gem and line.strip() and not line.startswith(" "):
                in_gem = False
        sections.append(_format_section("Gemfile.lock", sorted(entries)))

    if not found:
        sections.append("No recognised dependency files found.\n")

    return "\n".join(sections)


@app.callback(invoke_without_command=True)
def main(
    write: bool = typer.Option(False, "--write", help="Write output to .claudefiles/versions.md"),
):
    """Show pinned dependency versions for the current project."""
    root = git_root()
    output = _scan_versions(root)
    typer.echo(output, nl=False)
    if write:
        ensure_bus()
        out_file = bus() / "versions.md"
        out_file.write_text(output)
        typer.echo(f"# Written to {out_file}", err=True)
