# qdhenry/Claude-Command-Suite

**URL:** https://github.com/qdhenry/Claude-Command-Suite
**Stars:** ~500 | **Type:** Mega slash command + skills collection

## What It Is

One of the most comprehensive command collections publicly available:
- 216+ slash commands grouped under rich namespaces (`/project:*`, `/dev:*`, `/test:*`, `/security:*`, `/orchestration:*`, `/webmcp:*`)
- 12 Claude Code Skills (model-invoked)
- 54 named AI agents
- External integrations: GitHub, Linear, Cloudflare, BigCommerce

---

## What It Does Well

- **Scale with namespacing** — 200+ commands stay manageable because of consistent namespace grouping; commands don't collapse into an undifferentiated pile.
- **User-invoked vs model-invoked distinction** — same conceptual split as claudefiles (slash commands vs skills), applied consistently at scale.
- **External integrations as first-class skills** — Linear tickets, Cloudflare Workers, GitHub PRs are named skills rather than assumed context. Forces explicit surface area.
- **Multi-domain coverage** — `/security:*`, `/data:*`, `/orchestration:*` cover domains most toolkits skip.

---

## Weaknesses

- No installer or CLI — pure file dump, clone-and-use
- No routing system — user is always responsible for picking the right command out of 200+
- Integrations are tightly coupled to specific SaaS products — brittle outside those toolchains
- 216 commands without a discovery mechanism is overwhelming in practice

---

## What claudefiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **External system integrations as named skills** | A `linear-expert`, `slack-expert`, or `github-actions-expert` pattern where the skill encapsulates the entire integration surface (claudefiles has `github-expert` — extend this model) |
| **Namespace grouping in `cf agents`** | When skill count grows beyond 50, namespace prefixes (`/coding:`, `/research:`) in `cf agents --tree` output would help |
| **Explicit multi-domain coverage tracking** | A gap map of "which domains do we have vs. don't have" would make skill additions deliberate rather than organic |
