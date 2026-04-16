"""af repo — GitHub repository reconnaissance."""

import base64
import json
import subprocess
import sys
from pathlib import PurePosixPath
from typing import Optional

import typer

app = typer.Typer(invoke_without_command=True)


# ── helpers ──────────────────────────────────────────────────────────────────


def _gh_api(endpoint: str, jq: str | None = None) -> str | None:
    """Call gh api and return stdout, or None on error."""
    cmd = ["gh", "api", endpoint]
    if jq:
        cmd.extend(["--jq", jq])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _gh_api_json(endpoint: str) -> dict | list | None:
    raw = _gh_api(endpoint)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.0f}{unit}" if unit == "B" else f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}TB"


def _fmt_count(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


# ── key-file classification ─────────────────────────────────────────────────

_ENTRY_NAMES = {
    "main.py", "app.py", "index.ts", "index.js", "main.ts", "main.rs",
    "main.go", "lib.rs", "index.tsx", "index.jsx", "server.py", "server.ts",
    "server.js", "cli.py", "cli.ts", "__main__.py",
}

_CONFIG_NAMES = {
    "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "Gemfile",
    "pom.xml", "build.gradle", "build.gradle.kts", "Makefile", "CMakeLists.txt",
    "tsconfig.json", "vite.config.ts", "vite.config.js", "webpack.config.js",
    "next.config.js", "next.config.ts", "next.config.mjs",
    "docker-compose.yml", "docker-compose.yaml",
}

_DOC_NAMES = {"README.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE"}


def _classify_files(paths: list[str]) -> dict[str, list[str]]:
    cats: dict[str, list[str]] = {
        "entry_points": [], "config": [], "docs": [], "ci": [],
        "docker": [], "test_dirs": [],
    }
    seen: set[str] = set()

    for p in paths:
        name = PurePosixPath(p).name
        depth = p.count("/")

        # entry points — only top-level or src/ (skip deep sub-crate duplicates)
        if name in _ENTRY_NAMES and depth <= 2:
            cats["entry_points"].append(p)

        # config — only root-level config files
        if name in _CONFIG_NAMES and depth == 0:
            cats["config"].append(p)

        # docs — only root-level
        if name in _DOC_NAMES and depth == 0:
            cats["docs"].append(p)
        if p.startswith("docs/") and "docs/" not in seen:
            cats["docs"].append("docs/")
            seen.add("docs/")

        # ci
        if p.startswith(".github/workflows/") and ".github/workflows" not in seen:
            cats["ci"].append(".github/workflows/")
            seen.add(".github/workflows")
        for ci in (".gitlab-ci.yml", "Jenkinsfile", ".circleci/config.yml"):
            if p == ci:
                cats["ci"].append(ci)

        # docker
        if "Dockerfile" in name and depth <= 1:
            cats["docker"].append(p)

        # test dirs
        for td in ("tests/", "test/", "__tests__/", "spec/", "e2e/"):
            if p.startswith(td) and td not in seen:
                cats["test_dirs"].append(td.rstrip("/"))
                seen.add(td)

    return {k: sorted(set(v)) for k, v in cats.items() if v}


# ── compact tree rendering ──────────────────────────────────────────────────


def _render_compact_tree(items: list[dict], max_depth: int) -> list[str]:
    """Render a GitHub tree API response as a compact directory listing."""
    lines: list[str] = []
    root_files: list[str] = []
    dirs: dict[str, dict] = {}  # top-level dir -> {files: int, dirs: int, children: []}

    for item in items:
        path = item["path"]
        parts = path.split("/")
        depth = len(parts) - 1

        if depth == 0:
            if item["type"] == "tree":
                dirs.setdefault(path, {"files": 0, "subdirs": 0, "children": []})
            else:
                root_files.append(path)
        else:
            top = parts[0]
            dirs.setdefault(top, {"files": 0, "subdirs": 0, "children": []})
            if item["type"] == "tree":
                dirs[top]["subdirs"] += 1
            else:
                dirs[top]["files"] += 1
            if depth < max_depth:
                dirs[top]["children"].append((path, item["type"]))

    # root files first
    for f in sorted(root_files):
        lines.append(f"  {f}")

    # then directories
    for d in sorted(dirs.keys()):
        info = dirs[d]
        total = info["files"] + info["subdirs"]
        if total == 0:
            lines.append(f"  {d}/")
        elif total <= 10:
            # show children inline
            child_names = []
            for cpath, ctype in sorted(info["children"], key=lambda x: x[0]):
                rel = cpath[len(d) + 1:]
                if "/" not in rel:  # direct children only
                    child_names.append(rel + "/" if ctype == "tree" else rel)
            if child_names:
                lines.append(f"  {d}/ → {', '.join(child_names[:12])}")
            else:
                lines.append(f"  {d}/ ({info['files']} files)")
        else:
            lines.append(f"  {d}/ ({info['files']} files, {info['subdirs']} dirs)")

    return lines


# ── commands ─────────────────────────────────────────────────────────────────


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """GitHub repository reconnaissance."""
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@app.command()
def recon(
    repo: str = typer.Argument(..., help="owner/repo"),
    max_depth: int = typer.Option(3, "--depth", "-d", help="Tree display depth"),
):
    """Full reconnaissance — metadata, tree, languages, key files, recent commits."""
    meta = _gh_api_json(f"repos/{repo}")
    if meta is None:
        print(f"Error: could not fetch {repo}. Check the name and your gh auth.", file=sys.stderr)
        raise typer.Exit(1)

    languages = _gh_api_json(f"repos/{repo}/languages") or {}
    tree_data = _gh_api_json(f"repos/{repo}/git/trees/HEAD?recursive=1")
    commits_raw = _gh_api(
        f"repos/{repo}/commits?per_page=5",
        jq='.[].commit.message | split("\\n")[0]',
    )

    # ── header ───────────────────────────────────────────────────────────
    desc = meta.get("description") or "—"
    lic = (meta.get("license") or {}).get("spdx_id", "—")
    stars = _fmt_count(meta.get("stargazers_count", 0))
    forks = _fmt_count(meta.get("forks_count", 0))
    issues = _fmt_count(meta.get("open_issues_count", 0))
    size = _fmt_size(meta.get("size", 0) * 1024)
    branch = meta.get("default_branch", "main")
    created = (meta.get("created_at") or "—")[:10]
    pushed = (meta.get("pushed_at") or "—")[:10]
    topics = meta.get("topics", [])

    stars_raw = meta.get("stargazers_count", 0)
    star_bar = "★" * min(10, round(stars_raw / max(stars_raw, 1) * 10)) if stars_raw else ""

    print(f"# {repo}\n")
    print(f"{desc}\n")
    print(f"★ {stars_raw:,} stars  ({forks} forks  {issues} open issues)")
    print(f"License: {lic}  Size: {size}  Branch: {branch}")
    print(f"Created: {created}  Last push: {pushed}")
    if topics:
        print(f"Topics: {', '.join(topics)}")
    print()

    # ── languages ────────────────────────────────────────────────────────
    if languages:
        total = sum(languages.values())
        parts = [f"{lang} {v / total * 100:.0f}%" for lang, v in languages.items() if v / total >= 0.01]
        print(f"## Languages\n{', '.join(parts)}\n")

    # ── tree ─────────────────────────────────────────────────────────────
    if tree_data and "tree" in tree_data:
        all_items = tree_data["tree"]
        all_paths = [i["path"] for i in all_items]
        file_count = sum(1 for i in all_items if i["type"] != "tree")

        print(f"## Structure ({file_count} files)")
        for line in _render_compact_tree(all_items, max_depth):
            print(line)
        print()

        # ── key files ────────────────────────────────────────────────────
        key = _classify_files(all_paths)
        if key:
            print("## Key Files")
            max_show = 8
            for cat, items in key.items():
                label = cat.replace("_", " ").title()
                if len(items) <= max_show:
                    print(f"  {label}: {', '.join(items)}")
                else:
                    shown = ', '.join(items[:max_show])
                    print(f"  {label}: {shown} … and {len(items) - max_show} more")
            print()

    # ── recent commits ───────────────────────────────────────────────────
    if commits_raw:
        print("## Recent Commits")
        for line in commits_raw.splitlines()[:5]:
            print(f"  - {line}")
        print()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    language: Optional[str] = typer.Option(None, "--language", "-l"),
    sort: str = typer.Option("stars", "--sort", "-s", help="stars|forks|updated"),
    limit: int = typer.Option(10, "--limit", "-n"),
):
    """Search GitHub repos by keyword."""
    cmd = [
        "gh", "search", "repos", query,
        f"--sort={sort}", f"--limit={limit}",
        "--json", "fullName,description,stargazersCount,language,updatedAt",
    ]
    if language:
        cmd.append(f"--language={language}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Search failed: {result.stderr}", file=sys.stderr)
        raise typer.Exit(1)

    repos = json.loads(result.stdout)
    if not repos:
        print("No results.")
        return

    max_name = max(len(r["fullName"]) for r in repos)
    for r in repos:
        stars = f"★{r.get('stargazersCount', 0):>6,}"
        lang = (r.get("language") or "—")[:12]
        desc = ((r.get("description") or "—")[:60])
        name = r["fullName"].ljust(max_name)
        print(f"  {name}  {stars}  {lang:<12}  {desc}")


