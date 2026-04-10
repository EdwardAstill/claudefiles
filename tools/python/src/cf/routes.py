import re
import typer
from datetime import datetime
from pathlib import Path
from cf.lib import bus, ensure_bus, git_root

app = typer.Typer(invoke_without_command=True)

SKIP_DIRS = {
    "node_modules", "target", ".git", "dist", "build",
    "__pycache__", ".venv", "venv", ".next", ".nuxt",
}

EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".rs", ".py", ".go"}

# Each scanner: (label, pattern, method_group_idx_or_None, path_group_idx)
SCANNERS = [
    (
        "Express / Fastify / Hono",
        re.compile(r'\.(get|post|put|patch|delete|options|head)\s*\([\'"](/[^\'"]*)', re.IGNORECASE),
        1,  # method group
        2,  # path group
    ),
    (
        "Next.js App Router",
        re.compile(r'^export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s*\('),
        1,
        None,  # no path in pattern
    ),
    (
        "Axum",
        re.compile(r'\.(get|post|put|patch|delete|options|head)\s*\("[\'"]?(/[^\'"]*)', re.IGNORECASE),
        1,
        2,
    ),
    (
        "Actix-web",
        re.compile(r'#\[(?:web\.)?(get|post|put|patch|delete|options|head)\s*\("[\'"]?(/[^\'"]*)', re.IGNORECASE),
        1,
        2,
    ),
    (
        "FastAPI",
        re.compile(r'@(?:app|router)\.(get|post|put|patch|delete|options|head)\s*\([\'"](/[^\'"]*)', re.IGNORECASE),
        1,
        2,
    ),
    (
        "Go net/http",
        re.compile(r'HandleFunc\s*\([\'"](/[^\'"]*)', re.IGNORECASE),
        None,
        1,
    ),
    (
        "Go chi",
        re.compile(r'\.(Get|Post|Put|Patch|Delete|Options|Head)\s*\([\'"](/[^\'"]*)', re.IGNORECASE),
        1,
        2,
    ),
    (
        "Go Gin",
        re.compile(r'\.(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s*\([\'"](/[^\'"]*)', re.IGNORECASE),
        1,
        2,
    ),
]


def _iter_source_files(root: Path):
    """Walk tree yielding source files, skipping ignored dirs."""
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in EXTENSIONS:
            # Check none of the path parts are in SKIP_DIRS
            if not any(part in SKIP_DIRS for part in path.parts):
                yield path


def _scan_routes(root: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"# API ROUTES\n# Generated: {now}\n# Root: {root}\n\n"

    # Collect all source files
    source_files = list(_iter_source_files(root))

    # Run each scanner across all files
    sections: list[str] = []

    for label, pattern, method_grp, path_grp in SCANNERS:
        matches: list[str] = []
        for fpath in source_files:
            try:
                text = fpath.read_text(errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                m = pattern.search(line)
                if m:
                    rel = fpath.relative_to(root)
                    method = m.group(method_grp).upper() if method_grp else "ROUTE"
                    path = m.group(path_grp) if path_grp else "(see file)"
                    matches.append(f"  {rel}:{lineno} {method} {path}")
        if matches:
            sections.append(f"## {label}\n\n" + "\n".join(matches) + "\n")

    # Next.js file-based routes: pages/api/ or app/api/ directories
    nextjs_routes: list[str] = []
    for api_dir_name in ("pages/api", "app/api"):
        api_dir = root / api_dir_name
        if api_dir.exists() and api_dir.is_dir():
            for fpath in sorted(api_dir.rglob("*")):
                if fpath.is_file() and fpath.suffix in EXTENSIONS:
                    rel = fpath.relative_to(root)
                    nextjs_routes.append(f"  {rel}")
    if nextjs_routes:
        sections.append("## Next.js File Routes\n\n" + "\n".join(nextjs_routes) + "\n")

    if not sections:
        body = (
            "No route definitions found.\n"
            "Supported: Express, Fastify, Hono, Next.js, Axum, Actix-web, FastAPI, "
            "Go (net/http, chi, gin)\n"
        )
    else:
        body = "\n".join(sections)

    return header + body


@app.callback(invoke_without_command=True)
def main(
    write: bool = typer.Option(False, "--write", help="Write output to .claudefiles/routes.md"),
):
    """Scan the codebase for API route definitions."""
    root = git_root()
    output = _scan_routes(root)
    typer.echo(output, nl=False)
    if write:
        ensure_bus()
        out_file = bus() / "routes.md"
        out_file.write_text(output)
        typer.echo(f"# Written to {out_file}", err=True)
