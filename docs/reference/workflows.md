# Workflows Reference

End-to-end traces of common patterns — what happens at each stage, which skills run,
which scripts execute, which files are read and written.

---

## 1. New machine setup

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
```

| Step | What happens | Output |
|------|-------------|--------|
| Clone | Clones repo to `~/.local/share/claudefiles-src/` | Local clone |
| Build flat skills/ layer | `install.sh` finds all leaf `SKILL.md` files, builds symlinks in `skills/` | `skills/<name>/` symlinks |
| Install plugin | Symlinks `skills/` → `~/.claude/skills/claudefiles/` | Active on next session |
| Install bin tools | Symlinks `tools/scripts/cf-*` → `~/.local/bin/` | CLI tools on PATH |

All 30 skills active globally. Changes to skill files in the repo are live on the next
session — no reinstall needed.

---

## 2. Standard task — executor path

**User:** Any new task request.

| Step | What happens | Tools/scripts |
|------|-------------|---------------|
| Orient | `cf-context` + `cf-status` | Reads project structure, git state |
| Assess | Is genuine parallelism needed? Almost always no. | Inline decision |
| Plan (if needed) | 2–4 line approach for non-trivial tasks | In-context |
| Execute | Full tool access, specialist skills loaded on demand | Skill tool (inline) |
| Verify | Run tests, check output | Bash, Read |
| Report | Report with evidence, not assertions | — |

Specialist skills loaded inline during execution (examples):

| Signal | Skill loaded |
|--------|-------------|
| Rust, Cargo, ownership issues | `rust-expert` |
| Python type errors, toolchain | `python-expert` |
| API design question arises | `api-architect` |
| Bug appears mid-task | `systematic-debugging` |
| Library API needed | `docs-agent` |
| About to finish | `verification-before-completion` |

Inline loading keeps full session context. The specialist's patterns apply in the
same conversation — no context loss.

---

## 3. Multi-agent task — manager path

**Trigger:** Executor escalates (or user invokes manager directly) when the task
genuinely requires parallel agents.

### Phase 1 — Plan

| Step | What happens | Files read |
|------|-------------|------------|
| Read regions | `cat claudefiles/{coding,planning,research}/REGION.md` | Skill catalogs for involved categories |
| Answer three questions | Design? Git strategy? Coordination? | In-context |
| Load advisors (if needed) | `Skill("design-advisor")` / `Skill("git-advisor")` / `Skill("coordination-advisor")` | Advisor SKILL.md |
| Confirm with user | Present: which agents, what order, what each produces | — |
| Wait | Do not execute until confirmed | — |

### Phase 2 — Execute

| Pattern | When | How |
|---------|------|-----|
| Parallel agents | Independent domains, no shared state | Multiple Agent calls in one message |
| Sequential with gates | Tasks depend on each other's output | `Skill("subagent-driven-development")` |
| Single specialist | Focused domain work | Single Agent call |

After all agents return:
- Review summaries for conflicts
- Run full test suite
- Resolve any divergence before reporting

---

## 4. Feature work — git-worktree-workflow path

**User:** "Build the auth feature" or any discrete feature that needs isolation.

| Step | What happens | Scripts |
|------|-------------|---------|
| Assess git strategy | Is isolation needed? (new feature, risky changes, parallel work?) | Inline or `git-advisor` |
| Create worktree | `git worktree add ../worktree-<branch> -b <branch>` | `cf-worktree` |
| Emit context block | WORKTREE CONTEXT block for other skills to read | In-context |
| Implement | executor or agents work inside the worktree | — |
| Complete | Merge, PR, or discard — four options documented in the skill | `github-expert` for PRs |
| Cleanup | `git worktree remove` | `cf-worktree` |

WORKTREE CONTEXT block (published, consumed by other skills):
```
WORKTREE CONTEXT
  Path:    /path/to/worktree-feature-auth
  Branch:  feature/auth
  Status:  ready
```

---

## 5. New feature design — brainstorming + writing-plans path

**User:** "I want to add X" with unclear requirements or complex implementation.

| Step | Skill | Output |
|------|-------|--------|
| Clarify requirements | `brainstorming` | Spec document at `docs/specs/YYYY-MM-DD-<topic>-design.md` |
| Write implementation plan | `writing-plans` | Plan document at `docs/plans/YYYY-MM-DD-<topic>.md` |
| Execute plan | `subagent-driven-development` | Committed, reviewed implementation |
| Finish | `git-worktree-workflow` (if applicable) | Merged or PR'd |

---

## 6. Research workflow

### Technical reference — docs-agent

**User:** "How does Hono's streaming API work?" / "What's the Prisma upsert syntax?"

| Step | What happens | Tools |
|------|-------------|-------|
| Identify library + version | `cf-versions` if needed | Reads lockfiles |
| Fetch docs | context7 MCP → resolve library ID → fetch docs | `context7` MCP |
| Supplement | WebSearch / WebFetch for examples | Web |
| Output | Exact API, working example, source URL, version note | — |

### Trade-off research — research-agent

**User:** "Should I use Prisma or Drizzle?" / "What are the risks of X?"

| Step | What happens | Tools |
|------|-------------|-------|
| Search | WebSearch across multiple sources | Web |
| Fetch | WebFetch on top results | Web |
| Synthesise | Consensus, nuances, pitfalls, contradictions | In-context |
| Output | Structured report: confidence levels, recommendation, further investigation | — |

---

## 7. Agent communication bus

`.claudefiles/` is the shared state layer — written by CLI tools, read by any skill.

| File | Written by | Read by | Content |
|------|-----------|---------|---------|
| `context.md` | `cf-context` | executor, manager | Project fingerprint: language, stack, structure |
| `repo-map.md` | `cf-status` | executor, git-expert | Git state: branch, commits, worktrees |
| `versions.md` | `cf-versions` | docs-agent | Dependency versions for doc lookups |
| `routes.md` | `cf-routes` | api-architect | API surface map |
| `notes.md` | `cf-note` | Any skill | Free-form findings, decisions, context |

Read all at once: `cf-read` · Single file: `cf-read notes`

`.claudefiles/` is gitignored — session state, not source.
