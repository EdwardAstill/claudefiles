---
name: research
description: >
  Category dispatcher for research tasks — use when the user needs information
  before acting but hasn't narrowed down which research primitive fits.
  Trigger phrases: "research this", "help me figure out X", "look into Y",
  "find out about Z", "I need info on W", "what do we know about X",
  "investigate this topic", "before I decide, check", "can you do some digging",
  "what's the current state of X". Routes to docs-agent (exact APIs / versioned
  library docs), research-agent (trade-offs, risks, consensus), codebase-explainer
  (understand an unfamiliar repo), readrun (author interactive docs with
  runnable code), test-taker (answer a question set with strictness levels),
  youtube / terminal-read / web-scraper (the input-specific pulls). Do NOT use
  when the task is already narrowed to one primitive — invoke it directly
  (e.g. "exact API signature of X" → docs-agent). Do NOT use for planning or
  implementation (use planning or executor). Do NOT use to browse the web
  interactively with a real browser (use browser-control).
---

# Research

Routes to the right research skill based on the task.

## Sub-skills

| Skill | Use when |
|-------|----------|
| `docs-agent` | "How do I use X?" — exact API, config option, working example |
| `research-agent` | "Should I use X?" — trade-offs, risks, expert consensus |
| `codebase-explainer` | "How does this codebase work?" — architecture map, execution paths, mental model |
| `readrun` | Create readrun docs — folders of Markdown with runnable Python (Pyodide) and JSX visualisations, served by `rr` |
| `test-taker` | Answer a question set using reference material — rough-guide / strong-guide / only-information strictness, calculations get Python scripts |
| `youtube` | Fetch YouTube transcripts, audio (WAV/MP3), and summaries — `af youtube <cmd>`, native (no external wrapper) |
| `terminal-read` | Capture the user's live terminal scrollback (tmux/screen/stdin) so the agent can Read output that happened outside the chat |
| `web-scraper` | Pull data from a website via pure HTTP (no browser) — fetch HTML/JSON, parse with selectolax, paginate, store as JSONL/CSV/SQLite |
