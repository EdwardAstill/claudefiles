# Secret Management

API keys and tokens are stored at `~/.claude/secrets` — a plain `KEY=value` file,
chmod 600, never committed to any repo.

---

## Storing keys

```bash
af secrets set ANNAS_API_KEY <key>
af secrets set GITHUB_TOKEN ghp_xxx
af secrets set OPENAI_API_KEY sk-xxx
```

Re-running `set` overwrites the existing value.

---

## Using keys

**Inline — single command:**
```bash
ANNAS_API_KEY=$(af secrets get ANNAS_API_KEY) anna download <md5>
```

**Inject all secrets then run:**
```bash
af secrets exec -- anna download <md5>
af secrets exec -- some-tool --flag value
```

**Export everything for the session:**
```bash
eval $(af secrets env)
anna download <md5>     # ANNAS_API_KEY already in env
```

---

## All commands

```bash
af secrets set KEY value     # store or update
af secrets get KEY           # print value (raw, exits 1 if not found)
af secrets list              # list key names only — never prints values
af secrets remove KEY        # delete
af secrets env               # print all as `export KEY=value` lines
af secrets exec -- CMD ARGS  # run CMD with all secrets injected as env vars
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
and read it via `af secrets get KEY` or `af secrets exec`.

---

## What doesn't go here

- Claude Code's own API key — managed by Claude Code in `.credentials.json`
- Project-specific secrets that belong in a project `.env` — use `direnv` or your
  project's own secrets management for those
