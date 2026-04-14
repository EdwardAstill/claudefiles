# Skill Tree

```
agentfiles/
├── management/
│   ├── orchestration/
│   │   ├── executor              ← default entry point for every task
│   │   ├── manager               ← multi-agent coordinator (escalation only)
│   │   └── subagent-driven-development
│   ├── consultants/              (loaded inline by manager during planning)
│   │   ├── design-advisor
│   │   ├── git-advisor
│   │   └── coordination-advisor
│   └── meta/
│       ├── using-agentfiles     ← session-start skill
│       ├── agentfiles-manager
│       ├── skills
│       ├── writing-skills
│       └── documentation-maintainer  ← docs consistency checks
│
├── planning/
│   ├── brainstorming             ← idea → spec
│   └── writing-plans             ← spec → implementation plan
│
├── coding/
│   ├── languages/                (toolchain + conventions specialists)
│   │   ├── python-expert         ← pyright LSP, uv, ruff, pytest
│   │   ├── typescript-expert     ← ts-language-server LSP, bun, biome
│   │   ├── rust-expert           ← rust-analyzer LSP, cargo, clippy
│   │   ├── typst-expert          ← tinymist LSP, typst compile
│   │   ├── ui-expert             ← React, Tailwind, shadcn/ui
│   │   └── tui-expert            ← terminal UIs (Textual, Ratatui, Ink)
│   ├── quality/
│   │   ├── tdd
│   │   ├── systematic-debugging
│   │   ├── verification-before-completion  ← mandatory executor exit gate
│   │   ├── code-review
│   │   ├── simplify              ← recently changed code
│   │   ├── security-review       ← OWASP, CVEs, injection, auth    [NEW]
│   │   ├── performance-profiling ← "correct but slow"               [NEW]
│   │   ├── refactoring-patterns  ← large-scale restructuring        [NEW]
│   │   ├── dependency-management ← version bumps, CVE scanning      [NEW]
│   │   ├── observability         ← logging, tracing, metrics        [NEW]
│   │   ├── accessibility         ← WCAG 2.1 AA, ARIA, a11y         [NEW]
│   │   ├── regex-expert          ← mass search/replace with sd/rg
│   │   ├── skill-tester          ← benchmark skills with rubric grading
│   │   └── documentation         ← READMEs, API docs, guides, changelogs
│   ├── architecture/
│   │   └── system-architecture-expert ← service boundaries, scaling
│   ├── dsa/
│   │   └── dsa-expert            ← data structures, algorithms, complexity
│   ├── data/
│   │   ├── database-expert       ← schema, migrations, queries      [NEW]
│   │   └── file-converter        ← PDF/image to markdown via cnv
│   ├── infrastructure/
│   │   └── infrastructure-expert ← Docker, K8s, Terraform, IaC      [NEW]
│   ├── version-control/
│   │   ├── git-expert
│   │   ├── github-expert
│   │   └── git-worktree-workflow
│   ├── ci-cd/
│   │   └── github-actions-expert
│   └── api/
│       └── api-architect
│
└── research/
    ├── docs-agent                ← "how do I use X?"
    ├── research-agent            ← "should I use X?"
    ├── codebase-explainer        ← "how does this codebase work?"
    ├── note-taker
    └── test-taker
```

## Routing

```
user message
  │
  ▼
using-agentfiles (session start)
  │
  ▼
executor (every new task)
  │
  ├─ work ──────────────► handles end-to-end
  │                         loads specialists inline
  │                         MANDATORY verification before completion
  │                         passes HANDOFF CONTEXT on escalation
  │
  └─ parallel/multi-domain ──► manager
                                 │
                                 ├─ Phase 1: Plan
                                 │   reads HANDOFF CONTEXT from executor
                                 │   reads REGION.md files
                                 │   inline advisors (if non-obvious):
                                 │   ├── design-advisor
                                 │   ├── git-advisor
                                 │   └── coordination-advisor
                                 │
                                 ├─ Phase 2: Execute
                                 │   ├── Parallel agents
                                 │   ├── Sequential (subagent-driven-dev)
                                 │   └── Individual specialist
                                 │
                                 └─ Phase 3: Review + Replan
                                     check conflicts, run tests
                                     adaptive replan if agents fail
```

## Research Skill Routing

```
"how do I use X?"          → docs-agent          (API lookup)
"should I use X?"          → research-agent       (trade-off analysis)
"how does this code work?" → codebase-explainer   (architecture mapping)
```

## Quality Gate Chain

```
tdd (before code)
  → implementation
  → systematic-debugging (if broken)
  → security-review (if handles user input/auth)
  → verification-before-completion (MANDATORY before claiming done)
  → code-review (before merge)
  → simplify (after merge, if needed)
```

## Lifecycle

```
brainstorming → writing-plans → subagent-driven-development
     │                │                    │
  produces:       produces:            executes:
  spec doc     implementation plan    task-by-task with review gates
```
