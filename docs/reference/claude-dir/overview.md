# ~/.claude/ Directory Reference

`~/.claude/` is Claude Code's home directory. It has two zones: files Claude Code
manages itself, and files claudefiles manages.

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

## claudefiles managed

| Path | What it is | Managed by | Doc |
|------|------------|------------|-----|
| `skills/` | Installed skills → symlink into dotfiles | `install.sh` | [install](../install.md) |
| `logs/claudefiles.jsonl` | Skill invocation log | `hooks/skill-logger.py` | [cli](../cli.md#cf-log) |
| `data/` | Persistent data store for `cf index`/`cf search` | `cf index` | [cli](../cli.md#cf-index) |
| `secrets` | API keys, chmod 600 | `cf secrets` | [secrets](./secrets.md) |

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
cf agents                            # installed skills
cf log --stats                       # skill usage
cf search --list                     # indexed data sources
cf secrets list                      # stored secret key names (not values)
ls ~/.claude/data/                   # data store contents
```

## Safe to edit

- `~/.claude/settings.json` — add hooks, change model, toggle plugins
- `~/.claude/secrets` — use `cf secrets set/remove` rather than editing directly
- `~/.claude/data/` — rebuild with `cf index` if stale
