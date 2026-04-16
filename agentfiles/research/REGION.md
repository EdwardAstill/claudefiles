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

### note-taker
- **Purpose:** Create markdown notes in two modes: human-readable (with readrun interactive code) or LLM-optimized (dense, structured reference for AI/RAG consumption)
- **Use when:** "Make notes on X", "create a lesson", "write a readrun page", "LLM notes on Y", "add reference docs for Z to the knowledge base"
- **Produces:** Human mode: `.md` note(s) + `.readrun/scripts/` (if readrun). LLM mode: `.md` with YAML frontmatter, wikilinks, semantic headers.
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

### knowledge-base

- **Purpose:** Retrieve and synthesise from the personal knowledge base (~3700 docs)
- **Use when:** Answering questions about health, training, pharmacology, nutrition, supplements, hormones
- **NOT for:** Building protocols (health-advisor) or auditing beliefs (kb-critic)
- **Produces:** Synthesised answer grounded in personal KB notes
- **Chains into:** health-advisor (turns retrieval into protocol), kb-critic (audits retrieved beliefs)

> For action-oriented coaching or evidence critique, see `coaches/` region:
> `health-advisor` (protocols) and `kb-critic` (evidence audit).

