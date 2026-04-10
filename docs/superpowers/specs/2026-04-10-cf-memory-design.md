# cf-memory — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

**Depends on:** Tool management migration (bin/ → tools/python/)

---

## Goal

A per-project SQLite memory store with FTS5 full-text search. Enables Claude to save
decisions, discoveries, and patterns across sessions and retrieve them at task start.

---

## Design

### Implementation

New Python module: `tools/python/src/cf/memory.py`

Uses `sqlite3` from the Python standard library — no extra dependency.

Registered in `main.py`:
```python
from cf import memory
app.add_typer(memory.app, name="memory")
```

Entry in `tools/tools.json`:
```json
{
  "name": "memory",
  "type": "internal",
  "package": "cf",
  "description": "Per-project SQLite memory store with full-text search",
  "usage": "cf memory <add|search|list|clear> [args]"
}
```

### Storage

Per-project SQLite database at `.claudefiles/memory.db`. Always writes to/reads from
the database — does not follow the `--write` flag pattern (it IS the persistent store).

### Schema

```sql
CREATE TABLE IF NOT EXISTS memories (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tag     TEXT    NOT NULL DEFAULT 'general',
    body    TEXT    NOT NULL,
    created TEXT    NOT NULL  -- ISO8601: datetime('now')
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
    USING fts5(body, content=memories, content_rowid=id);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, body) VALUES (new.id, new.body);
END;
CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, body) VALUES ('delete', old.id, old.body);
END;
CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, body) VALUES ('delete', old.id, old.body);
    INSERT INTO memories_fts(rowid, body) VALUES (new.id, new.body);
END;
```

Schema is created on first use (IF NOT EXISTS — idempotent).

### CLI interface

```
cf memory add "text"                 # store, tag=general
cf memory add --tag decision "text"  # store with explicit tag
cf memory search "query"             # FTS5 BM25 search, top 10 by rank
cf memory list                       # last 20, newest first
cf memory list --tag decision        # filter by tag
cf memory clear                      # delete all (prompts confirmation)
```

Output format:
```
[42] [decision] 2026-04-10 14:22  Use FTS5 not LIKE — much faster on large stores
[41] [general]  2026-04-09 11:05  Auth middleware rewrite is driven by compliance
```

`search` uses `ORDER BY rank` (FTS5 BM25), returns top 10.
`list` uses `ORDER BY id DESC LIMIT 20`.

---

## Companion Skill: memory-agent

**Location:** `skills/management/meta/memory-agent/SKILL.md`

**Frontmatter description (under 1024 chars):**
```
Use when starting a non-trivial task on a project that has been worked on before, or
when making a significant decision, discovery, or resolving a blocker. Searches
cf memory for prior context before starting work. Saves decisions, non-obvious
discoveries, and resolved blockers after completing work. Does not activate for simple
one-off tasks.
```

**Save triggers:** architectural/design decisions, non-obvious discoveries, patterns
that apply to future tasks, blockers and resolutions.

**Search triggers:** start of medium/difficult tasks, before revisiting decisions,
when user references prior work.

---

## manifest.toml

Add skill entry (Claude Code tool permissions):
```toml
[skills.memory-agent]
tools = ["Bash"]
```

---

## skills/management/REGION.md

Add `memory-agent` entry under the meta section.

---

## Files

**Create:**
- `tools/python/src/cf/memory.py`
- `skills/management/meta/memory-agent/SKILL.md`

**Modify:**
- `tools/python/src/cf/main.py` — register memory sub-app
- `tools/tools.json` — add memory entry
- `manifest.toml` — add memory-agent skill entry
- `skills/management/REGION.md` — add memory-agent entry
