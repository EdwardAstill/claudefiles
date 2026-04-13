---
name: research
description: >
  Category dispatcher for research tasks. Use when you need information before
  acting. Routes to docs-agent (exact APIs, library usage, versioned docs),
  research-agent (trade-offs, consensus, risks), codebase-explainer (understand
  an unfamiliar codebase), test-taker (answer a question set using reference
  material with configurable strictness).
---

# Research

Routes to the right research skill based on the task.

## Sub-skills

| Skill | Use when |
|-------|----------|
| `docs-agent` | "How do I use X?" — exact API, config option, working example |
| `research-agent` | "Should I use X?" — trade-offs, risks, expert consensus |
| `codebase-explainer` | "How does this codebase work?" — architecture map, execution paths, mental model |
| `note-taker` | Create markdown notes or interactive lessons — plain or readrun-compatible with runnable code blocks |
| `test-taker` | Answer a question set using reference material — rough-guide / strong-guide / only-information strictness, calculations get Python scripts |
