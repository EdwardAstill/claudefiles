# Research Region

Skills for documentation lookup and research.

---

### docs-agent
- **Purpose:** Answers "how do I use X?" — exact API signatures, config options, working code examples
- **Use when:** Need current documentation for a specific library, framework, SDK, or CLI tool
- **NOT for:** "Should I use X?" (research-agent) or "How does this codebase work?" (codebase-explainer)
- **Produces:** API reference, working example, source URL, version note
- **Chains into:** api-architect (feeds reference into design), python-expert / typescript-expert / rust-expert

### research-agent
- **Purpose:** Answers "should I use X?" — trade-off analysis, risk evaluation, expert consensus
- **Use when:** Choosing between options, evaluating risks, or needing evidence before committing to an approach
- **NOT for:** API lookups (docs-agent) or codebase understanding (codebase-explainer)
- **Produces:** Structured report: consensus, nuances, pitfalls, contradictions, recommended direction
- **Chains into:** api-architect (informs design), brainstorming (informs spec)

### test-taker
- **Purpose:** Answer a set of questions using provided reference material, with configurable strictness on how closely to follow that material
- **Use when:** Given questions + information to draw from; needs a complete set of answers in one markdown doc; calculation questions get Python scripts written, run, and results embedded
- **Produces:** `answers.md` (all questions answered) + `scripts/q<N>_*.py` (one per calculation question, already executed)
- **Chains into:** (terminal)

### readrun
- **Purpose:** Create readrun documentation — folders of Markdown rendered by the `rr` CLI as interactive sites with runnable Python (Pyodide) and auto-mounting JSX/React visualisations
- **Use when:** "Make readrun docs for X", "add an interactive tutorial", "document this with JSX widgets", "turn these notes into a readrun site", "build a lesson with runnable code"
- **Produces:** `.md` pages + `.readrun/scripts/` (Python, JSX, HTML), `.readrun/images/`, `.readrun/files/`; verified with `rr validate` and previewed with `rr <folder>`
- **Chains into:** (terminal)

### github-repo-researcher
- **Purpose:** Investigate GitHub repos — search, analyze architecture, and produce concise technical breakdowns
- **Use when:** User wants to understand a remote GitHub repo, find repos for a purpose, or compare repo options
- **NOT for:** Local codebase analysis (codebase-explainer) or GitHub operations like PRs/issues (github-expert)
- **Produces:** Technical breakdown: what it does, architecture, key patterns, tech stack, notable observations
- **Chains into:** codebase-explainer (after cloning), research-agent (for trade-off evaluation)

### codebase-explainer
- **Purpose:** Answers "how does this codebase work?" — maps architecture, traces execution, identifies abstractions
- **Use when:** Entering unfamiliar codebase; onboarding; planning changes spanning multiple layers
- **NOT for:** External library docs (docs-agent) or evaluating approaches (research-agent)
- **Produces:** Architecture map, traced execution path, key abstractions summary, "where to look" guide
- **Chains into:** brainstorming (informs design), writing-plans (informs task breakdown)

### youtube
- **Purpose:** Pull transcripts, audio (WAV/MP3 + clip trim), and summaries from any YouTube URL — video, playlist, or channel
- **Use when:** User wants text, audio, or a summary of one or more YouTube videos; channel-scale bulk transcript grabs; metadata listings
- **NOT for:** Other video sites (use yt-dlp directly), or videos that need authenticated access (out of scope)
- **Produces:** `.txt` transcripts, `.mp3`/`.wav` audio, structured summary blocks
- **Chains into:** note-taker (turn transcripts into notes), knowledge-base (index into KB), test-taker (Q&A over a set)

### terminal-read
- **Purpose:** Capture the user's live terminal scrollback so the agent can see output that happened outside the conversation
- **Use when:** "Look at what just printed", "check that error", "see the output of setup.fish" — when the user has **not** pasted the output into chat
- **NOT for:** Output from commands the agent itself ran (Bash tool output is already visible)
- **Produces:** A plain-text capture file via `af terminal --out <path>`, ready to Read
- **Chains into:** systematic-debugging, codebase-explainer, executor

### knowledge-base

- **Purpose:** Retrieve and synthesise from the personal knowledge base (~3700 docs)
- **Use when:** Answering questions about health, training, pharmacology, nutrition, supplements, hormones
- **NOT for:** Building protocols (health-advisor) or auditing beliefs (kb-critic)
- **Produces:** Synthesised answer grounded in personal KB notes
- **Chains into:** health-advisor (turns retrieval into protocol), kb-critic (audits retrieved beliefs)

### web-scraper
- **Purpose:** Pull data off a website via pure HTTP — fetch HTML/JSON, parse, paginate, store
- **Use when:** User wants information from a site and the data is present in raw HTML, embedded JSON (`__NEXT_DATA__`, JSON-LD), or a discoverable JSON API endpoint
- **NOT for:** JS-rendered pages with no backing API (use `browser-control`), local file conversion (use `file-converter`), or full browser-driven sessions
- **Produces:** Runnable `uv run` Python script (httpx + selectolax + trafilatura) → JSONL/CSV/SQLite output
- **Chains into:** file-converter (HTML → markdown after scrape), note-taker (scraped prose → notes), knowledge-base (index), test-taker (Q&A over scraped corpus)

> For action-oriented coaching or evidence critique, see `coaches/` region:
> `health-advisor` (protocols) and `kb-critic` (evidence audit).

