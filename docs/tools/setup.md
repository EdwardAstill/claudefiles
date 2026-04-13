# af setup

Check tool dependencies for skills installed in the current project.

**Source:** `tools/python/src/af/setup.py`

## Usage

```bash
af setup                                       # check all project skills
af setup --skills "python-expert,rust-expert"  # specific skills
af setup --write                               # save report to .agentfiles/deps.md
```

## Options

| Flag | Description |
|------|-------------|
| `--write` | Save report to `.agentfiles/deps.md` |
| `--skills "<comma,separated>"` | Check specific skills only |

## Details

Reads `manifest.toml` to determine requirements. Shows package manager availability (bun, uv, cargo, rustup) and for each skill lists required agent tools, MCP servers, and CLI tools — marking each as installed or missing with install commands.
