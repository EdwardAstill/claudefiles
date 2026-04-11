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
- **Purpose:** Python implementation with type safety — pyright LSP, uv, ruff, pytest
- **Use when:** Writing, debugging, or reviewing Python code
- **Produces:** Type-checked, ruff-clean, tested Python code
- **Chains into:** tdd, systematic-debugging, verification-before-completion

### typescript-expert
- **Purpose:** TypeScript/JS implementation — typescript-language-server LSP, bun, biome
- **Use when:** Writing, debugging, or reviewing TypeScript or JavaScript code
- **Produces:** Strictly typed, biome-clean, tested TypeScript code
- **Chains into:** tdd, systematic-debugging, verification-before-completion

### rust-expert
- **Purpose:** Rust implementation — rust-analyzer LSP, cargo, clippy, rustfmt
- **Use when:** Writing, debugging, or reviewing Rust code
- **Produces:** Clippy-clean, rustfmt-formatted, tested Rust code
- **Chains into:** tdd, systematic-debugging, verification-before-completion

### typst-expert
- **Purpose:** Typst document authoring — tinymist LSP, typst compile/watch
- **Use when:** Writing or debugging Typst documents
- **Produces:** Compiling .typ document with correct output
- **Chains into:** (terminal)
