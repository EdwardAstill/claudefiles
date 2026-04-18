# thedotmack/claude-mem

**URL:** https://github.com/thedotmack/claude-mem

**One-line:** A Claude Code plugin that auto-captures session tool-use, AI-compresses it into semantic observations, and reinjects relevant context into future sessions via hooks + a local worker service.

## How it works

Claude-mem installs as a Claude Code plugin (`npx claude-mem install` or `/plugin install claude-mem`) that wires into six lifecycle hooks: `Setup`, `SessionStart`, `UserPromptSubmit`, `PreToolUse` (matcher: `Read`), `PostToolUse` (matcher: `*`), `Stop`, and `SessionEnd`. Each hook shells out to a Node/Bun runner that calls a long-lived local worker service on `http://localhost:37777`. The worker (managed by Bun, auto-installed if missing) exposes an HTTP API, a web viewer UI, and ten search endpoints. On `PostToolUse` every tool call is captured as an "observation"; on `Stop`/`SessionEnd` those observations are summarized; on `SessionStart` the worker injects prior context; on `PreToolUse` for `Read` it attaches relevant file context.

Storage is a hybrid of SQLite (sessions, raw observations, summaries, FTS5 keyword search) plus a Chroma vector database (managed by `uv`, also auto-installed) for semantic retrieval. Retrieval uses a deliberately **token-efficient 3-layer workflow** exposed as MCP tools: `search` returns a compact index (~50–100 tokens/result), `timeline` fetches chronological neighbors around an ID, and `get_observations` fetches full bodies only for the filtered IDs (~500–1000 tokens each) — the README claims ~10x token savings over naive dump-everything retrieval.

Additional surfaces: a `mem-search` skill for natural-language queries with progressive disclosure, a "Claude Desktop" search skill, `<private>` tags to exclude sensitive content, citations by observation ID (`http://localhost:37777/api/observation/{id}`), a "beta channel" with an experimental "Endless Mode" (biomimetic memory architecture for long sessions), and mode/language config via `CLAUDE_MEM_MODE` (e.g. `code--zh`, `code--ja`).

## Notable patterns

- **Hook-driven capture at tool granularity.** Every `PostToolUse` becomes a stored observation — much finer-grained than session-log post-hoc analysis.
- **Progressive disclosure as a retrieval contract.** `search` → `timeline` → `get_observations` is an explicit, named three-layer API the agent is told to follow, not a convention.
- **Dual index: FTS5 + vector (Chroma).** Keyword and semantic search combined; either-or is the usual mistake.
- **Worker service model.** A single local daemon on a known port instead of spawning a script per hook — amortizes model/index load.
- **Stable observation IDs as citations.** Observations get IDs that Claude can reference inline, with a browser endpoint for inspection.
- **Privacy is a first-class primitive.** `<private>` tag opt-out baked into the capture layer, not an afterthought.
- **Multi-host plugin packaging.** Same core ships for Claude Code, Gemini CLI, OpenCode, and OpenClaw from one plugin manifest.

## Take-aways for agentfiles

**Verdict: mostly skip, steal two ideas.** Agentfiles already solves the same problem with a different philosophy — `research/knowledge/` is human-curated distilled knowledge, `.agentfiles/notes.md` captures intra-session state, and `af log review` + the `retrospective` skill turn raw session logs into durable lessons. That pipeline produces higher-signal artifacts than claude-mem's auto-observation firehose, and it keeps the data as reviewable markdown in the repo rather than in an opaque SQLite/Chroma pair behind a daemon. Our data is grep-able, diffable, PR-reviewable, and survives without Bun, uv, port 37777, or the worker being up. Claude-mem also carries real operational tax: a daemon per host, two runtimes it auto-installs, and AGPL-3.0 network-copyleft on anything derived.

Two patterns are worth lifting, though:

1. **Progressive-disclosure retrieval contract for knowledge.** Formalize an `af ak search → af ak list-around <id> → af ak show <id>` trio so executor agents stop pulling full docs when an index line would do. Claude-mem's ~10x token claim is plausible and our current `af ak list` is already halfway there.
2. **Stable citation IDs for knowledge entries.** Assign each `research/knowledge/` entry a stable short ID and teach skills to cite them inline (`[K-042]`). Makes retrospectives and session logs linkable into the knowledge base cheaply.

Skip the observation capture, the worker, the vector DB, and Endless Mode — those solve a context-carry problem we deliberately don't have, because we chose curated distillation over automatic compression.

**Last checked:** 2026-04-18
