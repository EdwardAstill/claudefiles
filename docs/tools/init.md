# af init

Bootstrap `.agentfiles/` in the current project, populate all bus files.

**Source:** `tools/python/src/af/init.py`

## Usage

```bash
af init                # full init
af init --dry-run      # preview what would be created
```

## Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview without creating files |

## What It Does

1. Creates `.agentfiles/` directory
2. Adds `.agentfiles/` to `.gitignore`
3. Generates `context.md`, `versions.md`, `routes.md`, `repo-map.md`
