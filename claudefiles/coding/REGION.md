# Coding Region

Skills for implementation, quality, version control, and language-specific work.

---

## Quality

### tdd
- **Purpose:** Test-driven development — write failing test, implement, pass, commit
- **Use when:** Writing new functionality; any implementation task
- **Produces:** Tested, committed implementation
- **Chains into:** verification-before-completion, requesting-code-review

### systematic-debugging
- **Purpose:** Structured bug investigation — reproduce, isolate, fix, verify
- **Use when:** Bug report or unexpected behaviour; test failures
- **Produces:** Root cause identified, fix committed, regression test added
- **Chains into:** verification-before-completion

### verification-before-completion
- **Purpose:** Final check before declaring a task done — tests pass, no regressions
- **Use when:** Before marking any implementation task complete
- **Produces:** Go/no-go signal; failing tests reported
- **Chains into:** (terminal if passing); tdd, systematic-debugging (if failing)

### code-review
- **Purpose:** Request a code review (dispatch reviewer subagent with focused context) or process incoming review feedback (verify, implement, or push back technically)
- **Use when:** Implementation complete and want a quality check; or have review feedback to act on
- **Produces:** Review findings; or addressed review comments with updated code
- **Chains into:** verification-before-completion

### simplify
- **Purpose:** Reduce code complexity — remove duplication, dead code, over-engineering
- **Use when:** Code is working but complex; after a large implementation; refactor request
- **Produces:** Simpler code with same behaviour; committed
- **Chains into:** verification-before-completion

### security-review
- **Purpose:** Security audit — OWASP top 10, injection vectors, auth/authz, secrets exposure, dependency CVEs
- **Use when:** Before shipping code that handles user input, auth, or sensitive data; periodic security audit
- **Produces:** Prioritized security findings (critical/warning/info) with fix recommendations
- **Chains into:** verification-before-completion

### performance-profiling
- **Purpose:** Diagnose and fix performance issues — profiling, algorithmic analysis, benchmarks
- **Use when:** Code is correct but slow; optimizing hot paths; evaluating scalability
- **Produces:** Profile results, bottleneck identification, optimized code with benchmarks
- **Chains into:** tdd, verification-before-completion

### refactoring-patterns
- **Purpose:** Large-scale code restructuring using proven patterns (strangler fig, extract method, etc.)
- **Use when:** Restructuring existing code that has grown unwieldy; migrating architecture; not for small cleanups (that's simplify)
- **Produces:** Restructured code with tests green at every step; committed
- **Chains into:** tdd, verification-before-completion

### dependency-management
- **Purpose:** Dependency hygiene — version bumps, CVE scanning, breaking change analysis, lock file management
- **Use when:** Updating dependencies; auditing for vulnerabilities; evaluating new dependencies
- **Produces:** Updated dependencies with verified compatibility; audit report
- **Chains into:** verification-before-completion

### observability
- **Purpose:** Structured logging, distributed tracing, metrics instrumentation
- **Use when:** Adding logging/tracing/metrics to a service; debugging production issues via logs; setting up monitoring
- **Produces:** Instrumented code with structured logs, traces, or metrics
- **Chains into:** verification-before-completion

### accessibility
- **Purpose:** Web/UI accessibility compliance — WCAG 2.1 AA, semantic HTML, ARIA, keyboard navigation
- **Use when:** Building or reviewing UI components; accessibility audit; fixing a11y issues
- **Produces:** Accessible UI code; audit findings with fix recommendations
- **Chains into:** verification-before-completion

---

## Data

### database-expert
- **Purpose:** Schema design, migrations, query optimization, indexing, ORM patterns
- **Use when:** Designing database schema; writing migrations; optimizing slow queries; reviewing data layer code
- **Produces:** Schema design, migration files, optimized queries, indexing recommendations
- **Chains into:** tdd, verification-before-completion

---

## Infrastructure

### infrastructure-expert
- **Purpose:** Dockerfiles, docker-compose, Kubernetes, Terraform/Pulumi, cloud config, reverse proxies
- **Use when:** Writing or reviewing infrastructure config; containerizing an app; setting up deployment
- **Produces:** Infrastructure config files; deployment setup
- **Chains into:** verification-before-completion

---

## Version Control

### git-worktree-workflow
- **Purpose:** Full worktree lifecycle — create isolated workspace, verify baseline, finish with merge/PR/discard
- **Use when:** Starting feature work that needs isolation; completing work in a worktree
- **Produces:** Isolated branch + worktree (setup); merged/PR'd/cleaned work (finish)
- **Chains into:** specialist skill (after setup); git-expert, github-expert (at finish)

### git-expert
- **Purpose:** Deep git operations — complex history, conflict resolution, bisect, reflog
- **Use when:** Git operation beyond everyday commit/push/merge; something went wrong
- **Produces:** Resolved git state; history cleaned; conflict resolved
- **Chains into:** github-expert (if PR needed after)

### github-expert
- **Purpose:** GitHub-specific workflows — PRs, issues, Actions, branch protection
- **Use when:** Creating or managing PRs; GitHub Actions; repo settings
- **Produces:** PR created/merged; Actions configured; issue managed
- **Chains into:** (terminal)

---

## CI/CD

### github-actions-expert
- **Purpose:** Write, debug, and review GitHub Actions workflows
- **Use when:** Workflow failing; job skipped; secrets/permissions misconfigured; matrix builds behaving oddly; authoring a new workflow
- **Produces:** Fixed or new workflow file; root cause of failure identified
- **Chains into:** github-expert (for PR/repo operations after workflow fix)

---

## Architecture

### api-architect
- **Purpose:** Design and review API contracts — REST, GraphQL, RPC; schema design
- **Use when:** Designing a new API or reviewing an existing one for consistency/correctness
- **Produces:** API design document or review findings
- **Chains into:** tdd (implement the designed API)

---

## Languages

### python-expert
- **Purpose:** Python toolchain and conventions — pyright LSP, uv, ruff, pytest integration
- **Use when:** Need LSP diagnostics, package management, linting, or testing patterns for Python
- **Produces:** Type-checked, ruff-clean, tested Python code with proper toolchain usage
- **Chains into:** tdd, systematic-debugging, verification-before-completion

### typescript-expert
- **Purpose:** TypeScript toolchain and conventions — typescript-language-server LSP, bun, biome
- **Use when:** Need LSP diagnostics, bun/npm tooling, biome linting, or strict typing patterns for TS/JS
- **Produces:** Strictly typed, biome-clean, tested TypeScript code with proper toolchain usage
- **Chains into:** tdd, systematic-debugging, verification-before-completion

### rust-expert
- **Purpose:** Rust toolchain and conventions — rust-analyzer LSP, cargo, clippy, rustfmt
- **Use when:** Need LSP diagnostics, cargo tooling, clippy linting, or Rust-specific patterns (ownership, lifetimes)
- **Produces:** Clippy-clean, rustfmt-formatted, tested Rust code with proper toolchain usage
- **Chains into:** tdd, systematic-debugging, verification-before-completion

### typst-expert
- **Purpose:** Typst document authoring — tinymist LSP, typst compile/watch
- **Use when:** Writing or debugging Typst documents
- **Produces:** Compiling .typ document with correct output
- **Chains into:** (terminal)
