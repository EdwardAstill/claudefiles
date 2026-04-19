# Secret Management

API keys and tokens are stored at `~/.claude/secrets` — a plain `KEY=value` file,
chmod 600, never committed to any repo.

Managed by the external [`secrets`](https://github.com/EdwardAstill/secrets) CLI
(install via `uv pip install -e ~/projects/secrets` or `pipx install secrets-cli`).

---

## Storing keys

```bash
secrets set ANNAS_API_KEY <key>
secrets set GITHUB_TOKEN ghp_xxx
secrets set OPENAI_API_KEY sk-xxx
```

Re-running `set` overwrites the existing value.

---

## Using keys

**Inline — single command:**
```bash
ANNAS_API_KEY=$(secrets get ANNAS_API_KEY) anna download <md5>
```

**Inject all secrets then run:**
```bash
secrets exec -- anna download <md5>
secrets exec -- some-tool --flag value
```

**Export everything for the session:**
```bash
eval $(secrets env)
anna download <md5>     # ANNAS_API_KEY already in env
```

---

## All commands

```bash
secrets set KEY value     # store or update
secrets get KEY           # print value (raw, exits 1 if not found)
secrets list              # list key names only — never prints values
secrets remove KEY        # delete
secrets env               # print all as `export KEY=value` lines
secrets exec -- CMD ARGS  # run CMD with all secrets injected as env vars
```

---

## File format

`~/.claude/secrets` is a plain text file:

```
# comments are fine
ANNAS_API_KEY=abc123
GITHUB_TOKEN=ghp_xxx
```

- One `KEY=value` per line
- Lines starting with `#` and blank lines are ignored
- Values are stored as-is — no quoting needed
- chmod 600 is enforced on every write

---

## What goes here

| Key | Used by |
|-----|---------|
| `ANNAS_API_KEY` | `anna download`, `anna get`, `anna batch` |

Add more as needed. Skills that need a key should document it in their SKILL.md
and read it via `secrets get KEY` or `secrets exec`.

---

## What doesn't go here

- Claude Code's own API key — managed by Claude Code in `.credentials.json`
- Project-specific secrets that belong in a project `.env` — use `direnv` or your
  project's own secrets management for those
