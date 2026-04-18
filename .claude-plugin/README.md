# agentfiles — Claude Code plugin manifest

This directory turns the repository into a Claude Code plugin and a single-plugin
marketplace. Two manifests live here:

- `plugin.json` — the plugin manifest consumed by Claude Code when the repo is
  loaded via `claude --plugin-dir` or installed from the marketplace.
- `marketplace.json` — the marketplace manifest so the repo can also be added
  with `/plugin marketplace add EdwardAstill/agentfiles`, after which the plugin
  installs with `/plugin install agentfiles@agentfiles`.

## What the plugin ships

| Component | Source path | Count |
|-----------|-------------|-------|
| Skills    | `skills/` (curated symlinks into `agentfiles/<category>/<skill>/`) | 54 |
| Agents    | `agentfiles/agents/*.md` | 10 |
| Hooks     | `hooks/hooks.json` (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop, PermissionRequest, Notification) | 7 events |

The full set of 73 `SKILL.md` files in the repo includes category-level index
skills (e.g. `agentfiles/planning/SKILL.md`) that are structural, not
slash-command surfaces. The plugin intentionally exposes only the 54 curated
leaf skills mirrored under `skills/`.

## What the plugin does *not* bundle

- The `af` CLI. It lives under `tools/python/` and installs via
  `uv tool install -e tools/python/`. Several skills (e.g. `executor`,
  `agentfiles-manager`, `using-agentfiles`) expect `af` on `PATH`.
- The project-level `.agentfiles/` communication bus. Created per-project by
  `af init`.
- MCP servers, LSP servers, monitors — not used by this plugin.

## Local development

Test changes without installing:

```bash
claude --plugin-dir /home/eastill/projects/agentfiles
```

Reload after edits:

```
/reload-plugins
```

## Notes on directory layout

- `skills/` at the repo root is a flat directory of symlinks into the canonical
  `agentfiles/<category>/<skill>/` tree. Claude Code preserves symlinks in the
  plugin cache and resolves them at runtime, so this layout works when the
  plugin is installed from a marketplace.
- `hooks/hooks.json` already references scripts via `${CLAUDE_PLUGIN_ROOT}`,
  which is the one substitution pattern Claude Code requires for portable
  plugin hook commands.
- `agents` is declared with a custom path because agent markdown lives in
  `agentfiles/agents/`, not the default `agents/` at the plugin root.
