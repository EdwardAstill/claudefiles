# Watchlist — repos worth monitoring

Not full curated writeups (those go in the other `research/projects/` files).
Just a running list of agent-ecosystem repos to keep an eye on: interesting
ideas, competing approaches, or upstream patterns worth borrowing.

Format: `- [owner/repo](url) — one-line reason to watch, date added`.

---

- [EvoMap/evolver](https://github.com/EvoMap/evolver) — worth investigating; flagged 2026-04-19 as potentially useful for the agent ecosystem. TBD what it actually does; look at it before next scope decision.
- [openai/openai-agents-python](https://github.com/openai/openai-agents-python) — OpenAI's Python Agents SDK; a competing take on multi-agent orchestration. Patterns for tool calling / handoffs / tracing worth comparing to the agentfiles subagent + skill split. 2026-04-19.

---

## Promotion rule

When a watchlist entry earns a full writeup (we adopt patterns, reject them
explicitly, or it becomes a peer/competitor worth calibrating against),
move it to a proper `<owner>-<repo>.md` file under `research/projects/`
following the template from the existing entries (agent-platforms,
education-and-showcases, etc.).
