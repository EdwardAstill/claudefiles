# Task Archetypes Registry

Canonical catalog of big-task archetypes mapped to agent compositions. The machine-readable source of truth is [`task-archetypes.json`](./task-archetypes.json); this document renders the same content as per-archetype tables.

## How to use this registry

This registry is consumed by the `manager` and `executor` skills when they need to decide how to split a large task across agents. The flow:

1. The executor (or manager) reads the user request and scans the `signal_phrases` across all archetypes for a match.
2. If an archetype matches, the phases tell the agent:
   - Which specialists to load for each phase.
   - Which phases can run in parallel vs must be sequential.
   - What each phase is expected to produce (the handoff artifact).
3. The `coordination` field on a phase, when present, names the higher-order skill that drives execution — usually `subagent-driven-development` or `git-worktree-workflow`.
4. The `risks` field is surfaced to the user up-front so scope is set honestly.

### Conventions

- `|` inside an agent entry (e.g. `python-expert|typescript-expert`) means OR — pick the one that matches the project's stack.
- `parallel: true` means the agents in that phase can be dispatched as concurrent subagents; `parallel: false` means strictly sequential.
- Agent names are exact matches to entries in `manifest.toml`. If a name is ever renamed there, update both this file and the JSON.

### When to add a new archetype

Add a new archetype when a recurring big-task shape does not cleanly map to an existing one, AND at least two past sessions would have benefited from the mapping. Prefer editing an existing archetype's signal phrases over inventing a new one.

---

## Archetypes

### `new-feature-full-stack` — Build a new full-stack feature

**Scale:** medium-large

**Signal phrases:** "build a feature", "implement X end-to-end", "add a new page that talks to the API", "full-stack feature", "new endpoint + UI", "ship a feature across UI, API, and DB"

| Phase | Agents | Produces | Parallel | Coordination |
|---|---|---|---|---|
| design | brainstorming, api-architect, database-expert, ui-expert | approved spec + API contract + schema sketch + component spec | no | sequential handoff |
| plan | writing-plans, coordination-advisor, git-advisor | implementation plan + coordination + git strategy | no | — |
| implement | database-expert, python-expert\|typescript-expert\|rust-expert, ui-expert, typescript-expert | working code + unit tests across DB, API, UI | yes | subagent-driven-development with git-worktree-workflow |
| verify | tdd, verification-before-completion, code-review, accessibility | tested, reviewed, a11y-checked change | no | — |

**Risks:** scope creep, cross-layer coupling, schema drift from contract.
**Notes:** Use `git-worktree-workflow` when parallel implementation could collide. Manager should escalate here if three+ layers change in parallel.

---

### `bug-investigation-and-fix` — Diagnose and fix a bug with a regression test

**Scale:** small-medium

**Signal phrases:** "there's a bug", "X is broken", "unexpected behaviour", "tests are failing", "fix the crash", "investigate this error"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| reproduce | systematic-debugging, terminal-read | reliable reproduction + captured error output | no |
| diagnose | systematic-debugging, codebase-explainer | root cause + affected surface area | no |
| fix | tdd, python-expert\|typescript-expert\|rust-expert | failing regression test, then passing fix | no |
| verify | verification-before-completion, code-review | verified fix + reviewed change | no |

**Risks:** fixing the symptom not the cause, missing regression test, over-scoping.
**Notes:** Always write the failing test before the fix. Do not skip `systematic-debugging` even if the cause looks obvious.

---

### `refactor-at-scale` — Large-scale structural refactor

**Scale:** large

**Signal phrases:** "refactor this module", "restructure the codebase", "split this monolith", "extract a package", "rename across the repo", "migrate to new pattern"

| Phase | Agents | Produces | Parallel | Coordination |
|---|---|---|---|---|
| map | codebase-explainer, system-architecture-expert | map of current structure + pain points | no | — |
| plan | refactoring-patterns, writing-plans, git-advisor | pattern choice + step plan + git strategy | no | — |
| execute | refactoring-patterns, regex-expert, python-expert\|typescript-expert\|rust-expert | refactored code, tests green at every step | no | subagent-driven-development |
| verify | tdd, verification-before-completion, simplify, code-review | tests green + simpler surface + review sign-off | no | — |

**Risks:** big-bang rewrite, test coverage gaps, merge conflicts with in-flight work.
**Notes:** Always use `git-worktree-workflow`. Strangler fig beats big bang. Tests green at every step is non-negotiable.

---

### `security-hardening` — Security audit, fix, and verification pass

