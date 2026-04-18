# documentation/

Local copies of third-party platform documentation that this system
depends on. Mirrored here so the repo doesn't rely on public URLs
staying stable or being reachable, and so versioning is explicit.

## What goes here

Platform reference docs we read often:

```
documentation/
  claude-code/          Claude Code CLI, skills, subagents, hooks, settings
  anthropic-api/        Anthropic SDK, prompt caching, tool use, batching
  <vendor>/             add as needed — one dir per platform
```

One subdir per platform. Inside, preserve the upstream doc's filename
and drop a `SOURCE.md` recording where it came from and when.

## What does NOT go here

- General knowledge — goes in `../knowledge/`.
- Our own reference docs — live at `../../docs/reference/`.
- External repo summaries — `../projects/`.
- Academic PDFs — `../papers/`.

## How to add

Manual: download and commit, with a one-line note in `SOURCE.md`:

```
2026-04-18  fetched https://code.claude.com/docs/en/skills.md
```

Or via `docs-agent` skill when you need a specific section.

## Consumption

Not queried by `af ak`. Read directly:

```bash
cat research/documentation/claude-code/skills.md
rg "tool use" research/documentation/anthropic-api/
```
