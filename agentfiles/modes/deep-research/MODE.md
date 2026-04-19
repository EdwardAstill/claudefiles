---
name: deep-research
description: >
  Force multi-source fanout on research questions. Require 3+ sources cited
  inline, prefer primary docs (context7) over web search, never answer from
  memory alone when the question is factual and freshness-sensitive.
category: research
levels: [on]
reminder: >
  deep-research: fan out across 3+ sources in parallel, cite each inline,
  prefer primary docs (context7) over general web search, do not answer
  from memory alone. If the question is about a library/framework/API,
  fetch current docs before responding.
conflicts_with: []
auto_clarity: false
---

# deep-research

Research questions get researched. This mode forces the agent out of
"answer from memory" mode and into "consult primary sources, cite, and
cross-check" mode.

## When to use

- Questions about library APIs, framework behavior, CLI tools, or cloud
  services where training data may be stale.
- Factual questions where freshness matters (releases, versions, CVEs,
  current best practices).
- Comparative questions ("X vs Y") where a single-source answer biases
  the result.

## Rules

- **Fan out.** Launch 3+ parallel source lookups before composing the
  answer (context7, WebFetch, WebSearch, local knowledge base).
- **Cite inline.** Every non-obvious factual claim gets a source. URLs
  for web/docs; file paths for local sources.
- **Primary over secondary.** Library docs beat blog posts. Official
  release notes beat summaries. Use context7 first for library
  questions.
- **No memory-only answers** on freshness-sensitive topics. If you only
  have training-data knowledge, say so explicitly and fetch.
- **Cross-check.** If two sources disagree, surface the disagreement
  rather than picking one silently.

## When to ignore

- Pure code generation from well-specified requirements (no facts to
  check).
- Refactoring or debugging existing code in the repo.
- General programming concepts ("what is a closure") — memory is fine.

## Persistence

State file: `~/.claude/modes/deep-research`. The `UserPromptSubmit` hook
re-injects the reminder each turn. Control:

```bash
af mode on deep-research
af mode off deep-research
af mode status
```

## Interaction with other modes

- Stacks cleanly with `verify-first` (research + verify = rigorous).
- Stacks with `token-efficient` or `caveman` — citations stay, prose
  around them compresses.
- Does not conflict with any existing mode.
