# Secret Management

API keys and tokens are stored at `~/.claude/secrets` — a plain `KEY=value` file,
chmod 600, never committed to any repo.

---

## Storing keys

```bash
cf secrets set ANNAS_API_KEY <key>
cf secrets set GITHUB_TOKEN ghp_xxx
cf secrets set OPENAI_API_KEY sk-xxx
```

Re-running `set` overwrites the existing value.

---

## Using keys

**Inline — single command:**
```bash
ANNAS_API_KEY=$(cf secrets get ANNAS_API_KEY) anna download <md5>
```

**Inject all secrets then run:**
```bash
cf secrets exec -- anna download <md5>
cf secrets exec -- some-tool --flag value
```

**Export everything for the session:**
```bash
eval $(cf secrets env)
anna download <md5>     # ANNAS_API_KEY already in env
```

---

## All commands

```bash
cf secrets set KEY value     # store or update
cf secrets get KEY           # print value (raw, exits 1 if not found)
cf secrets list              # list key names only — never prints values
cf secrets remove KEY        # delete
cf secrets env               # print all as `export KEY=value` lines
cf secrets exec -- CMD ARGS  # run CMD with all secrets injected as env vars
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
and read it via `cf secrets get KEY` or `cf secrets exec`.

---

## What doesn't go here

- Claude Code's own API key — managed by Claude Code in `.credentials.json`
- Project-specific secrets that belong in a project `.env` — use `direnv` or your
  project's own secrets management for those
