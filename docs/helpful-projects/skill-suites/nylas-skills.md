# nylas/skills

**URL:** https://github.com/nylas/skills
**Type:** Specialized API Skill Pack

## What It Is

A specialized skill pack developed by Nylas that teaches agents how to interact with Email, Calendar, and Contacts APIs. It is designed to prevent hallucinations during complex integration tasks by providing the agent with exact API signatures and patterns.

---

## What It Does Well

- **API Precision** — Dramatically reduces hallucinations when working with specific, complex external APIs.
- **Integration Patterns** — Not just a list of endpoints; includes "best practice" patterns for common integration tasks (e.g., "How to handle OAuth refresh tokens").
- **Vendor-Backed** — High-quality, reliable information directly from the source.
- **Modular** — Can be easily added to any agent project that needs to handle communication-related features.

---

## Weaknesses

- **Extremely Niche** — Only useful for projects using the Nylas API or similar communication services.
- **Maintenance** — If the API changes, the skills must be manually updated to prevent the agent from using outdated patterns.
- **Commercial Bias** — Naturally focused on the Nylas ecosystem rather than generic, open-source alternatives.

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **External API Packs** | Create a `agentfiles/api/` category for specialized skills that handle common third-party services (Stripe, AWS, GitHub API, etc.). |
| **Pattern-Based Skills** | Shift some skills from "how to use a language" to "how to implement a pattern" (e.g., "The OAuth Specialist," "The Webhook Handler"). |
| **Documentation Inlining** | For complex APIs, have the skill include the "Most Important 10%" of the documentation directly in the prompt to avoid `docs-agent` lookups. |
