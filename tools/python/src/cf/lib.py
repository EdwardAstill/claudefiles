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
        content = ignore.read_text()
        if entry in content.splitlines():
            return
        sep = "" if content.endswith("\n") else "\n"
        ignore.write_text(content + sep + entry + "\n")
    else:
        ignore.write_text(entry + "\n")
