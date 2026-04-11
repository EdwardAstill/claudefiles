# Workflows Reference

End-to-end traces of common patterns — what happens at each stage, which skills run,
which scripts execute, which files are read and written.

---

## 1. New Machine Setup

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
```

| Step | What happens | Output |
|------|-------------|--------|
| Clone | Clones repo to `~/.local/share/claudefiles-src/` | Local clone |
| Install CLI | `uv tool install --force -e tools/python/` | `cf` command on PATH |
| Install skills | `install.sh --global` — builds flat symlinks, installs each skill | 39 skills in `~/.claude/skills/` |

All 39 skills active globally. Changes to skill files in the repo are live on the next
session — no reinstall needed.

---

## 2. Standard Task — Executor Path

**User:** Any new task request.

| Step | What happens | Tools |
|------|-------------|-------|
| Orient | `cf context` + `cf status` (MANDATORY) | Bash |
| Assess | Parallel agents needed? Almost always no. | Inline |
| Plan | 2–4 line approach for non-trivial tasks | — |
| Execute | Full tool access; load specialists inline as needed | Skill tool |
| Verify | **MANDATORY** — run tests, check output, report evidence | Bash, Read |
| Report | Evidence-based, not assertions | — |

### Specialist Loading During Execution

| Signal | Skill loaded |
|--------|-------------|
| Python type errors, toolchain | `python-expert` |
| Rust, Cargo, ownership issues | `rust-expert` |
| API design question | `api-architect` |
| Bug appears mid-task | `systematic-debugging` |
| Library API needed | `docs-agent` |
| Security concerns | `security-review` |
| Database work | `database-expert` |
| Performance issue | `performance-profiling` |
| About to finish | `verification-before-completion` |

Inline loading keeps full session context — no context loss.

---

## 3. Multi-Agent Task — Manager Path

**Trigger:** Executor escalates with HANDOFF CONTEXT block, or user invokes manager directly.

### Phase 1 — Plan

| Step | What happens |
|------|-------------|
| Read handoff | Parse HANDOFF CONTEXT: task, cf context, cf status, work done, why escalating |
| Read regions | `cat claudefiles/{coding,planning,research}/REGION.md` |
| Three questions | Design? Git strategy? Coordination? |
| Load advisors | `Skill("design-advisor")` / `Skill("git-advisor")` / `Skill("coordination-advisor")` — only if non-obvious |
| Confirm | Present plan to user. Wait for confirmation. |

### Phase 2 — Execute

| Pattern | When | How |
|---------|------|-----|
| Parallel agents | Independent domains, no shared state | Multiple Agent calls in one message |
| Sequential + gates | Tasks depend on each other | `subagent-driven-development` |
| Single specialist | Focused domain work | Single Agent call |

### Phase 3 — Review + Replan

| Step | What happens |
|------|-------------|
| Check conflicts | Did agents touch the same files? |
| Run tests | Full test suite on combined output |
| Evaluate | Did any agent fail or discover unexpected info? |
| Replan | If needed: re-dispatch, resequence, or re-run planning |

---

## 4. Feature Work — Worktree Path

**User:** "Build the auth feature" or any discrete feature needing isolation.

| Step | What happens |
|------|-------------|
| Assess | Is isolation needed? (new feature, risky changes, parallel work?) |
| Create worktree | `git worktree add ../worktree-<branch> -b <branch>` |
| Emit context | WORKTREE CONTEXT block for other skills |
| Implement | Executor or agents work inside the worktree |
| Complete | 4 options: merge locally, create PR, keep as-is, discard |
| Cleanup | `git worktree remove` |

---

## 5. Design-to-Implementation Path

**User:** "I want to add X" with unclear requirements or complex implementation.

| Step | Skill | Output |
|------|-------|--------|
| Clarify requirements | `brainstorming` | Spec at `docs/specs/YYYY-MM-DD-<topic>-design.md` |
| Write plan | `writing-plans` | Plan at `docs/plans/YYYY-MM-DD-<topic>.md` |
| Execute plan | `subagent-driven-development` | Committed, reviewed implementation |
| Finish | `git-worktree-workflow` (if applicable) | Merged or PR'd |

---

## 6. Research Workflows

### "How do I use X?" — docs-agent

| Step | What happens | Tools |
|------|-------------|-------|
| Check versions | `cf versions` for installed versions | Reads lockfiles |
| Fetch docs | context7 MCP → resolve library → fetch docs | `context7` |
| Supplement | WebSearch / WebFetch if context7 doesn't have it | Web tools |
| Output | Exact API, working example, source URL, version note | — |

### "Should I use X?" — research-agent

| Step | What happens | Tools |
|------|-------------|-------|
| Search | WebSearch across multiple sources | Web |
| Read | WebFetch on authoritative results | Web |
| Synthesize | Consensus, nuances, pitfalls, contradictions | — |
| Output | Structured report with confidence levels and recommendation | — |

### "How does this codebase work?" — codebase-explainer

| Step | What happens | Tools |
|------|-------------|-------|
| Orient | cf context, README, CLAUDE.md | Bash, Read |
| Map layers | Identify architecture layers and responsibilities | Grep, Glob |
| Trace path | Follow a key execution path end-to-end | Read, Grep |
| Identify abstractions | Core types, DI patterns, error handling | Grep |
| Output | Architecture map, execution trace, "where to look" guide | — |

---

## 7. Quality Gate Chain

The full quality pipeline, in order:

```
tdd                              write failing test first
  → implementation               make it pass
  → systematic-debugging         if something breaks: find root cause
  → security-review              if handles user input/auth
  → verification-before-completion   MANDATORY before claiming done
  → code-review                  before merge
  → simplify                     after merge, if needed
```

---

## 8. Agent Communication Bus

`.claudefiles/` is shared state — written by CLI tools, read by any skill.

| File | Written by | Read by | Content |
|------|-----------|---------|---------|
| `context.md` | `cf context` | executor, manager | Project fingerprint |
| `repo-map.md` | `cf status` | executor, git-expert | Git topology |
| `versions.md` | `cf versions` | docs-agent | Dependency versions |
| `routes.md` | `cf routes` | api-architect | API surface map |
| `notes.md` | `cf note` | any skill | Free-form findings |

Bootstrap all: `cf init` / Read all: `cf read` / Single: `cf read notes`
