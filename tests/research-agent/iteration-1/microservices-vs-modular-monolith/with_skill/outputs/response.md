# Research: Microservices vs Modular Monolith at ~30 Engineers

**Depth level:** Standard. Defaulting to structured report format; say the word if you want a full deep-dive with vendor-survey citations.

## Claim-Type Audit

| Claim | Type | Weight |
|---|---|---|
| "At ~30 engineers, modular monolith is the correct default" | Practitioner consensus + industry experience | Moderate-high |
| "Microservices add 30-40% infrastructure cost" | Vendor survey / blog estimates | Low-moderate (experiential, not peer-reviewed) |
| "You should microservices because you're at that scale" | Bandwagon / marketing | Low |
| "Amazon Prime Video saved 90% by going back to monolith" | Single case study (famous) | Moderate — one data point |
| "Microservices require independent deployment cadence / scaling profiles to pay off" | Principled architectural argument | High |

## Consensus

**Strong consensus in the 2024-2026 practitioner literature:**
- **Modular monolith is now the correct default** for teams with <50 engineers on a single product.
- The industry has swung from "microservices by default" (2015-2020) to "monolith by default, microservices for specific reasons" (2023-2026).
- **Team size alone is not a valid trigger for microservices.** The valid triggers are architectural, not organizational.

Confidence: high that the consensus has shifted; moderate on the specific thresholds.

## Nuances

### The real triggers for microservices (not team size)

Microservices pay off when you have at least one of:
1. **Independent deployment cadence** — different domains need to ship at different rates without coordination.
2. **Different scaling profiles** — one domain is CPU-bound ML inference, another is CRUD; monolith forces you to scale everything together.
3. **Different runtime / language needs** — e.g., Python for ML, Go for control plane.
4. **Regulatory / security isolation** — PCI scope, HIPAA, or tenant isolation.
5. **Different team ownership becoming a deploy bottleneck** — team A can't ship because team B's change is in the same release.

**At 30 engineers on one product, most teams have none of these.** Re-ask leadership: which one do we have?

### Team-size heuristics (practitioner consensus, not peer-reviewed)
- <20 engineers: modular monolith, clearly.
- 20-50 engineers: modular monolith, unless a real architectural trigger above is present.
- 50-100 engineers: microservices start to pay off for domain autonomy.
- 100+: microservices are typically correct for most orgs.

At 30, you are below the size where microservices pay back coordination overhead.

### The migration-back trend
Documented cases of going microservices → monolith or hybrid:
- **Amazon Prime Video (2023)**: 90% cost reduction consolidating a monitoring component.
- **InVision**, **Istio** (simplification of its own architecture), various startup blog posts.
- Industry shift is real and not just contrarian.

## Known Pitfalls (Failure Modes to Warn Leadership About)

1. **Distributed monolith.** Services are deployed separately but coupled at runtime — every change requires coordinated deploys. You get all microservice costs and none of the independence. This is the #1 failure mode; practitioner estimates suggest it catches ~50% of first-time microservice migrations.
2. **Transaction boundaries crossing services.** Anything that was a database transaction is now a saga, two-phase commit, or eventual consistency problem. Every cross-service write is a new bug surface.
3. **Operational overhead explosion.** Kubernetes, service mesh, distributed tracing, per-service CI/CD, per-service observability. Infrastructure cost typically rises 30-40% (vendor surveys, not rigorous). SRE / platform team becomes a hiring requirement you didn't have before.
4. **Debuggability collapses.** "Stack trace" is now a Jaeger trace you have to navigate. MTTR climbs.
5. **Data consistency becomes everyone's problem.** CAP trade-offs used to be the DB's concern. Now every feature team has to reason about eventual consistency, idempotency, and retry semantics.
6. **Deployment coordination.** Service A v1.5 depends on Service B v2.0. Now you need contract testing, versioning discipline, or release trains — often reinventing the monolith's implicit coordination, badly.
7. **On-call burden multiplies.** Each service needs coverage. A 30-person org typically cannot staff N on-call rotations.
8. **Conway's Law inversion.** Service boundaries force org structure. If your team boundaries change, your services don't match and you're stuck.
9. **Resume-driven architecture.** The strongest microservices advocate on the team may be pushing for it because it's professionally interesting, not because it helps the business. Flag this explicitly.
10. **Reversibility is expensive.** Going back to monolith is much harder than staying on one.

