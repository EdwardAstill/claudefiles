# cf-memory — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

---

## Goal

A per-project SQLite memory store with FTS5 full-text search. Enables Claude to save
decisions, discoveries, and patterns across sessions and retrieve them at task start.
Fills the gap between ephemeral `cf-note` (in-session) and nothing (cross-session).

---

## Problem

`cf-note` writes to `.claudefiles/notes.md` and is cleared between sessions. There is
no durable, searchable record of decisions made, patterns discovered, or context built
up over time working on a project. Claude starts every session with no memory of prior
work beyond what's in the code and git history.

---

## Design

### Storage

Per-project SQLite database at `.claudefiles/memory.db`.

Note: `cf-memory` always writes to/reads from the database — it does not follow the
stdout/--write flag pattern of other cf-* tools. This is intentional: it IS the
persistent store, not a reporting tool.

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

-- Triggers to keep FTS index in sync
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

### CLI interface

```
cf-memory add "text"                 # store a memory, tag=general
cf-memory add --tag decision "text"  # store with explicit tag
cf-memory search "query"             # FTS5 search, top 10 by relevance
cf-memory list                       # last 20 memories, newest first
cf-memory list --tag decision        # filter by tag
cf-memory clear                      # delete all (prompts for confirmation)
```

Output format for `search` and `list`:
```
[42] [decision] 2026-04-10 14:22  Use FTS5 not LIKE — much faster on large stores
[41] [general]  2026-04-09 11:05  Auth middleware rewrite is driven by compliance
```

`search` uses `ORDER BY rank` (FTS5 BM25 ranking) and returns top 10 results.
`list` uses `ORDER BY id DESC LIMIT 20`.

### Implementation

`bin/cf-memory` is a bash script using `sqlite3`. Sources `lib/common.sh` for git root
detection. Creates `.claudefiles/memory.db` and runs the full schema (with IF NOT EXISTS)
on every invocation — safe and idempotent.

---

## Companion Skill: memory-agent

**Location:** `dev-suite/management/meta/memory-agent/SKILL.md`

**Frontmatter description (under 1024 chars):**
```
Use when starting a non-trivial task on a project that has been worked on before, or
when making a significant decision, discovery, or resolving a blocker. Searches
cf-memory for prior context before starting work. Saves decisions, non-obvious
discoveries, and resolved blockers after completing work. Does not activate for simple
one-off tasks.
```

**Save triggers:**
- Architectural or design decisions made during a session
- Non-obvious discoveries (e.g. undocumented API behaviour, hidden constraints)
- Patterns that will apply to future tasks in this project
- Blockers and how they were resolved

**Search triggers:**
- Start of any medium/difficult task — search for relevant prior context
- Before making a decision that may have been made before
- When the user references prior work ("like we did before", "same as last time")

---

## manifest.toml

Add `cf-memory` to `[bin].install`.

Add skill entry:
```toml
[skills.memory-agent]
tools = ["Bash"]
```

Add CLI requirement (sqlite3 is typically pre-installed on Linux/macOS but should be
declared for cf-doctor to check):
```toml
[cli.sqlite3]
manager = "system"
package = "sqlite3"
description = "SQLite CLI — required by cf-memory"
```

---

## management/REGION.md

Add `memory-agent` entry under the meta section.

---

## Files

**Create:**
- `bin/cf-memory`
- `dev-suite/management/meta/memory-agent/SKILL.md`

**Modify:**
- `manifest.toml` — add cf-memory to bin, memory-agent skill entry, sqlite3 cli entry
- `dev-suite/management/REGION.md` — add memory-agent entry
