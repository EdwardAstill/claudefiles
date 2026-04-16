---
name: github-repo-researcher
description: >
  Investigate GitHub repos — search for repos by topic, analyze how a repo works,
  break down its architecture, and produce a concise technical summary. Use when
  the user says "look at this repo", "how does X work", "find repos for Y",
  "break down owner/repo", "what does this project do", "analyze this GitHub repo",
  or anything involving understanding a GitHub repository they don't already have
  cloned locally. Also use when comparing repos or evaluating whether to adopt
  a library. NOT for operating on the current local repo (codebase-explainer)
  or for GitHub operations like PRs/issues (github-expert).
---

# GitHub Repo Researcher

Quickly investigate any GitHub repository — find it, break it down, understand how
it works. Produces concise technical summaries that answer "what does this do and how?"

## When You Arrive

Figure out which phase you're in:

1. **Discovery** — user wants to find repos ("find me a good X library")
2. **Analysis** — user has a specific repo ("break down owner/repo for me")
3. **Comparison** — user wants to evaluate alternatives ("compare X vs Y")

## Phase 1: Discovery

When the user wants to find repos for a purpose:

```bash
af repo search "query" --sort stars --limit 10
af repo search "query" --language rust --sort stars
```

Present the top candidates with a one-line take on each. Ask which ones to dig into,
or just dig into the top 2-3 if the user seems to want a quick answer.

## Phase 2: Reconnaissance

Start every repo analysis with the one-shot recon:

```bash
af repo recon owner/repo
```

This gives you metadata, file tree, languages, key files, and recent commits in one
call. Read the output carefully — it tells you a lot about what kind of project this
is before you read a single file.

From the recon, identify:
- **What kind of project** — library, framework, CLI tool, web app, API server, etc.
- **Primary language and framework** — from languages + config files
- **Scale** — file count, repo size, contributor activity
- **Entry points** — where execution starts

## Phase 3: Deep Dive

Read the files that matter most, in this order:

### 1. README (if recon didn't include enough)
```bash
af repo read owner/repo README.md
```

### 2. Build/project config — reveals dependencies and project shape
```bash
af repo read owner/repo package.json     # or pyproject.toml, Cargo.toml, etc.
```

### 3. Entry points — where execution starts
Read the entry points identified by recon. These tell you the application's
top-level structure and how it boots up.

```bash
af repo read owner/repo src/main.ts
```

### 4. Core modules — the interesting parts
Based on the tree structure and entry points, identify which directories contain
the core logic (not utils, not tests, not config). Read 2-3 key files from there
to understand the architecture patterns.

### 5. For large/complex repos — use repomix
When you need broader context than individual file reads provide:

```bash
repomix --remote owner/repo --compress --include "src/**"
```

This packs the repo (with function signatures, not bodies) into a single context
file. Use `--include` to focus on the interesting directories.

## Phase 4: Produce the Breakdown

Structure your analysis as:

### What It Does
One paragraph. What problem does this solve, who is it for, what's the value prop.

### Architecture
How the codebase is organized. Name the layers/modules and their responsibilities.
Use a simple diagram if it helps:

```
CLI parser → Command handlers → Core engine → Output formatters
                                    ↓
                              Plugin system
```

### Key Patterns
The 3-5 most important design decisions. Things like:
- How it handles configuration
- The plugin/extension model (if any)
- Data flow through the system
- Error handling strategy
- Testing approach

### Tech Stack
Languages, frameworks, key dependencies, build system — the stuff someone needs
to know before contributing.

### Notable
Anything surprising, clever, or unusual. Also flag any red flags (no tests, stale
dependencies, abandoned maintenance).

## Comparison Mode

When comparing repos, run recon on each, then build a comparison table:

| Aspect | repo-a | repo-b |
|--------|--------|--------|
| Stars / Activity | ... | ... |
| Language | ... | ... |
| Architecture | ... | ... |
| Key trade-off | ... | ... |

Follow the table with a short recommendation based on the user's stated needs.

## Tools

- `af repo recon` — one-shot metadata + tree + key files + commits
- `af repo search` — find repos by keyword
- `af repo tree` — detailed file tree
- `af repo read` — read individual files (handles base64 decoding)
- `repomix --remote` — pack a repo for broad context analysis
- `gh api` — fallback for any GitHub API endpoint not covered above

## Judgement Calls

- **Depth vs speed**: Default to a quick breakdown (recon + 3-5 file reads). Only
  go deeper if the user asks or if the repo is complex enough to warrant it.
- **What to skip**: Tests, CI config, docs — unless the user specifically asks
  about testing or deployment.
- **When to clone**: Almost never. `af repo read` and `repomix --remote` handle
  99% of cases. Only suggest cloning if the user wants to run or modify the code.
- **Large monorepos**: Focus on the directory the user cares about. Use
  `repomix --remote owner/repo --include "packages/the-one-they-care-about/**"`.
