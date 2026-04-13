import typer
import subprocess
from datetime import datetime
from pathlib import Path
from af.lib import git_root, bus, ensure_bus

app = typer.Typer(invoke_without_command=True)


def _git(root: Path, *args) -> str:
    """Run git command in repo root."""
    result = subprocess.run(
        ["git", "-C", str(root)] + list(args),
        capture_output=True,
        text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _find_trunk(root: Path) -> str:
    """Find trunk branch (main, master, or current default)."""
    # Check for main
    if _git(root, "show-ref", "--verify", "--quiet", "refs/heads/main"):
        return "main"
    # Check for master
    if _git(root, "show-ref", "--verify", "--quiet", "refs/heads/master"):
        return "master"
    # Fall back to current branch
    result = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--short", "HEAD"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip() if result.returncode == 0 else "HEAD"


def _parse_worktrees(root: Path) -> dict[str, dict]:
    """Parse git worktree list --porcelain output."""
    worktrees = {}
    current_path = None
    current_branch = None
    current_bare = False

    result = subprocess.run(
        ["git", "-C", str(root), "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True
    )

    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            current_path = line[9:]
        elif line.startswith("branch "):
            current_branch = line[14:]  # Strip "branch refs/heads/"
        elif line == "bare":
            current_bare = True
        elif line == "" and current_path and current_branch:
            # Extract branch name from refs path
            branch_name = current_branch.split("/")[-1] if "/" in current_branch else current_branch
            worktrees[branch_name] = {
                "path": current_path,
                "bare": current_bare
            }
            # Check for .env PORT
            env_file = Path(current_path) / ".env"
            if env_file.exists():
                try:
                    content = env_file.read_text()
                    for line_text in content.splitlines():
                        if line_text.startswith("PORT="):
                            worktrees[branch_name]["port"] = line_text[5:]
                            break
                except Exception:
                    pass
            current_path = None
            current_branch = None
            current_bare = False

    return worktrees


def _format_sync_status(trunk: str, root: Path) -> tuple[int, int, str]:
    """Get trunk's remote tracking status."""
    remote_result = subprocess.run(
        ["git", "-C", str(root), "for-each-ref", "--format=%(upstream:short)", f"refs/heads/{trunk}"],
        capture_output=True,
        text=True
    )
    trunk_remote = remote_result.stdout.strip()

    if not trunk_remote:
        return 0, 0, "(no remote tracking)"

    # Count commits ahead/behind
    ahead_result = subprocess.run(
        ["git", "-C", str(root), "rev-list", "--count", f"{trunk_remote}..{trunk}"],
        capture_output=True,
        text=True
    )
    behind_result = subprocess.run(
        ["git", "-C", str(root), "rev-list", "--count", f"{trunk}..{trunk_remote}"],
        capture_output=True,
        text=True
    )

    ahead = int(ahead_result.stdout.strip()) if ahead_result.returncode == 0 else 0
    behind = int(behind_result.stdout.strip()) if behind_result.returncode == 0 else 0

    if ahead == 0 and behind == 0:
        sync = "(in sync)"
    elif ahead > 0 and behind == 0:
        sync = f"({ahead} ahead — not yet pushed)"
    elif ahead == 0 and behind > 0:
        sync = f"({behind} behind — pull available)"
    else:
        sync = f"(diverged: +{ahead} / -{behind})"

    return ahead, behind, sync


@app.callback(invoke_without_command=True)
def main(write: bool = typer.Option(False, "--write", help="Write output to .agentfiles/repo-map.md")):
    """Generate a full branch/worktree topology map for the current repo."""
    root = git_root()
    lines = []

    # Header
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append("# REPO MAP")
    lines.append(f"# Generated: {now}")
    lines.append(f"# Repo: {root}")
    lines.append("")

    # Find trunk
    trunk = _find_trunk(root)
    trunk_head = _git(root, "rev-parse", "--short", trunk) or "unknown"
    trunk_msg = _git(root, "log", "-1", "--pretty=format:%s", trunk) or ""
    remote_result = subprocess.run(
        ["git", "-C", str(root), "for-each-ref", "--format=%(upstream:short)", f"refs/heads/{trunk}"],
        capture_output=True,
        text=True
    )
    trunk_remote = remote_result.stdout.strip()

    ahead, behind, sync = _format_sync_status(trunk, root)

    # Parse worktrees
    worktrees = _parse_worktrees(root)
    trunk_path = worktrees.get(trunk, {}).get("path", str(root))

    # Output trunk section
    lines.append("TRUNK")
    lines.append(f"  branch:  {trunk}")
    lines.append(f"  HEAD:    {trunk_head}  \"{trunk_msg}\"")
    lines.append(f"  remote:  {trunk_remote or 'none'} {sync}")
    lines.append(f"  path:    {trunk_path}")
    lines.append("")

    # Get all branches (excluding trunk)
    branches_result = subprocess.run(
        ["git", "-C", str(root), "branch", "--format=%(refname:short)"],
        capture_output=True,
        text=True
    )
    all_branches = [b for b in branches_result.stdout.strip().split("\n") if b and b != trunk]

    active_branches = 0
    active_worktrees = 0
    stale_branches = []
    diverged = 0
    warnings = []

    if all_branches:
        lines.append("BRANCHES & WORKTREES ──────────────────────────────────────────────")
        lines.append("")

        for branch in all_branches:
            # Check if branch is valid
            verify = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "--short", branch],
                capture_output=True,
                text=True
            )
            if verify.returncode != 0:
                continue

            # Get merge base with trunk
            merge_base_result = subprocess.run(
                ["git", "-C", str(root), "merge-base", trunk, branch],
                capture_output=True,
                text=True
            )
            if merge_base_result.returncode != 0:
                continue

            merge_base = merge_base_result.stdout.strip()
            base_hash = _git(root, "rev-parse", "--short", merge_base) or "unknown"
            base_msg = _git(root, "log", "-1", "--pretty=format:%s", merge_base) or "unknown"
            base_ago = _git(root, "log", "-1", "--pretty=format:%cr", merge_base) or ""

            # Count commits ahead/behind
            ahead_count_result = subprocess.run(
                ["git", "-C", str(root), "rev-list", "--count", f"{trunk}..{branch}"],
                capture_output=True,
                text=True
            )
            behind_count_result = subprocess.run(
                ["git", "-C", str(root), "rev-list", "--count", f"{branch}..{trunk}"],
                capture_output=True,
                text=True
            )

            ahead_count = int(ahead_count_result.stdout.strip()) if ahead_count_result.returncode == 0 else 0
            behind_count = int(behind_count_result.stdout.strip()) if behind_count_result.returncode == 0 else 0

            # Check if stale (no commits ahead)
            if ahead_count == 0:
                stale_branches.append(branch)
                continue

            active_branches += 1
            wt_path = worktrees.get(branch, {}).get("path")
            wt_port = worktrees.get(branch, {}).get("port")
            status_label = "CLEAN"

            if wt_path:
                active_worktrees += 1
                dirty_result = subprocess.run(
                    ["git", "-C", wt_path, "status", "--short"],
                    capture_output=True,
                    text=True
                )
                dirty_lines = dirty_result.stdout.strip().split("\n") if dirty_result.returncode == 0 else []
                if dirty_lines and dirty_lines[0]:
                    mod = sum(1 for l in dirty_lines if l.startswith((" M", "M ")))
                    untrack = sum(1 for l in dirty_lines if l.startswith("??"))
                    status_label = f"DIRTY ({mod} modified, {untrack} untracked)"

            # Get recent commits
            commits_result = subprocess.run(
                ["git", "-C", str(root), "log", "--oneline", f"{merge_base}..{branch}"],
                capture_output=True,
                text=True
            )
            commits = [c for c in commits_result.stdout.strip().split("\n") if c][:5]

            # Get diff stat
            diff_result = subprocess.run(
                ["git", "-C", str(root), "diff", "--stat", f"{trunk}...{branch}"],
                capture_output=True,
                text=True
            )
            diff_lines = diff_result.stdout.strip().split("\n") if diff_result.returncode == 0 else []
            diff_stat = diff_lines[-1].strip() if diff_lines and diff_lines[-1].strip() else ""

            # Output branch
            lines.append(branch)
            if wt_path:
                lines.append(f"  worktree:    {wt_path}")
                if wt_port:
                    lines.append(f"  port:        {wt_port}")
            else:
                lines.append("  worktree:    none (local branch)")
            lines.append(f"  status:      {status_label}")
            lines.append(f"  branched from: {base_hash}  \"{base_msg}\"  [{base_ago}]")

            if commits:
                lines.append("  commits since branch:")
                for i, commit in enumerate(commits):
                    if i == 0:
                        lines.append(f"    HEAD     {commit}")
                    else:
                        lines.append(f"    HEAD~{i}   {commit}")

            if behind_count > 0:
                lines.append(f"  ahead/behind {trunk}:  +{ahead_count} / -{behind_count}   ← BEHIND: {trunk} has moved, consider rebasing")
                warnings.append(f"! {branch} is {behind_count} commit(s) behind {trunk} — consider: git rebase {trunk}")
                diverged += 1
            else:
                lines.append(f"  ahead/behind {trunk}:  +{ahead_count} / 0")

            if diff_stat:
                lines.append(f"  diff summary:  {diff_stat}")
            lines.append("")

    if stale_branches:
        lines.append("STALE / MERGED ────────────────────────────────────────────────────")
        lines.append("")
        for branch in stale_branches:
            last_ago = _git(root, "log", "-1", "--pretty=format:%cr", branch) or "unknown"
            lines.append(branch)
            lines.append(f"  status:      fully merged into {trunk}")
            lines.append(f"  last commit: {last_ago}")
            lines.append(f"  suggestion:  safe to delete → git branch -d {branch}")
            lines.append("")

    if warnings:
        lines.append("DIVERGENCE WARNINGS ───────────────────────────────────────────────")
        lines.append("")
        for w in warnings:
            lines.append(w)
        lines.append("")

    lines.append("SNAPSHOT ──────────────────────────────────────────────────────────")
    lines.append("")
    lines.append(f"  {active_branches} active branch(es)  |  {active_worktrees} worktree(s)  |  {len(stale_branches)} stale  |  {diverged} diverged")
    lines.append("")

    output = "\n".join(lines)
    typer.echo(output, nl=False)

    if write:
        b = ensure_bus()
        (b / "repo-map.md").write_text(output)
        typer.echo(f"# Written to {b}/repo-map.md", err=True)
