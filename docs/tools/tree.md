# af tree

Show folder structure as a layered tree.

**Source:** `tools/python/src/af/tree.py`

## Usage

```bash
af tree [PATH]                 # default: cwd
af tree --depth 3              # limit depth
af tree --json                 # JSON output
af tree --no-ignore            # include .git, node_modules, etc.
af tree --write                # save to .agentfiles/tree.json
```

## Arguments

| Argument | Description |
|----------|-------------|
| `path` | Directory to scan (default: cwd) |

## Options

| Flag | Description |
|------|-------------|
| `--depth <d>`, `-d` | Max depth (0 = unlimited) |
| `--json`, `-j` | Output as JSON |
| `--no-ignore` | Don't skip ignored directories |
| `--write` | Save to `.agentfiles/tree.json` |

## Ignored by Default

`.git`, `__pycache__`, `node_modules`, `.venv`, `venv`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `dist`, `build`, `.egg-info`, `.tox`, `.next`, `target`
