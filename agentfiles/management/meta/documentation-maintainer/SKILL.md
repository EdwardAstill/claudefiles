---
name: documentation-maintainer
description: >
  Use when adding, removing, or renaming skills, when docs feel stale, when the
  user asks to update or check documentation, or after any structural change to
  the skill hierarchy. Triggers on: "update the docs", "check documentation",
  "docs are stale", "add this to the README", "sync the skill tree".
---

# Documentation Maintainer

Keep project documentation consistent with the actual codebase. Documentation
rots when skills are added, renamed, or removed without updating the docs that
reference them.

## When to Use

- After adding, removing, or renaming a skill
- After adding a new `af` CLI subcommand
- When the user says docs are wrong, stale, or incomplete
- As a final step after structural changes to the skill hierarchy
- Periodically (monthly) alongside `af log review`

## The Checklist

Run through these in order. Skip any that don't apply to the change you made.

### 1. Skill registry files

These files list all skills — they must stay in sync:

| File | What it contains | How to check |
|------|-----------------|--------------|
| `README.md` (Skills section) | Skill tables grouped by category with counts | Compare against actual SKILL.md files |
| `docs/reference/skills.md` | Complete catalog with invocation names | Compare against actual SKILL.md files |
| `docs/skill-tree.md` | ASCII hierarchy diagram | Compare against directory structure |
| Category `REGION.md` files | Per-category skill lists | Run `af check` |

**Quick verification:**

```bash
# Count actual leaf skills (directories with SKILL.md that have no child SKILL.md)
find agentfiles -name SKILL.md -exec sh -c \
  'dir=$(dirname "{}"); [ -z "$(find "$dir" -mindepth 2 -name SKILL.md 2>/dev/null)" ] && basename "$dir"' \
  \; | sort | wc -l

# Run the built-in checker
af check
```

If the count doesn't match what README.md says, update the docs.

### 2. CLI documentation

When a new `af` subcommand is added:

| File | What to update |
|------|---------------|
| `docs/tools/<command>.md` | Create tool doc (usage, options, examples) |
| `docs/tools/README.md` | Add entry to index |
| `docs/reference/cli.md` | Add to command reference table |
| `README.md` (CLI section) | Add if it's a user-facing command |

**Quick verification:**

```bash
# List registered subcommands from source
grep -oP '"(\w[\w-]*)"' tools/python/src/af/main.py | sort

# List documented tools
ls docs/tools/*.md | sed 's|.*/||;s|\.md||' | sort

# Diff
diff <(grep -oP '"(\w[\w-]*)"' tools/python/src/af/main.py | tr -d '"' | sort) \
     <(ls docs/tools/*.md | sed 's|.*/||;s|\.md||' | grep -v README | grep -v index | sort)
```

### 3. Reference docs

When changing logging, hooks, install, orchestration, or workflows:

| File | Covers |
|------|--------|
| `docs/reference/logging.md` | Log files, `af log` commands, review cycle |
| `docs/reference/install.md` | Install system, scopes, hooks |
| `docs/reference/orchestration.md` | Executor/manager routing |
| `docs/reference/workflows.md` | End-to-end workflow traces |

### 4. README.md Docs table

The Docs table at the bottom of README.md should list every file in `docs/reference/`.
Cross-check and add any missing entries.

## Style rules

- **No orphan docs** — every doc must be reachable from README.md or another doc
- **Counts must be accurate** — if README says "Skills (39)" it must be 39
- **Names must match** — use the skill's `name` field from frontmatter, not the directory name
- **One source of truth per fact** — if the skill count is in README and skills.md, they must agree
- **Keep it terse** — tool docs should be scannable, not essays

## After updating

Run `af check` to verify REGION.md entries are correct. Then grep for the old
name/count if you renamed or removed something:

```bash
# Find stale references to a removed skill
grep -r "old-skill-name" docs/ README.md agentfiles/
```
