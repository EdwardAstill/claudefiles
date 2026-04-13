# af worktree

Create a git worktree and open a terminal with Claude Code.

**Source:** `tools/python/src/af/worktree.py`

## Usage

```bash
af worktree <branch-name> [base-branch]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `branch` | New branch name (required) |
| `base` | Base branch (default: main) |

## Details

Creates a worktree at `<parent>/<repo>-<branch>`, allocates a free port, prints a `WORKTREE CONTEXT` block, and attempts to open a terminal via the `$TERMINAL` environment variable.
