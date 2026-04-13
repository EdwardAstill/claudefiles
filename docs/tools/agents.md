# af agents

Full inventory of Claude Code skills and MCP servers across every scope.

**Source:** `tools/python/src/af/agents.py`

## Usage

```bash
af agents              # full overview, grouped by category
af agents --tree       # deep skill hierarchy tree
af agents --global     # user-level skills only (~/.claude/skills/)
af agents --project    # current project skills only (.claude/skills/)
af agents --available  # in agentfiles but not installed
af agents --mcp        # MCP servers only
```

## Options

| Flag | Description |
|------|-------------|
| `--tree` | Print skill hierarchy as indented tree |
| `--global` | User-level skills only |
| `--project` | Project-level skills only |
| `--available` | Skills in agentfiles repo but not yet installed |
| `--mcp` | MCP servers only |

## Details

Groups skills by category from `manifest.toml`. Shows Claude and Gemini user/project skills, plugins, MCP servers, and CLI tools. Skills not in the manifest appear under `(uncategorized)`.
