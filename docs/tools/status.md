# af status

Full repo branch/worktree topology — trunk, branches, commits, ahead/behind, dirty state.

**Source:** `tools/python/src/af/status.py`

## Usage

```bash
af status              # print to stdout
af status --write      # also save to .agentfiles/repo-map.md
```

## Options

| Flag | Description |
|------|-------------|
| `--write` | Save output to `.agentfiles/repo-map.md` |

## Output

- Trunk branch detection (main/master)
- Remote tracking status
- Worktree list with allocated ports
- Stale branches
- Active branches with diff summary
- Divergence warnings
