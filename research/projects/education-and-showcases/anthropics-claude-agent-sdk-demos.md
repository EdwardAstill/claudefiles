# anthropics/claude-agent-sdk-demos

**URL:** https://github.com/anthropics/claude-agent-sdk-demos
**Stars:** ~2,200 | **Type:** Official SDK demo collection (TypeScript-first)

## What It Is

Anthropic's reference demos for the Claude Agent SDK — the programmatic harness that exposes Claude Code's agent loop, tool use, and session machinery as a library. Eight runnable demos, each isolating one pattern:

- **Hello World / Hello World V2** — minimum viable agent loop and the V2 Session API for multi-turn persistence
- **Research Agent** — multi-agent orchestration: spawns parallel researcher subagents, synthesizes a report
- **Email Agent** — IMAP integration with agentic inbox search and assisted replies
- **Excel Demo** — spreadsheet manipulation as a tool-use case study
- **AskUserQuestion Previews** — branding assistant rendering visual HTML preview cards mid-conversation
- **Resume Generator** — web-search → assembly → `.docx` output pipeline
- **Simple Chat App** — React + Express UI with streaming responses

Bun-first runtime, ~89% TypeScript with a Python sidecar for select demos.

---

## What It Does Well

- **One pattern per demo** — easy to read, easy to lift; each demo answers a single question (how do I do X with the SDK)
- **Plan mode and subagent orchestration shown concretely** — the research agent demonstrates spawning specialized researchers in parallel and merging their output, which is the canonical multi-agent pattern
- **Session API V2 coverage** — multi-turn conversation persistence is a 2025+ SDK addition and the demos already reflect it
- **Visual UI previews** — `AskUserQuestion` with HTML preview cards is a non-obvious capability most users don't realize the SDK exposes

---

## Weaknesses

- **Local-dev only** — the README explicitly disclaims production use; no auth/secret-management story
- **TypeScript-heavy** — Python users get a smaller slice (the Python SDK has its own `examples/` directory, not unified here)
- **Demo overlap with `anthropic-quickstarts`** — some patterns (autonomous coding, computer use) live in the quickstarts repo instead, which is mildly confusing for newcomers

---

## Take

The canonical reference for Agent SDK patterns. The **Research Agent** demo is the most relevant to agentfiles — it implements parallel subagent dispatch and result synthesis, which is the same pattern agentfiles approximates via its `research-agent` skill. Worth diffing the two implementations to see whether agentfiles' synthesis step (currently markdown-template-driven) could be replaced or augmented by an SDK-style programmatic synthesizer.
