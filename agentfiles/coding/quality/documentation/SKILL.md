---
name: documentation
description: >
  Use when the primary output is documentation prose — READMEs, API
  docs, architecture guides, ADRs, changelogs, migration guides, or
  module-level comments. Trigger phrases: "write docs for this", "update
  the README", "document this API", "add a changelog entry", "write a
  migration guide", "this needs better docs", "write an ADR for this
  decision", "document how this module works", "rewrite this section
  clearer", "CONTRIBUTING.md for this repo". Do NOT use for OpenAPI
  specs of an API being designed (use api-architect), design docs about
  service topology (use system-architecture-expert), or the code itself
  (use the relevant language expert).
---

# Documentation

Write documentation that people actually read. Good docs are scannable, accurate,
and maintained. Bad docs are worse than no docs — they teach the wrong thing.

## Principles

1. **Write for the reader, not the author.** What does someone need to know to use this? Not what was interesting to build.
2. **Scannable first, detailed second.** Headings, tables, and code blocks before prose. Readers scan — let them find what they need.
3. **One source of truth.** If something is documented in two places, one will be wrong. Cross-reference instead of duplicating.
4. **Examples over explanations.** A working code example teaches faster than three paragraphs.
5. **Keep it current or delete it.** Stale docs actively harm. If you can't maintain it, don't write it.

## Before Writing

1. **Check what exists.** Read existing docs first. You may need to update, not create.
2. **Identify the audience.** New user? Contributor? API consumer? This determines depth and tone.
3. **Pick the right format.** Not everything needs a markdown file:

| Need | Format |
|------|--------|
| How to get started | README section or quickstart guide |
| API contract | OpenAPI spec or generated API docs |
| Architecture decisions | ADR (Architecture Decision Record) |
| What changed | CHANGELOG entry |
| How to migrate | Migration guide with before/after |
| Why we chose X | ADR or design doc |
| How a module works | Code comments + short doc at module level |
| How to contribute | CONTRIBUTING.md |

## README Structure

A README should answer these questions in order:

1. **What is this?** — one sentence
2. **How do I install it?** — copy-pasteable commands
3. **How do I use it?** — the simplest working example
4. **What are the options?** — reference table or link to full docs
5. **How do I contribute?** — or link to CONTRIBUTING.md

```markdown
# Project Name

One-line description of what this does.

## Install

\`\`\`bash
npm install project-name
\`\`\`

## Usage

\`\`\`javascript
import { thing } from 'project-name'
const result = thing('input')
\`\`\`

## API

| Function | Description |
|----------|-------------|
| `thing(input)` | Does the thing |

## License

MIT
```

**Anti-patterns:**
- Badges wall before the description
- "Table of Contents" for a 50-line README
- Installation instructions that assume a specific OS without saying so
- "TODO: add docs" committed to main

## API Documentation

For each endpoint or public function:

```markdown
### `functionName(param1, param2, options?)`

Brief description of what it does.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `param1` | `string` | yes | What this is |
| `param2` | `number` | yes | What this is |
| `options.flag` | `boolean` | no | Default: `false`. What it does |

**Returns:** `Promise<Result>` — description

**Example:**

\`\`\`typescript
const result = await functionName('hello', 42, { flag: true })
\`\`\`

**Errors:**
- Throws `ValidationError` if param1 is empty
```

## Changelogs

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [1.2.0] - 2026-04-14

### Added
- New `--format` flag for JSON output

### Fixed
- Crash when input file is empty (#123)

### Changed
- Default timeout increased from 30s to 60s
```

Group by: Added, Changed, Deprecated, Removed, Fixed, Security. Most recent version first.

## Architecture Decision Records (ADRs)

Short documents that capture why a decision was made:

```markdown
# ADR-001: Use PostgreSQL over SQLite

## Status
Accepted

## Context
We need a database that supports concurrent writes from multiple workers.

## Decision
Use PostgreSQL.

## Consequences
- Need to run a database server (added operational complexity)
- Get concurrent write support and full SQL
- Team already has PostgreSQL experience
```

Store in `docs/decisions/` or `docs/adr/`. Number sequentially.

## Migration Guides

Structure as before/after with exact steps:

```markdown
# Migrating from v1 to v2

## Breaking changes

### `createUser()` now requires an email

**Before (v1):**
\`\`\`javascript
createUser({ name: 'Alice' })
\`\`\`

**After (v2):**
\`\`\`javascript
createUser({ name: 'Alice', email: 'alice@example.com' })
\`\`\`

### Configuration file moved

\`\`\`bash
mv .config/old-name.json .config/new-name.json
\`\`\`
```

## Review Checklist

When reviewing existing docs:

- [ ] **Accurate?** Does it match the current code? Run any commands it shows.
- [ ] **Complete?** Are there features/options not mentioned?
- [ ] **Scannable?** Can someone find what they need in 10 seconds?
- [ ] **Examples work?** Copy-paste every code example and run it.
- [ ] **Links work?** Check internal and external links.
- [ ] **No duplication?** Is the same thing documented in two places?
- [ ] **Right audience?** Does the depth match who reads this?