**Scale:** medium

**Signal phrases:** "security audit", "harden this", "before production", "check for vulnerabilities", "OWASP review", "pentest prep"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| audit | security-review, dependency-management | prioritised findings + CVE list | yes |
| fix | tdd, python-expert\|typescript-expert\|rust-expert, database-expert | patches for each finding with tests | no |
| verify | security-review, verification-before-completion, code-review | re-audit showing findings closed + reviewed change | no |

**Risks:** partial fixes, regressing auth/authz, missed supply-chain CVEs.
**Notes:** Fix highest-severity findings first. Re-run `security-review` to confirm closure.

---

### `performance-optimization` — Profile, fix, and benchmark a slow path

**Scale:** small-medium

**Signal phrases:** "make it faster", "this is slow", "optimise the hot path", "cut latency", "reduce memory", "speed up the query"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| profile | performance-profiling, observability | profile output + bottleneck + baseline benchmark | no |
| fix | performance-profiling, python-expert\|typescript-expert\|rust-expert, database-expert, dsa-expert | optimised code with preserved behaviour | no |
| verify | performance-profiling, tdd, verification-before-completion | benchmark showing improvement + no regressions | no |

**Risks:** premature optimisation, unrealistic micro-bench, correctness regressions.
**Notes:** Do not skip the baseline benchmark. Optimise the actual hot path shown by the profile.

---

### `new-language-library-adoption` — Research, spike, and integrate a new library

**Scale:** medium

**Signal phrases:** "should we use X", "evaluate this library", "adopt a new dependency", "try out framework Y", "compare libraries for Z"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| research | research-agent, docs-agent, github-repo-researcher | trade-off report + API reference + repo analysis | yes |
| spike | brainstorming, python-expert\|typescript-expert\|rust-expert, tdd | throwaway spike proving the library fits | no |
| integrate | dependency-management, writing-plans, subagent-driven-development | integrated library with lockfile + rollout plan | no |
| verify | verification-before-completion, security-review, code-review | reviewed, CVE-clean integration | no |

**Risks:** sunk-cost after a big spike, license incompatibility, unmaintained upstream.
**Notes:** Spike should be discarded before real integration. Do not skip `security-review` on new deps.

---

### `codebase-onboarding` — Explore and document an unfamiliar repo

**Scale:** small-medium

**Signal phrases:** "new repo", "never seen this codebase", "onboard me to X", "how does this project work", "orient me in this repo"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| survey | codebase-explainer, github-repo-researcher | architecture map + execution paths + abstractions | yes |
| deepen | codebase-explainer, repomix | packed context + traced flows | no |
| document | note-taker, documentation | onboarding notes + orientation doc | no |

**Risks:** skimming without reading, wrong mental model, stale docs.
**Notes:** For remote repos, start with `github-repo-researcher`; for local, `codebase-explainer`. `repomix` compresses large trees.

---

### `infrastructure-migration` — Plan, implement, and verify an infra change

**Scale:** medium-large

**Signal phrases:** "migrate to Kubernetes", "move from docker-compose to K8s", "cloud migration", "change the deployment", "switch hosting", "rewrite the Dockerfile"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| plan | infrastructure-expert, system-architecture-expert, writing-plans | migration plan with rollback + staged cutover | no |
| implement | infrastructure-expert, github-actions-expert, observability | IaC + CI pipeline + observability instrumented | yes |
| verify | verification-before-completion, security-review, performance-profiling | staged env verified, perf + security parity | no |

**Risks:** no rollback plan, hidden coupling to old infra, secret drift.
**Notes:** Always stage behind a feature flag or DNS cutover. Observability must land before cutover.

---

### `documentation-sprint` — Audit, write, and cross-link docs

**Scale:** small-medium

**Signal phrases:** "write the docs", "documentation sprint", "update the README", "docs are stale", "add API docs", "write a migration guide"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| audit | documentation-maintainer, codebase-explainer | missing/stale docs + ground truth from code | yes |
| write | documentation, note-taker | new and updated docs with runnable examples | yes |
| link | documentation-maintainer | cross-links + TOC + sync with SKILL.md / AGENTS.md | no |

**Risks:** documenting intent not reality, drift from code, duplicated docs.
**Notes:** Verify each claim against the code. Prefer one source of truth.

---

### `deep-research-report` — Multi-source research synthesised into a report

**Scale:** medium-large