## Contradictions / Open Questions

| Disagreement | Why |
|---|---|
| Netflix / Uber blogs: "microservices at scale are essential." | They're at 1,000-10,000 engineers, which is far above your scale. Not contradictory — different regime. |
| DHH / Basecamp / HEY: "just use a monolith." | Small team (<50), focused product — matches your regime; their argument generalizes to you. |
| Fowler's "MonolithFirst" (2015) vs microservices-first advocacy of the same era. | Even Fowler, who popularized microservices, argued start-monolith-then-extract from the beginning. |
| "Independent scaling" claimed benefit. | Valid only if domains actually scale differently. If your load is proportional across the app, one big box scales fine. |

Critical meta-observation: most microservices success stories come from companies **much larger than 30 engineers**. That their architecture works at 1000 engineers does not mean it would have worked for them at 30.

## Source Quality Note

- The specific cost/complexity multipliers (30-40% infra cost, 5x operational complexity) come from vendor surveys (DataDog, Honeycomb, Camunda) and practitioner blog posts. Treat as **experiential wisdom, not empirical fact**.
- Peer-reviewed academic research on microservices vs monolith at team-level decisions is sparse. Shahin, Babar & Zhu 2017 ("Continuous Integration, Delivery and Deployment: A Systematic Review") is a reasonable academic anchor but doesn't directly address the decision.
- The strongest available evidence is **case studies** (Amazon Prime Video, Uber, Netflix, Basecamp) and the **Team Topologies / DDD literature** (Skelton & Pais, Evans).

## Recommended Direction

**Push back on the migration. Reframe the conversation.**

1. **Ask leadership what specific pain they're solving.** "We're at the scale where you do this" is not a reason. Real reasons look like: "Team A's deploys break Team B's service three times a week." Or: "Our ML inference spikes force us to over-provision CRUD servers."
2. **If the pain is real but narrow**, extract 1-2 specific services (strangler pattern). "Microservices for the edges, monolith for the core." This is the pragmatic path.
3. **If the pain is vague**, decline and invest in modularity within the monolith: bounded contexts (DDD), module boundaries enforced at build time (e.g., import linting), internal APIs, async event bus within one deployable, independent DB schemas per module. This captures ~80% of the microservices benefit at ~5% of the cost.
4. **Run the cost math out loud.** At 30 engineers, adding K8s + service mesh + per-service CI + distributed tracing + an SRE hire is easily $500K-$1M/year. What's the expected return?

### Steelman of the pro-microservices case (when it would be correct for you)
- Your monolith build+test cycle is >20 minutes and blocking deploys.
- One team's changes consistently break another's — and bounded contexts within the monolith haven't helped.
- You have a domain with drastically different scaling profile (ML, real-time, video) that's forcing the whole app to over-provision.
- Regulatory isolation requires it (PCI / HIPAA separation).

If any of these are true, extract *that* domain, not everything.

## Further Investigation

- Pull **DORA metrics** on your current monolith: deploy frequency, lead time, change failure rate, MTTR. This will tell you whether your monolith is actually the bottleneck.
- Count deploy conflicts per month — is one team's code blocking another's?
- Profile which endpoints cause scaling pain. If it's one or two, that's the extraction candidate, not "all of it."
- Read **Sam Newman, *Monolith to Microservices*** for the extraction-pattern playbook.
- Read **Skelton & Pais, *Team Topologies*** for the org-design angle on when service boundaries pay off.
- Read **Amazon Prime Video's 2023 "Scaling up the Prime Video audio/video monitoring service"** blog post — the canonical modern "we went back" case.

**Confidence summary for your decision:**
- "At 30 engineers on one product, microservices are probably premature" → moderate-high confidence.
- "Specific cost multipliers (30-40% overhead)" → moderate confidence (experiential data).
- "Modular monolith can get you 80% of the benefit" → practitioner consensus, moderate confidence.
- "The migration will probably fail as a distributed monolith" → moderate-high confidence based on observed failure rate of first-time microservice migrations.
