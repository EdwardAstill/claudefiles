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
    if ignore.exists():
        lines = ignore.read_text().splitlines()
        if entry in lines:
            return
        with ignore.open("a") as f:
            f.write(f"\n{entry}\n")
    else:
        ignore.write_text(f"{entry}\n")