**Signal phrases:** "do deep research on X", "write a report on Y", "survey the literature", "synthesise sources about Z", "research report", "what does the evidence say"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| scope | brainstorming, research-agent | research question + success criteria + source plan | no |
| gather | research-agent, docs-agent, web-scraper, sci-hub, youtube, github-repo-researcher | papers + scraped pages + transcripts + repo breakdowns | yes |
| synthesise | note-taker, kb-critic, knowledge-base | per-source notes + contradiction map + integrated synthesis | no |
| deliver | documentation, note-taker | final report with citations + wiki cross-links | no |

**Risks:** one-source bias, paraphrasing without citation, scope creep.
**Notes:** This is the target archetype for `af research`. Results should feed back into `wiki/research/` as notes indexed by `knowledge-base`.

---

### `knowledge-base-ingestion` — Ingest external sources into the KB

**Scale:** medium

**Signal phrases:** "add this to the KB", "ingest these papers", "import this video series", "take notes on these docs", "index this corpus"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| acquire | sci-hub, youtube, web-scraper, file-converter | raw source material | yes |
| process | file-converter, note-taker | markdown notes with YAML frontmatter + wikilinks | yes |
| index | knowledge-base | ingested into markstore (BM25 + vector search) | no |
| audit | kb-critic | evidence-tier map + contradictions flagged | no |

**Risks:** duplicate ingestion, lossy PDF conversion, unvetted claims.
**Notes:** Run `kb-critic` after ingestion — never trust new material without auditing for contradictions.

---

### `skill-authoring` — Design, write, and test a new agentfiles skill

**Scale:** small-medium

**Signal phrases:** "write a new skill", "author a skill", "create a SKILL.md", "add a skill to agentfiles", "skill for doing X"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| design | brainstorming, design-advisor | skill purpose + trigger phrases + non-goals | no |
| write | writing-skills, documentation | SKILL.md with frontmatter + body | no |
| install | agentfiles-manager, audit | skill in manifest.toml + symlinks verified | no |
| test | skill-tester | eval output graded against benchmarks | no |

**Risks:** vague description, overlap with existing skill, not actually tested.
**Notes:** `audit` must pass before claiming install complete. `skill-tester` catches weak descriptions early.

---

### `api-design-review` — Spec an API, review it, iterate

**Scale:** small-medium

**Signal phrases:** "design an API", "review this API", "OpenAPI spec", "REST contract", "GraphQL schema", "check the endpoint design"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| spec | api-architect, brainstorming, docs-agent | OpenAPI / structured markdown contract + examples | no |
| review | api-architect, security-review, database-expert | findings across correctness, versioning, security, data model | yes |
| iterate | api-architect, writing-plans | revised contract + implementation plan | no |

**Risks:** breaking change in a "minor" version, auth as afterthought, N+1 baked into the contract.
**Notes:** Run `security-review` on auth paths. `database-expert` checks the contract does not force bad schemas.

---

### `data-analysis` — Ingest, clean, analyse, and report on data

**Scale:** medium

**Signal phrases:** "analyse this dataset", "run the numbers", "data analysis on X", "extract insights from Y", "make a chart of Z"

| Phase | Agents | Produces | Parallel |
|---|---|---|---|
| ingest | web-scraper, file-converter, database-expert | structured data in JSONL/CSV/SQLite | yes |
| analyse | python-expert, dsa-expert, database-expert | analysis scripts + computed results | no |
| report | note-taker, documentation, typst-expert | written report with charts + citations | no |

**Risks:** unvalidated data, p-hacking, non-reproducible results.
**Notes:** Every chart must come from a committed script. Prefer polars/duckdb for medium data.

---

### `multi-repo-change` — Coordinated change across multiple repos

**Scale:** large

**Signal phrases:** "change across repos", "update the client and server", "bump shared library", "cross-repo refactor", "sync three projects"

| Phase | Agents | Produces | Parallel | Coordination |
|---|---|---|---|---|
| plan | system-architecture-expert, writing-plans, git-advisor, coordination-advisor | per-repo task list + merge order + rollout | no | — |
| execute | git-worktree-workflow, python-expert\|typescript-expert\|rust-expert, tdd | branches per repo with passing tests | yes | manager with one subagent per repo |
| land | github-expert, github-actions-expert, code-review | PRs opened, CI green, merges in order | no | — |
| verify | verification-before-completion, observability | post-merge smoke test + alerting confirmed | no | — |

**Risks:** merge-order deadlock, half-rolled-out breaking change, forgotten downstream consumer.
**Notes:** Clear manager escalation. Merge order matters — write it down before opening any PR.