@app.command()
def tree(
    repo: str = typer.Argument(..., help="owner/repo"),
    depth: int = typer.Option(3, "--depth", "-d"),
):
    """Show remote repo file tree."""
    tree_data = _gh_api_json(f"repos/{repo}/git/trees/HEAD?recursive=1")
    if not tree_data or "tree" not in tree_data:
        print(f"Error: could not fetch tree for {repo}", file=sys.stderr)
        raise typer.Exit(1)

    for item in tree_data["tree"]:
        path = item["path"]
        level = path.count("/")
        if level < depth:
            indent = "  " * level
            name = PurePosixPath(path).name
            if item["type"] == "tree":
                name += "/"
            elif "size" in item:
                name += f"  ({_fmt_size(item['size'])})"
            print(f"{indent}{name}")


@app.command("read")
def read_file(
    repo: str = typer.Argument(..., help="owner/repo"),
    path: str = typer.Argument(..., help="File path within repo"),
    ref: Optional[str] = typer.Option(None, "--ref", "-r", help="Branch or tag"),
):
    """Read a file from a remote GitHub repo (handles base64 decoding)."""
    endpoint = f"repos/{repo}/contents/{path}"
    if ref:
        endpoint += f"?ref={ref}"

    raw = _gh_api_json(endpoint)
    if raw is None:
        print(f"Error: could not read {repo}/{path}", file=sys.stderr)
        raise typer.Exit(1)

    if isinstance(raw, list):
        # It's a directory listing
        for entry in raw:
            t = "d" if entry.get("type") == "dir" else "f"
            sz = _fmt_size(entry.get("size", 0)) if t == "f" else ""
            print(f"  [{t}] {entry['name']}  {sz}")
        return

    content_b64 = raw.get("content", "")
    try:
        print(base64.b64decode(content_b64).decode("utf-8"))
    except Exception:
        print("Error: could not decode (binary file?)", file=sys.stderr)
        raise typer.Exit(1)
