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
