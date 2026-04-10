import typer
from datetime import datetime
from pathlib import Path
import subprocess
from cf.lib import git_root, bus, ensure_bus

app = typer.Typer(invoke_without_command=True)

@app.callback(invoke_without_command=True)
def main(write: bool = typer.Option(False, "--write")):
    root = git_root()
    lines = []
    line = lines.append

    line("# PROJECT CONTEXT")
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
    if (root / "pom.xml").exists() or (root / "build.gradle").exists(): langs.append("Java/JVM")
    if (root / "composer.json").exists():  langs.append("PHP")

    line("RUNTIME")
    line(f"  languages:    {', '.join(langs) if langs else 'unknown'}")

    # Package manager
    pkg_mgr = "none"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists(): pkg_mgr = "bun"
    elif (root / "pnpm-lock.yaml").exists(): pkg_mgr = "pnpm"
    elif (root / "yarn.lock").exists():      pkg_mgr = "yarn"
    elif (root / "package-lock.json").exists(): pkg_mgr = "npm"
    elif (root / "Cargo.lock").exists():     pkg_mgr = "cargo"
    elif (root / "go.sum").exists():         pkg_mgr = "go mod"
    elif (root / "uv.lock").exists():        pkg_mgr = "uv"
    elif (root / "poetry.lock").exists():    pkg_mgr = "poetry"
    line(f"  package mgr:  {pkg_mgr}")

    # Framework detection
    frameworks = []
    pkg_json = root / "package.json"
    if pkg_json.exists():
        text = pkg_json.read_text()
        for fw, key in [("Next.js","\"next\""),("React","\"react\""),("Vue","\"vue\""),
                        ("Svelte","\"svelte\""),("Express","\"express\""),("Fastify","\"fastify\""),
                        ("Hono","\"hono\""),("Astro","\"astro\"")]:
            if key in text: frameworks.append(fw)
    cargo = root / "Cargo.toml"
    if cargo.exists():
        text = cargo.read_text()
        for fw, name in [("Axum","axum"),("Actix","actix"),("Rocket","rocket")]:
            if name in text: frameworks.append(fw)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text()
        for fw, name in [("FastAPI","fastapi"),("Django","django"),("Flask","flask")]:
            if name in text: frameworks.append(fw)
    if frameworks:
        line(f"  frameworks:   {', '.join(frameworks)}")
    line("")

    # Git state
    def git(*args):
        r = subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""

    branch = git("symbolic-ref", "--short", "HEAD") or "detached"
    dirty = len([l for l in git("status", "--short").splitlines() if l])
    upstream_result = subprocess.run(
        ["git", "-C", str(root), "rev-list", "--count", "@{upstream}..HEAD"],
        capture_output=True, text=True
    )
    ahead = upstream_result.stdout.strip() if upstream_result.returncode == 0 else "0"

    line("GIT")
    line(f"  branch:       {branch}")
    line(f"  uncommitted:  {dirty} file(s)")
    if ahead and int(ahead) > 0:
        line(f"  unpushed:     {ahead} commit(s)")

    if bus().exists():
        files = " ".join(f.name for f in sorted(bus().iterdir()))
        line(f"  .claudefiles: {files}")
    line("")

    line("KEY FILES")
    for f in ["README.md","CLAUDE.md",".env",".env.example","tsconfig.json","Makefile","Dockerfile","docker-compose.yml"]:
        if (root / f).exists():
            line(f"  {f}")
    line("")

    out = "\n".join(lines)
    typer.echo(out, nl=False)

    if write:
        b = ensure_bus()
        (b / "context.md").write_text(out)
        typer.echo(f"# Written to {b}/context.md", err=True)
