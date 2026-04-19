# Microservices vs Modular Monolith for a 30-Engineer Team

Your skepticism is well-founded. The consensus has shifted against microservices-by-default, and 30 engineers is below the scale where microservices typically pay off.

## When microservices actually pay off

Team size is a weak trigger — the real drivers are:

1. **Independent deployment cadence** — different domains genuinely need to ship at different rates.
2. **Different scaling profiles** — e.g., ML inference vs CRUD.
3. **Different runtime / language needs.**
4. **Regulatory or security isolation** (PCI scope, HIPAA).
5. **Team coordination breaking down at deploy time** — team A's release consistently blocks team B.

Rough team-size heuristics from practitioner consensus:
- Under 20 engineers: modular monolith.
- 20-50: modular monolith unless one of the triggers above applies.
- 50-100: microservices start to pay off.
- 100+: microservices usually correct.

At 30 engineers on one product, you're in the "probably premature" zone unless you have a specific trigger.

## The industry has actually turned on microservices-by-default

In 2023-2026 several notable companies have gone back from microservices to monolith or hybrid architectures. Amazon Prime Video's 2023 case (90% cost reduction on a monitoring component) is the most-cited example. The practitioner narrative has shifted from "always microservices" (~2015-2020) to "modular monolith by default, microservices when you have a specific reason."

## Concrete failure modes to warn leadership about

1. **Distributed monolith** — services deployed separately but coupled at runtime. Every change needs coordinated deploys. All costs, no benefit. This is the #1 failure mode.
2. **Transaction boundaries crossing services** — anything that was a DB transaction is now a saga or eventual-consistency problem.
3. **Operational cost explosion** — K8s, service mesh, distributed tracing, per-service CI/CD. Infrastructure costs typically rise 30-40%. Needs a platform/SRE team you don't have.
4. **Debuggability loss** — stack trace becomes distributed trace. MTTR goes up.
5. **Data consistency becomes everyone's problem** — CAP trade-offs in every feature team.
6. **Deployment coordination** — versioning, contract tests, release trains. Often reinvents the monolith implicitly.
7. **On-call burden multiplies** — 30 people probably can't staff N rotations.
8. **Conway's Law pressure** — once service boundaries are set, org structure has to match, and vice versa.
9. **Resume-driven architecture** — sometimes the push is professional interest, not business need.
10. **Hard to reverse** — going back to monolith is much more expensive than staying.

## What to propose instead

1. **Ask leadership what specific pain they're trying to solve.** "We're at that scale" isn't a reason. Look for concrete triggers from the list above.
2. **If there's a specific pain point,** extract only that domain — strangler pattern. Microservices for the edges, monolith for the core.
3. **If there's no specific pain**, invest in modularity within the monolith:
   - Bounded contexts (DDD).
   - Module boundaries enforced by build tooling.
   - Internal APIs between modules.
   - Async event bus within one deployable.
   - Independent schemas per module.

This gets you most of the microservices benefits at a fraction of the cost.

## Caveats on sources

The specific cost multipliers (30-40% infra overhead, etc.) come from vendor surveys and practitioner blog posts — treat them as experiential wisdom, not rigorous research. Peer-reviewed studies on this specific decision are sparse. The strongest evidence is case studies (Amazon Prime Video, Basecamp, Netflix) and the DDD / Team Topologies literature.

## The steelman for microservices at your scale

They would be right if:
- Your monolith build+test cycle is over 20 min and blocking deploys.
- Team A's changes consistently break Team B's and bounded contexts haven't helped.
- One domain genuinely has very different scaling needs (ML, video, real-time).
- Regulatory isolation forces separation.

If any of these are true, extract that domain specifically — don't migrate everything.

## What to measure before deciding

- DORA metrics on your current monolith — deploy frequency, lead time, change failure rate, MTTR.
- Deploy conflicts per month across teams.
- Which endpoints/domains cause the scaling pain, if any.

Good reading: Sam Newman's *Monolith to Microservices*, Skelton & Pais's *Team Topologies*, and the Amazon Prime Video 2023 blog post.
