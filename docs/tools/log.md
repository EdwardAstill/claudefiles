# af log

View the skill invocation log.

**Source:** `tools/python/src/af/log.py`

## Usage

```bash
af log                 # last 20 invocations
af log --tail 50       # last 50 entries
af log --skill tdd     # filter to one skill
af log --stats         # frequency table + escalation count
af log --escalations   # only sessions with executor→manager escalation
```

## Options

| Flag | Description |
|------|-------------|
| `--skill <name>`, `-s` | Filter to specific skill |
| `--stats` | Show frequency table sorted by invocation count |
| `--escalations`, `-e` | Only sessions with executor→manager escalation |
| `--tail <n>`, `-n` | Show last N entries (default: 20) |

## Details

Skills are recorded automatically by the `hooks/skill-logger.py` PostToolUse hook whenever a `SKILL.md` is read. Each entry records skill name, session ID, parent skill, and escalation status.

**Log file:** `~/.claude/logs/agentfiles.jsonl`
