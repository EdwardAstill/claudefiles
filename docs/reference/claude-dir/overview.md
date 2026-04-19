# ~/.claude/ Directory Reference

`~/.claude/` is Claude Code's home directory. It has two zones: files Claude Code
manages itself, and files agentfiles manages.

---

## Claude Code managed

Leave these alone unless you know what you're doing.

| Path | What it is |
|------|------------|
| `settings.json` | Main config — model, enabled plugins, hooks, permissions |
| `.credentials.json` | API auth token (chmod 600) |
| `history.jsonl` | Full conversation history |
| `file-history/` | Per-file edit history, one dir per file Claude has touched |
| `projects/` | Per-project conversation state, keyed by path hash |
| `sessions/` | Active session state |
| `session-env/` | Shell environment snapshots per session |
| `shell-snapshots/` | Shell state at session start |
| `tasks/` | Background task tracking |
| `agents/` | Agent configuration |
| `plugins/` | Marketplace plugin installs |
| `plans/` | Plan files |
| `agent-memory/` | Claude's persistent memory files (the auto-memory system) |
| `cache/` | General cache |
| `paste-cache/` | Clipboard paste cache |
| `backups/` | Auto-backups |
| `telemetry/` | Usage telemetry |
| `.session-stats.json` | Session statistics |
| `mcp-needs-auth-cache.json` | MCP auth state |

---

## agentfiles managed

| Path | What it is | Managed by | Doc |
|------|------------|------------|-----|
| `skills/` | Installed skills → symlink into dotfiles | `af install` | [install](../install.md) |
| `logs/agentfiles.jsonl` | Skill invocation log (automated) | `hooks/skill-logger.py` | [logging](../logging.md) |
| `logs/observations.md` | Qualitative notes — patterns, routing misses | manual | [logging](../logging.md) |
| `logs/backlog.md` | Actionable improvement items | manual | [logging](../logging.md) |
| `logs/.sessions/` | Per-session state for logger (auto-cleaned) | `hooks/skill-logger.py` | — |
| `data/` | Persistent data store for `af index`/`af search` | `af index` | [cli](../cli.md#af-index) |
| `secrets` | API keys, chmod 600 | external [`secrets`](https://github.com/EdwardAstill/secrets) CLI | [secrets](./secrets.md) |

---

## Dotfiles symlinks

| Path | Points to |
|------|-----------|
| `skills/` | `~/dotfiles/app-configuration/claude/.claude/skills/` |
| `.mcp.json` | `~/dotfiles/app-configuration/claude/.claude/.mcp.json` |
| `image-cache/` | `~/dotfiles/app-configuration/claude/.claude/image-cache/` |

Changes to MCP config or skills go through the dotfiles repo, not directly in `~/.claude/`.

---

## Safe to inspect

```bash
cat ~/.claude/settings.json          # current config
af agents                            # installed skills
af log --stats                       # skill usage
af search --list                     # indexed data sources
secrets list                         # stored secret key names (not values)
ls ~/.claude/data/                   # data store contents
```

## Safe to edit

- `~/.claude/settings.json` — add hooks, change model, toggle plugins
- `~/.claude/secrets` — use `secrets set/remove` (external CLI) rather than editing directly
- `~/.claude/data/` — rebuild with `af index` if stale
