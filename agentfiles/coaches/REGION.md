# Coaches Region

Skills that go beyond retrieval — applying domain reasoning to produce plans,
protocols, and critical evaluations grounded in the personal knowledge base.

The key distinction from `research/knowledge-base`:
- `knowledge-base` → retrieves and summarises what you know
- `coaches/*` → applies reasoning to what you know to produce action or critique

---

### health-advisor

- **Purpose:** Integrated health coach across diet, exercise, biochemistry, and supplementation
- **Use when:** You want a protocol or recommendation, not just information
- **NOT for:** Purely factual retrieval (knowledge-base) or evidence auditing (kb-critic)
- **Produces:** Actionable protocol with mechanism, watch points, and confidence rating
- **Chains into:** kb-critic (to validate the beliefs behind the protocol)

### kb-critic

- **Purpose:** Adversarial evidence auditor for the personal knowledge base
- **Use when:** You want to stress-test a belief, find contradictions, or audit a topic area
- **NOT for:** Retrieving information (knowledge-base) or building protocols (health-advisor)
- **Produces:** Evidence tier map, contradiction report, bias flags, recommended updates
- **Chains into:** note-taker (to update notes based on findings), health-advisor (re-plan after audit)
