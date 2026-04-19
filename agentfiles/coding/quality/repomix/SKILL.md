---
name: repomix
description: >
  Use when packing a whole repo or directory into a single AI-friendly
  file for LLM context. Trigger phrases: "pack this repo for an AI",
  "dump the codebase into one file", "repomix this directory", "audit
  this remote repo without cloning", "compress the codebase for
  context", "feed this repo to a model", "token-count tree before I
  include", "generate a single-file snapshot of the project", "strip
  impl with --compress", "build a minimal context bundle". Uses
  repomix with --compress (Tree-sitter, ~70% token reduction),
  --remote for GitHub repos, and include/ignore filters. Do NOT use
  for explaining a codebase the user wants to understand themselves
  (use codebase-explainer), scraping arbitrary websites (use
  web-scraper), or converting a single file on disk (use
  file-converter).
---

Pack repo into single file for AI context. Use `--compress` to strip impl details, keep structure.

## Core commands

```bash
# Current directory
repomix

# Specific path
repomix path/to/dir

# Remote GitHub repo (no clone needed)
repomix --remote owner/repo
repomix --remote owner/repo --include "src/**/*.ts"

# Compressed — ~70% token reduction (Tree-sitter strips fn bodies, keeps signatures)
repomix --compress

# See token distribution before deciding what to include
repomix --token-count-tree 1000

# Target specific files
repomix --include "src/**" --ignore "**/*.test.*,**/node_modules"

# Strip comments too (more reduction)
repomix --compress --remove-comments
```

## Output formats

| Flag | Use case |
|------|----------|
| (default) | XML — best for Claude, structured headers |
| `--style markdown` | Human-readable code blocks |
| `--style json` | Programmatic processing |

## Token reduction strategy

1. Run `repomix --token-count-tree 1000` — see which dirs are expensive
2. Use `--include` to target only relevant paths
3. Add `--compress` — keeps class/fn signatures, drops bodies
4. Add `--remove-comments` for extra reduction
5. Use `--split-output 1mb` if output still too large

## Config file

Save defaults in `repomix.config.json` at repo root:
```json
{
  "output": { "style": "xml", "compress": true, "removeComments": false },
  "ignore": { "patterns": ["**/*.test.*", "dist/**", ".env*"] }
}
```

## When to use

- Feeding unfamiliar codebase to AI for audit/refactor
- Analyzing remote repo without cloning
- Pre-task context compression on large projects
- Passing codebase context to subagents
