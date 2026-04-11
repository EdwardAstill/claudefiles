# Research Region

Skills for documentation lookup and research.

---

### docs-agent
- **Purpose:** Fetch current documentation for libraries, frameworks, SDKs, APIs, and CLI tools
- **Use when:** Need accurate API signatures, config options, or working examples for a specific library
- **Produces:** API reference, working example, source URL, version note
- **Chains into:** api-architect (feeds reference into design), python-expert / typescript-expert / rust-expert

### research-agent
- **Purpose:** General research and critical analysis — expert consensus, trade-offs, pitfalls
- **Use when:** Evaluating an approach, understanding risks, or finding expert consensus before committing
- **Produces:** Structured report: consensus, nuances, pitfalls, contradictions, recommended direction
- **Chains into:** api-architect (informs design), brainstorming (informs spec)

### test-taker
- **Purpose:** Answer a set of questions using provided reference material, with configurable strictness on how closely to follow that material
- **Use when:** Given questions + information to draw from; needs a complete set of answers in one markdown doc; calculation questions get Python scripts written, run, and results embedded
- **Produces:** `answers.md` (all questions answered) + `scripts/q<N>_*.py` (one per calculation question, already executed)
- **Chains into:** (terminal)

### note-taker
- **Purpose:** Create markdown notes, lessons, or interactive tutorials — plain or readrun-compatible with runnable code blocks
- **Use when:** "Make notes on X", "create a lesson", "write a readrun page", "interactive tutorial for X"
- **Produces:** `.md` note(s) + `.readrun/scripts/` files (if readrun mode), verified for broken references
- **Chains into:** (terminal)

### codebase-explainer
- **Purpose:** Systematic codebase analysis — architecture layers, execution paths, key abstractions, dependencies
- **Use when:** Unfamiliar codebase needs a working mental model before making changes; onboarding; tracing unexpected behaviour
- **Produces:** Architecture map, traced execution path, key abstractions summary, "where to look" guide
- **Chains into:** brainstorming (informs design), writing-plans (informs task breakdown)

