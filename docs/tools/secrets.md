# af secrets

Manage API keys and tokens stored at `~/.claude/secrets`.

**Source:** `tools/python/src/af/secrets.py`

## Usage

```bash
af secrets set ANNAS_API_KEY <key>     # store or update
af secrets get ANNAS_API_KEY           # print value (raw, no label)
af secrets list                        # key names only (never values)
af secrets remove ANNAS_API_KEY        # delete
af secrets env                         # print all as export KEY=value
af secrets exec -- <cmd> [args]        # run command with secrets injected
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `set <key> <value>` | Store or update a secret |
| `get <key>` | Print secret value |
| `list` | List key names only |
| `remove <key>` | Delete a secret |
| `env` | Print all as `export KEY=value` lines |
| `exec -- <cmd> [args]` | Run command with secrets as env vars |

## Examples

```bash
# Inline injection (one-off):
ANNAS_API_KEY=$(af secrets get ANNAS_API_KEY) anna download <md5>

# Inject all secrets then run:
af secrets exec -- anna download <md5>

# Export everything for the session:
eval $(af secrets env)
```

## File Format

Stored at `~/.claude/secrets` with `chmod 600`. Never in any repo or project directory.

```
# comments are ignored
ANNAS_API_KEY=abc123
GITHUB_TOKEN=ghp_xxx
```
