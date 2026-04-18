# Skills vs Subagents

When to make something a **skill** (text loaded into the current conversation)
versus a **subagent** (separate Claude invocation, own context, returns a summary).

This is the rule the repo follows. It decides whether a new capability lives
under `agentfiles/<category>/<name>/SKILL.md` or `agentfiles/agents/<name>.md`.

---

## The rule

A capability should be a **subagent** only when all three of these hold:

1. **Output is verbose and you won't re-reference it.**
   Think logs, grep dumps, rubric scores, scan results — material the parent
   would immediately compress or ignore.

2. **Task is self-contained — clean input → summary out.**
   No back-and-forth with the user, no progressive file edits the user is
   watching land. One handoff in, one report out.

3. **You benefit from either tool restriction or context isolation.**
   Read-only audits, security scans, evaluators that shouldn't touch the
   working tree — or long-running research where parent-context bloat is the
   real cost.

If any of the three fails, it's a skill.

Source: [Claude Code subagent docs](https://code.claude.com/docs/en/sub-agents.md)
and [Claude Code skill docs](https://code.claude.com/docs/en/skills.md).

---

## Quick decision table

| Situation | Choose |
|---|---|
| Reference material, playbook, checklist | Skill |
| Iterative work with the user (TDD, debugging, refactoring) | Skill |
| Routing / orchestration / meta decisions | Skill |
| Progressive file edits the user is watching | Skill |
| Read-heavy scan, summary comes back | Subagent |
| Rubric-graded evaluation | Subagent |
| Needs tool restriction (read-only, narrow allowlist) | Subagent |
| Parallel work across independent domains | Subagent |

---

## Why the repo defaults to skills

Most capabilities here are procedures the main Claude should run *inline*, so
the user sees every tool call and can steer mid-run. Wrapping those in a
subagent loses visibility and iteration — the parent only gets a final summary.

Subagents pay off when the work is truly hand-off-and-forget, with verbose
byproducts the parent shouldn't absorb.

---

## What lives where

```
agentfiles/
  <category>/<name>/SKILL.md     # skills — inline, loaded on demand
  agents/<name>.md               # subagents — isolated, invoked via Agent tool
```

Skills and subagents are installed into separate harness locations:

| Source | Installed to | Loaded by |
|---|---|---|
| `agentfiles/<category>/<name>/SKILL.md` | `~/.claude/skills/<name>` | Skill tool |
| `agentfiles/agents/<name>.md` | `~/.claude/agents/<name>.md` | Agent tool |

Both are managed by `af install`. The flat `skills/` directory at the repo
root is the symlink registry the installer reads.

---

## Built-in subagents — don't use them

Claude Code ships built-in subagent types (`Explore`, `Plan`, `general-purpose`,
`feature-dev:code-architect`, etc.). **This repo does not use them.**

Reason: the repo aims to be self-contained. External dependencies on
built-ins mean the behavior of a skill can silently change when Claude Code
ships a new model or tweaks a prompt. Local copies live at
`agentfiles/agents/` and are versioned with the rest of the repo.

If a skill needs research, planning, or code review help, it dispatches to
the *local* copy (`research-agent`, `plan`, `code-reviewer`, etc.) — never to
a built-in.

---

## Current subagent inventory

Custom subagents shipped by this repo (see `agentfiles/agents/`):

| Name | Role |
|---|---|
| `skill-tester` | Rubric-grades a skill against hard benchmark questions |
| `audit` | Verifies manifest-vs-disk consistency, read-only |
| `security-review` | Scans code for OWASP/CVE/secrets, read-only |
| `explore` | General read-only codebase exploration (local copy of built-in) |
| `plan` | Read-only research for planning phase (local copy of built-in) |
| `general-purpose` | Multi-step read+write work (local copy of built-in) |
| `code-architect` | Feature architecture design (local copy of built-in) |
| `code-explorer` | Deep codebase analysis (local copy of built-in) |
| `code-reviewer` | Focused PR/code review (local copy of built-in) |
| `code-simplifier` | Refine code for clarity (local copy of built-in) |

Everything else in the repo is a skill.

---

## Anti-patterns

- **Skill as subagent.** Converting reference material or an iterative
  workflow to a subagent wastes context and loses user visibility.
- **Subagent for tiny tasks.** Spawning a subagent to "run the linter" costs
  a fresh context for no benefit.
- **Many subagents in parallel.** Results from N subagents all flood the
  parent. Use sparingly or chain sequentially.
- **Custom subagent replicating a built-in verbatim.** We do this
  *intentionally* in this repo (self-containment) — but if you only need
  vanilla exploration, the built-in is fine elsewhere. Here, always dispatch
  to the local copy.
- **Routing/orchestration as subagent.** The executor and manager layers
  must run in the main context to see the full conversation.

---

## Adding a new subagent

1. Write `agentfiles/agents/<name>.md` with frontmatter (`name`,
   `description`, optional `tools`, optional `model`).
2. Keep the body a short system prompt — it's the entire persona.
3. If the subagent replaces an existing skill, thin the SKILL.md down to a
   one-line dispatcher that calls the subagent via the Agent tool.
4. Add the entry to `manifest.toml` under `[agents.<name>]`.
5. Run `af install` to symlink into `~/.claude/agents/`.
6. Run `af audit` to verify manifest consistency.
