# Anthropic — Claude Code Best Practices

**URL:** https://code.claude.com/docs/en/best-practices (canonical, redirected from https://www.anthropic.com/engineering/claude-code-best-practices)

**One-line:** Anthropic's canonical guide on patterns for productive agentic coding with Claude Code, from environment setup to parallel-session scaling.

## Key practices covered

- **Context is the fundamental constraint.** "LLM performance degrades as context fills." Almost every recommendation traces back to protecting the context window.
- **Give Claude a way to verify its work** — tests, screenshots, linters, build commands. "This is the single highest-leverage thing you can do."
- **Explore → Plan → Implement → Commit.** Use Plan Mode for unfamiliar, multi-file, or ambiguous changes; skip it when the diff fits one sentence.
- **Specific prompts with scope, sources, and reference patterns** beat vague ones. Use `@file` refs, pasted images, piped data.
- **CLAUDE.md: short, human-readable, pruned ruthlessly.** "If Claude keeps doing something you don't want despite having a rule against it, the file is probably too long."
- **Skills over CLAUDE.md** for anything only sometimes relevant — loaded on demand.
- **Hooks for things that must happen every time** ("deterministic, unlike advisory CLAUDE.md").
- **Subagents for investigation and review** — they run in separate context windows.
- **Permission modes:** auto mode + allowlists + sandboxing beat click-through-everything.
- **CLI tools (`gh`, `aws`, `gcloud`) and MCP servers** are context-efficient for external services.
- **Non-interactive `claude -p`** for CI, pre-commit, fan-out across files.
- **Parallel sessions** (desktop worktrees, web VMs, agent teams) for Writer/Reviewer patterns.
- **Session hygiene:** `/clear` between unrelated tasks, `/rewind` checkpoints, `claude --continue`/`--resume`, `/rename` sessions like branches.
- **Named failure modes:** kitchen-sink session, correcting-over-and-over, over-specified CLAUDE.md, trust-then-verify gap, infinite exploration.

## Already in agentfiles

- **Skill suite in `agentfiles/<category>/.../SKILL.md`** with frontmatter — matches the `.claude/skills/` pattern exactly.
- **Hooks present** (`hooks/safety-gate.py`, `skill-logger.py`, session-start) — deterministic enforcement.
- **Orient-first workflow.** Executor is mandated to run `af context`/`af status` before routing — matches the "Explore first" phase.
- **Verification is mandatory.** `verification-before-completion` skill + executor rule ("verification is MANDATORY before reporting completion") directly implements the highest-leverage practice.
- **`tdd` skill** — aligns with "have one Claude write tests, then another write code to pass them."
- **Manager/executor split** maps to main-thread + subagent separation ("subagents for investigation and review").
- **`git-worktree-workflow` skill** — matches parallel-sessions guidance.
- **Pruned CLAUDE.md / AGENTS.md** with an explicit anti-bloat rule — directly honors the "ruthlessly prune" guidance.
- **Agent communication bus (`.agentfiles/`)** — a form of context-offloading so files don't live in the chat forever.
- **`af log review` loop** — matches "develop your intuition / pay attention to what works."

## Gaps / worth adopting

- **Plan Mode is not surfaced anywhere.** Executor jumps straight to routing. A "when to Plan Mode" rule (multi-file, unfamiliar code, ambiguous approach) belongs in executor.
- **No `AskUserQuestion`-driven interview skill.** The doc recommends starting larger features with an interview that writes `SPEC.md`, then a fresh session to execute. `brainstorming` exists but not wired to `AskUserQuestion`.
- **No canonical fan-out script pattern** using `claude -p` + `--allowedTools` for batch migrations. Would be a natural `af` subcommand (e.g., `af fan-out`).
- **Writer/Reviewer two-session pattern** is not a named skill. Given the manager/executor infra, a `reviewer-session` skill that explicitly opens a fresh context for review would be cheap.
- **Checkpoint / `/rewind` hygiene is not documented.** SESSION-CHECKLIST.md could mention "after two failed corrections, `/clear` and rewrite prompt."
- **`/btw` for side questions** — no guidance to use it for off-topic checks, which directly bloats logs today.
- **Auto mode and sandboxing** aren't mentioned in the install or hook docs. For unattended `af` runs this is the recommended default.
- **`disable-model-invocation: true`** pattern for side-effect skills is not used — could tighten skills like `install` or `fan-out`.

## Take-aways

1. **Add a Plan Mode trigger rule to `executor`** — mirror the "multi-file / unfamiliar / ambiguous" heuristic from the doc. Cheapest high-value change.
2. **Wire `brainstorming` to `AskUserQuestion` and produce `SPEC.md`** per the "let Claude interview you" pattern, explicitly advising a fresh session to execute.
3. **Document the `/clear`, `/rewind`, `--continue` discipline** in SESSION-CHECKLIST.md and the `using-agentfiles` skill — those are the named failure-mode antidotes and they cost nothing.

**Last checked:** 2026-04-18
