# claudefiles Full Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Absorb 14 superpowers skills into claudefiles, restructure dev-suite with a new `planning/` top-level category, fix infrastructure tooling, and expand language expert skills.

**Architecture:** Skills are copied verbatim from the superpowers plugin cache, `superpowers:*` cross-references replaced with plain skill names, placed into the new directory hierarchy. Dispatcher SKILL.md files are written by hand. Infrastructure changes are made to bin tools and scripts. No new runtime dependencies introduced.

**Tech Stack:** Bash, awk, SKILL.md (YAML frontmatter + markdown), TOML (manifest.toml)

**Key paths:**
- Repo root: `~/projects/claudefiles/`
- Superpowers source: `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.5/skills/`
- Dev suite: `dev-suite/`

**Spec:** `docs/superpowers/specs/2026-04-10-claudefiles-overhaul-design.md`

---

## File Map

### Created
| File | Notes |
|------|-------|
| `dev-suite/planning/SKILL.md` | New top-level dispatcher |
| `dev-suite/planning/brainstorming/SKILL.md` | Absorbed |
| `dev-suite/planning/brainstorming/visual-companion.md` | Absorbed |
| `dev-suite/planning/brainstorming/spec-document-reviewer-prompt.md` | Absorbed |
| `dev-suite/planning/writing-plans/SKILL.md` | Absorbed |
| `dev-suite/planning/writing-plans/plan-document-reviewer-prompt.md` | Absorbed |
| `dev-suite/planning/executing-plans/SKILL.md` | Absorbed |
| `dev-suite/management/meta/SKILL.md` | New sub-dispatcher |
| `dev-suite/management/meta/skill-manager/SKILL.md` | Moved + renamed from agent-manager |
| `dev-suite/management/meta/writing-skills/SKILL.md` | Absorbed |
| `dev-suite/management/meta/writing-skills/testing-skills-with-subagents.md` | Absorbed |
| `dev-suite/management/meta/writing-skills/anthropic-best-practices.md` | Absorbed |
| `dev-suite/management/meta/writing-skills/persuasion-principles.md` | Absorbed |
| `dev-suite/management/orchestration/dispatching-parallel-agents/SKILL.md` | Absorbed |
| `dev-suite/management/orchestration/subagent-driven-development/SKILL.md` | Absorbed |
| `dev-suite/management/orchestration/subagent-driven-development/implementer-prompt.md` | Absorbed |
| `dev-suite/management/orchestration/subagent-driven-development/code-quality-reviewer-prompt.md` | Absorbed |
| `dev-suite/management/orchestration/subagent-driven-development/spec-reviewer-prompt.md` | Absorbed |
| `dev-suite/coding/quality/tdd/SKILL.md` | Absorbed |
| `dev-suite/coding/quality/tdd/testing-anti-patterns.md` | Absorbed |
| `dev-suite/coding/quality/systematic-debugging/SKILL.md` | Absorbed |
| `dev-suite/coding/quality/systematic-debugging/root-cause-tracing.md` | Absorbed |
| `dev-suite/coding/quality/systematic-debugging/condition-based-waiting.md` | Absorbed |
| `dev-suite/coding/quality/systematic-debugging/defense-in-depth.md` | Absorbed |
| `dev-suite/coding/quality/verification-before-completion/SKILL.md` | Absorbed |
| `dev-suite/coding/quality/requesting-code-review/SKILL.md` | Absorbed |
| `dev-suite/coding/quality/requesting-code-review/code-reviewer.md` | Absorbed |
| `dev-suite/coding/quality/receiving-code-review/SKILL.md` | Absorbed |
| `dev-suite/coding/quality/simplify/SKILL.md` | Absorbed |
| `dev-suite/coding/version-control/git-worktree-workflow/SKILL.md` | Merged from 2 skills |
| `bin/cf-check` | New registry sync tool |

### Modified
| File | Change |
|------|--------|
| `dev-suite/management/SKILL.md` | Remove planning, add meta routing |
| `dev-suite/coding/quality/SKILL.md` | Replace placeholder with full routing table |
| `dev-suite/registry.md` | Add all new skill entries |
| `manifest.toml` | Add new skills + cf-check bin entry |
| `bin/cf-setup` | Replace Python TOML parser with awk |
| `bootstrap.sh` | Pre-flight checks + skill-manager references |
| `CLAUDE.md` | Add cf-check instruction |
| `dev-suite/coding/languages/python/SKILL.md` | Expand depth |
| `dev-suite/coding/languages/typescript/SKILL.md` | Expand depth |
| `dev-suite/coding/languages/rust/SKILL.md` | Expand depth |
| `dev-suite/coding/languages/typst/SKILL.md` | Expand depth |

### Deleted
| File | Why |
|------|-----|
| `dev-suite/management/planning/` | Empty dir — replaced by top-level planning/ |
| `dev-suite/management/agent-manager/SKILL.md` | Content moved to skill-manager |

---

## Task 1: Create directory structure

**Files:**
- Create: `dev-suite/planning/` (directory)
- Create: `dev-suite/management/meta/` (directory)
- Delete: `dev-suite/management/planning/` (empty directory)

- [ ] **Step 1: Create new directories**

```bash
mkdir -p dev-suite/planning
mkdir -p dev-suite/management/meta
```

- [ ] **Step 2: Remove the empty planning placeholder**

```bash
rmdir dev-suite/management/planning
```

Expected: no output (silent success). If it errors because the directory is not empty, inspect its contents before deleting.

- [ ] **Step 3: Verify structure**

```bash
ls dev-suite/planning dev-suite/management/meta
```

Expected: both directories exist (empty at this point)

- [ ] **Step 4: Commit**

```bash
git add dev-suite/planning dev-suite/management/meta
git commit -m "chore: create planning/ and management/meta/ directories"
```

---

## Task 2: Move and rename agent-manager → skill-manager

**Files:**
- Create: `dev-suite/management/meta/skill-manager/SKILL.md`
- Delete: `dev-suite/management/agent-manager/SKILL.md`

- [ ] **Step 1: Create the new directory and copy the file**

```bash
mkdir -p dev-suite/management/meta/skill-manager
cp dev-suite/management/agent-manager/SKILL.md dev-suite/management/meta/skill-manager/SKILL.md
```

- [ ] **Step 2: Update frontmatter name field**

In `dev-suite/management/meta/skill-manager/SKILL.md`, change:
```yaml
name: agent-manager
```
to:
```yaml
name: skill-manager
```

- [ ] **Step 3: Update title and internal references**

In the same file:
- Change `# Agent Manager` → `# Skill Manager`
- Change all occurrences of `agent-manager` → `skill-manager` in body text (the description and any body references)
- The section "## What Agent Manager Does NOT Do" → "## What Skill Manager Does NOT Do"
- Update the categories description: `management/` — orchestration (simple + complex), this skill → change to reflect new structure: orchestration, meta tooling (this skill + writing-skills)

- [ ] **Step 4: Remove old directory**

```bash
rm -rf dev-suite/management/agent-manager
```

- [ ] **Step 5: Verify**

```bash
cat dev-suite/management/meta/skill-manager/SKILL.md | grep "name:"
# Expected: name: skill-manager
ls dev-suite/management/agent-manager 2>&1
# Expected: No such file or directory
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: rename agent-manager to skill-manager, move to management/meta/"
```

---

## Task 3: Absorb planning skills

**Source:** `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.5/skills/`

**Files:**
- Create: `dev-suite/planning/brainstorming/SKILL.md` (+ 2 supporting files)
- Create: `dev-suite/planning/writing-plans/SKILL.md` (+ 1 supporting file)
- Create: `dev-suite/planning/executing-plans/SKILL.md`

- [ ] **Step 1: Copy brainstorming skill**

```bash
SP="$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.5/skills"
mkdir -p dev-suite/planning/brainstorming
cp "$SP/brainstorming/SKILL.md" dev-suite/planning/brainstorming/
cp "$SP/brainstorming/visual-companion.md" dev-suite/planning/brainstorming/
cp "$SP/brainstorming/spec-document-reviewer-prompt.md" dev-suite/planning/brainstorming/
```

- [ ] **Step 2: Copy writing-plans skill**

```bash
mkdir -p dev-suite/planning/writing-plans
cp "$SP/writing-plans/SKILL.md" dev-suite/planning/writing-plans/
cp "$SP/writing-plans/plan-document-reviewer-prompt.md" dev-suite/planning/writing-plans/
```

- [ ] **Step 3: Copy executing-plans skill**

```bash
mkdir -p dev-suite/planning/executing-plans
cp "$SP/executing-plans/SKILL.md" dev-suite/planning/executing-plans/
```

- [ ] **Step 4: Verify all files present**

```bash
find dev-suite/planning -name "*.md" | sort
```

Expected:
```
dev-suite/planning/brainstorming/SKILL.md
dev-suite/planning/brainstorming/spec-document-reviewer-prompt.md
dev-suite/planning/brainstorming/visual-companion.md
dev-suite/planning/executing-plans/SKILL.md
dev-suite/planning/writing-plans/SKILL.md
dev-suite/planning/writing-plans/plan-document-reviewer-prompt.md
```

- [ ] **Step 5: Commit**

```bash
git add dev-suite/planning/
git commit -m "feat: absorb planning skills from superpowers (brainstorming, writing-plans, executing-plans)"
```

---

## Task 4: Absorb orchestration execution skills

**Files:**
- Create: `dev-suite/management/orchestration/dispatching-parallel-agents/SKILL.md`
- Create: `dev-suite/management/orchestration/subagent-driven-development/SKILL.md` (+ 3 prompt files)

- [ ] **Step 1: Copy dispatching-parallel-agents**

```bash
SP="$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.5/skills"
mkdir -p dev-suite/management/orchestration/dispatching-parallel-agents
cp "$SP/dispatching-parallel-agents/SKILL.md" dev-suite/management/orchestration/dispatching-parallel-agents/
```

- [ ] **Step 2: Copy subagent-driven-development**

```bash
mkdir -p dev-suite/management/orchestration/subagent-driven-development
cp "$SP/subagent-driven-development/SKILL.md" dev-suite/management/orchestration/subagent-driven-development/
cp "$SP/subagent-driven-development/implementer-prompt.md" dev-suite/management/orchestration/subagent-driven-development/
cp "$SP/subagent-driven-development/code-quality-reviewer-prompt.md" dev-suite/management/orchestration/subagent-driven-development/
cp "$SP/subagent-driven-development/spec-reviewer-prompt.md" dev-suite/management/orchestration/subagent-driven-development/
```

- [ ] **Step 3: Verify**

```bash
find dev-suite/management/orchestration -name "*.md" | sort
```

Expected: 6 files total (2 existing + 5 new — SKILL.md files for the new skills plus prompt files)

- [ ] **Step 4: Commit**

```bash
git add dev-suite/management/orchestration/
git commit -m "feat: absorb dispatching-parallel-agents and subagent-driven-development"
```

---

## Task 5: Absorb meta skill (writing-skills)

**Files:**
- Create: `dev-suite/management/meta/writing-skills/SKILL.md` (+ 3 supporting files)

- [ ] **Step 1: Copy writing-skills**

```bash
SP="$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.5/skills"
mkdir -p dev-suite/management/meta/writing-skills
cp "$SP/writing-skills/SKILL.md" dev-suite/management/meta/writing-skills/
cp "$SP/writing-skills/testing-skills-with-subagents.md" dev-suite/management/meta/writing-skills/
cp "$SP/writing-skills/anthropic-best-practices.md" dev-suite/management/meta/writing-skills/
cp "$SP/writing-skills/persuasion-principles.md" dev-suite/management/meta/writing-skills/
```

- [ ] **Step 2: Remove broken references in SKILL.md**

The copied `writing-skills/SKILL.md` references two files that are NOT included:
- `@graphviz-conventions.dot` (a superpowers-internal file)
- `./render-graphs.js` (a superpowers-internal script)

In `dev-suite/management/meta/writing-skills/SKILL.md`:
- Remove the line referencing `@graphviz-conventions.dot`
- Remove the "Visualizing for your human partner" subsection that references `render-graphs.js`

- [ ] **Step 3: Verify**

```bash
grep -n "graphviz-conventions\|render-graphs" dev-suite/management/meta/writing-skills/SKILL.md
```

Expected: no output (references removed)

- [ ] **Step 4: Commit**

```bash
git add dev-suite/management/meta/writing-skills/
git commit -m "feat: absorb writing-skills from superpowers"
```

---

## Task 6: Absorb quality skills

**Files:** 6 skills in `dev-suite/coding/quality/`

- [ ] **Step 1: Copy tdd**

```bash
SP="$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.5/skills"
mkdir -p dev-suite/coding/quality/tdd
cp "$SP/test-driven-development/SKILL.md" dev-suite/coding/quality/tdd/
cp "$SP/test-driven-development/testing-anti-patterns.md" dev-suite/coding/quality/tdd/
```

Note: source directory is `test-driven-development/` but destination is `tdd/`. The `name:` field in the SKILL.md will need updating in Task 8 (it will currently say `test-driven-development` or `superpowers:test-driven-development`).

- [ ] **Step 2: Copy systematic-debugging**

```bash
mkdir -p dev-suite/coding/quality/systematic-debugging
cp "$SP/systematic-debugging/SKILL.md" dev-suite/coding/quality/systematic-debugging/
cp "$SP/systematic-debugging/root-cause-tracing.md" dev-suite/coding/quality/systematic-debugging/
cp "$SP/systematic-debugging/condition-based-waiting.md" dev-suite/coding/quality/systematic-debugging/
cp "$SP/systematic-debugging/defense-in-depth.md" dev-suite/coding/quality/systematic-debugging/
```

Note: Do NOT copy `test-pressure-*.md`, `test-academic.md`, or `CREATION-LOG.md` — these are superpowers eval artifacts.

- [ ] **Step 3: Copy verification-before-completion**

```bash
mkdir -p dev-suite/coding/quality/verification-before-completion
cp "$SP/verification-before-completion/SKILL.md" dev-suite/coding/quality/verification-before-completion/
```

- [ ] **Step 4: Copy requesting-code-review**

```bash
mkdir -p dev-suite/coding/quality/requesting-code-review
cp "$SP/requesting-code-review/SKILL.md" dev-suite/coding/quality/requesting-code-review/
cp "$SP/requesting-code-review/code-reviewer.md" dev-suite/coding/quality/requesting-code-review/
```

- [ ] **Step 5: Copy receiving-code-review**

```bash
mkdir -p dev-suite/coding/quality/receiving-code-review
cp "$SP/receiving-code-review/SKILL.md" dev-suite/coding/quality/receiving-code-review/
```

- [ ] **Step 6: Copy simplify**

```bash
mkdir -p dev-suite/coding/quality/simplify
cp "$SP/simplify/SKILL.md" dev-suite/coding/quality/simplify/
```

- [ ] **Step 7: Verify all quality skills present**

```bash
find dev-suite/coding/quality -name "SKILL.md" | sort
```

Expected: 7 files (existing dispatcher + 6 new leaf skills)

- [ ] **Step 8: Commit**

```bash
git add dev-suite/coding/quality/
git commit -m "feat: absorb quality skills (tdd, systematic-debugging, verification, review, simplify)"
```

---

## Task 7: Create merged git-worktree-workflow skill

**Files:**
- Create: `dev-suite/coding/version-control/git-worktree-workflow/SKILL.md`

The merged skill combines `using-git-worktrees` (setup phase) and `finishing-a-development-branch` (completion phase) into one coherent skill.

- [ ] **Step 1: Create the directory**

```bash
mkdir -p dev-suite/coding/version-control/git-worktree-workflow
```

- [ ] **Step 2: Read both source skills**

```bash
SP="$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.5/skills"
cat "$SP/using-git-worktrees/SKILL.md"
cat "$SP/finishing-a-development-branch/SKILL.md"
```

Read both in full before writing anything. The merged skill must faithfully combine them.

- [ ] **Step 3: Write the merged SKILL.md**

Write `dev-suite/coding/version-control/git-worktree-workflow/SKILL.md` with this structure:

```markdown
---
name: git-worktree-workflow
description: >
  Use when starting isolated feature work (creates a worktree with safety
  verification) or when implementation is complete and you need to merge,
  create a PR, or clean up. Covers the full worktree lifecycle: setup through
  completion.
---

# Git Worktree Workflow

Manages the full worktree lifecycle: create an isolated workspace to start,
clean up when done.

**Core principle:** Systematic directory selection + safety verification on
creation; verify tests → present options → execute + clean up on completion.

---

## Phase 1: Setup — Creating a Worktree

**Announce:** "Using git-worktree-workflow to set up an isolated workspace."

[Copy the full content of using-git-worktrees SKILL.md starting from
"## Directory Selection Process" through "## Red Flags" — omitting the
Overview (already covered above) and the Integration section at the end]

---

## Phase 2: Finishing — Completing the Work

**Announce:** "Using git-worktree-workflow to complete this work."

[Copy the full content of finishing-a-development-branch SKILL.md starting
from "## The Process" through "## Red Flags" — omitting the Overview and
Integration sections]

---

## Integration

**Setup is called by:**
- `brainstorming` — when design is approved and implementation follows
- `subagent-driven-development` — before executing any tasks
- `executing-plans` — before executing any tasks

**Finish is called by:**
- `subagent-driven-development` — after all tasks complete
- `executing-plans` — after all batches complete
```

Do not template-fill this — actually write the merged content by reading both source skills and combining them. The structure above is the skeleton; fill it with the real content from both source files.

- [ ] **Step 4: Verify the merged skill reads coherently**

Read the output file and confirm:
- Phase 1 section contains the full directory selection + safety verification + creation steps
- Phase 2 section contains the full verify tests → present 4 options → execute workflow
- No dangling references to `using-git-worktrees` or `finishing-a-development-branch` by those names (they're now one skill)

- [ ] **Step 5: Commit**

```bash
git add dev-suite/coding/version-control/git-worktree-workflow/
git commit -m "feat: create git-worktree-workflow (merged from using-git-worktrees + finishing-a-development-branch)"
```

---

## Task 8: Update superpowers:* cross-references

All absorbed SKILL.md files still reference `superpowers:*` names. Update them to plain names.

**Files:** All SKILL.md files under `dev-suite/planning/`, `dev-suite/management/meta/`, `dev-suite/management/orchestration/dispatching-parallel-agents/`, `dev-suite/management/orchestration/subagent-driven-development/`, `dev-suite/coding/quality/`, `dev-suite/coding/version-control/git-worktree-workflow/`

- [ ] **Step 1: Run find-and-replace for all superpowers: references**

```bash
# From repo root — run each substitution
find dev-suite -name "SKILL.md" -o -name "*.md" | xargs sed -i \
  -e 's/superpowers:brainstorming/brainstorming/g' \
  -e 's/superpowers:writing-plans/writing-plans/g' \
  -e 's/superpowers:executing-plans/executing-plans/g' \
  -e 's/superpowers:dispatching-parallel-agents/dispatching-parallel-agents/g' \
  -e 's/superpowers:subagent-driven-development/subagent-driven-development/g' \
  -e 's/superpowers:test-driven-development/tdd/g' \
  -e 's/superpowers:systematic-debugging/systematic-debugging/g' \
  -e 's/superpowers:verification-before-completion/verification-before-completion/g' \
  -e 's/superpowers:requesting-code-review/requesting-code-review/g' \
  -e 's/superpowers:receiving-code-review/receiving-code-review/g' \
  -e 's/superpowers:using-git-worktrees/git-worktree-workflow/g' \
  -e 's/superpowers:finishing-a-development-branch/git-worktree-workflow/g'
```

- [ ] **Step 2: Update tdd skill name in frontmatter**

The copied skill at `dev-suite/coding/quality/tdd/SKILL.md` has `name: superpowers:test-driven-development` or `name: test-driven-development` in its frontmatter. Change it to `name: tdd`.

- [ ] **Step 3: Verify no superpowers: references remain**

```bash
grep -r "superpowers:" dev-suite/ --include="*.md"
```

Expected: no output

- [ ] **Step 4: Verify tdd skill name**

```bash
grep "^name:" dev-suite/coding/quality/tdd/SKILL.md
```

Expected: `name: tdd`

- [ ] **Step 5: Commit**

```bash
git add dev-suite/
git commit -m "fix: update superpowers:* cross-references to plain skill names"
```

---

## Task 9: Create new dispatcher skills

**Files:**
- Create: `dev-suite/planning/SKILL.md`
- Create: `dev-suite/management/meta/SKILL.md`

- [ ] **Step 1: Write planning/SKILL.md**

```markdown
---
name: planning
description: >
  Category dispatcher for the planning lifecycle. Use when starting work on an
  idea without a design (brainstorming), when you have an approved spec and need
  an implementation plan (writing-plans), or when you have a plan and need to
  execute it (executing-plans).
---

# Planning

Routes to the right phase of the design-plan-execute lifecycle.

## Phases

| Skill | Use when |
|-------|----------|
| `brainstorming` | Have an idea or request — haven't designed it yet |
| `writing-plans` | Have an approved spec/design — need an implementation plan |
| `executing-plans` | Have a plan — handing off to a fresh parallel session |
```

- [ ] **Step 2: Write management/meta/SKILL.md**

```markdown
---
name: management-meta
description: >
  Sub-category dispatcher for skill system tooling. Use when the user wants to
  see, manage, or install skills (skill-manager) or when creating or editing
  a skill (writing-skills).
---

# Management Meta

Routes to skill system tooling.

## Skills

| Skill | Use when |
|-------|----------|
| `skill-manager` | Viewing, installing, or removing skills; setting up a new project |
| `writing-skills` | Creating a new skill or editing an existing one |
```

- [ ] **Step 3: Verify both files have valid frontmatter**

```bash
head -5 dev-suite/planning/SKILL.md
head -5 dev-suite/management/meta/SKILL.md
```

- [ ] **Step 4: Commit**

```bash
git add dev-suite/planning/SKILL.md dev-suite/management/meta/SKILL.md
git commit -m "feat: add planning/ and management/meta/ dispatcher skills"
```

---

## Task 10: Update existing dispatchers

**Files:**
- Modify: `dev-suite/management/SKILL.md`
- Modify: `dev-suite/coding/quality/SKILL.md`

- [ ] **Step 1: Rewrite management/SKILL.md**

Replace the entire file content with:

```markdown
---
name: management
description: >
  Category dispatcher for management and orchestration. Use when the task
  involves routing or planning a multi-step workflow (orchestration), managing
  or installing skills (meta), or creating a new skill (meta). For design and
  implementation planning, use the planning category instead.
---

# Management

Routes to orchestration or skill system meta tooling.

## Sub-categories

| Area | Use when |
|------|----------|
| `orchestration/` | Routing tasks, planning multi-skill workflows, executing plans with agents |
| `meta/` | Managing installed skills or authoring new skills |

## Orchestration skills

| Skill | Use when |
|-------|----------|
| `simple-orchestrator` | Start of any task — assesses complexity and routes |
| `complex-orchestrator` | Escalated tasks needing full multi-skill planning |
| `dispatching-parallel-agents` | Multiple independent tasks to run simultaneously |
| `subagent-driven-development` | Executing an implementation plan in the current session |

## Meta skills

| Skill | Use when |
|-------|----------|
| `skill-manager` | Viewing, installing, or removing skills across scopes |
| `writing-skills` | Creating or editing a skill |
```

- [ ] **Step 2: Rewrite coding/quality/SKILL.md**

Replace the entire file content with:

```markdown
---
name: coding-quality
description: >
  Sub-category dispatcher for code quality. Use when writing new features
  (tdd), encountering a bug or test failure (systematic-debugging), about to
  claim work is complete (verification-before-completion), completing
  implementation before merging (requesting-code-review), acting on review
  feedback (receiving-code-review), or cleaning up after implementation
  (simplify).
---

# Coding Quality

Routes to the right code quality skill based on the situation.

## Skills

| Skill | Use when |
|-------|----------|
| `tdd` | Before writing any implementation code |
| `systematic-debugging` | Bug, test failure, or unexpected behaviour |
| `verification-before-completion` | Before claiming work is done or creating a PR |
| `requesting-code-review` | After implementation, before merging |
| `receiving-code-review` | When acting on review feedback |
| `simplify` | After implementation — clean up and refine |
```

- [ ] **Step 3: Verify**

```bash
grep "name:" dev-suite/management/SKILL.md
grep "name:" dev-suite/coding/quality/SKILL.md
```

- [ ] **Step 4: Commit**

```bash
git add dev-suite/management/SKILL.md dev-suite/coding/quality/SKILL.md
git commit -m "feat: update management and coding/quality dispatchers to reflect new structure"
```

---

## Task 11: Update registry.md and manifest.toml

**Files:**
- Modify: `dev-suite/registry.md`
- Modify: `manifest.toml`

### registry.md

- [ ] **Step 1: Update the taxonomy section**

Replace the existing `Taxonomy` tree with:

```
dev-suite/
├── management/           ← orchestration and skill system tooling
│   ├── orchestration/
│   │   ├── simple-orchestrator
│   │   ├── complex-orchestrator
│   │   ├── dispatching-parallel-agents
│   │   └── subagent-driven-development
│   └── meta/
│       ├── skill-manager
│       └── writing-skills
├── planning/             ← design-plan-execute lifecycle
│   ├── brainstorming
│   ├── writing-plans
│   └── executing-plans
├── coding/               ← code writing, review, version control, API design
│   ├── quality/
│   │   ├── tdd
│   │   ├── systematic-debugging
│   │   ├── verification-before-completion
│   │   ├── requesting-code-review
│   │   ├── receiving-code-review
│   │   └── simplify
│   ├── version-control/
│   │   ├── git-expert
│   │   ├── github-expert
│   │   └── git-worktree-workflow
│   └── api/
│       └── api-architect
└── research/             ← technical reference, analysis, trade-offs
    ├── docs-agent
    └── research-agent
```

- [ ] **Step 2: Rename agent-manager entry to skill-manager**

In the existing `## agent-manager` section, change:
- Heading: `## agent-manager` → `## skill-manager`
- Purpose line: update to mention it's now in `management/meta/`

- [ ] **Step 3: Add new skill entries**

Add the following entries (after the existing entries, before the Chaining Patterns section):

```markdown
## brainstorming

- **Purpose:** Turn ideas into validated specs through collaborative design dialogue
- **Triggers when:** User has an idea or requirement that hasn't been designed yet
- **Inputs:** Raw idea or feature request
- **Outputs:** Approved spec document saved to `docs/superpowers/specs/`
- **Tools required:** Read, Write, Glob, Agent
- **Chains into:** `writing-plans`

---

## writing-plans

- **Purpose:** Create detailed implementation plans from approved specs
- **Triggers when:** Spec is approved and ready for implementation
- **Inputs:** Spec document path
- **Outputs:** Implementation plan saved to `docs/superpowers/plans/`
- **Tools required:** Read, Write
- **Chains into:** `subagent-driven-development` or `executing-plans`

---

## executing-plans

- **Purpose:** Execute implementation plans in a fresh parallel session with review checkpoints
- **Triggers when:** Plan is ready and user wants parallel session handoff
- **Inputs:** Plan document path
- **Outputs:** Implemented and reviewed code, committed to branch
- **Tools required:** Read, Agent
- **Chains into:** `git-worktree-workflow` (finish phase)

---

## dispatching-parallel-agents

- **Purpose:** Dispatch multiple agents to work on independent tasks simultaneously
- **Triggers when:** Multiple independent failures or tasks that can run concurrently
- **Inputs:** List of independent problem domains with scopes
- **Outputs:** Summaries from each agent; integrated fixes
- **Tools required:** Agent
- **Chains into:** Nothing — aggregates results from parallel agents

---

## subagent-driven-development

- **Purpose:** Execute implementation plans in current session using fresh subagents with two-stage review per task
- **Triggers when:** Plan is ready and user wants same-session execution with quality gates
- **Inputs:** Plan document path
- **Outputs:** Implemented, reviewed, and committed code
- **Tools required:** Read, Agent
- **Chains into:** `git-worktree-workflow` (finish phase), `requesting-code-review`

---

## skill-manager

- **Purpose:** Visibility and management of Claude Code skills across all scopes
- **Triggers when:** User asks what skills they have, wants to install or remove skills, or wants to set up a new project
- **Inputs:** Optional scope flag (global / project / available)
- **Outputs:** Skill inventory; install/remove actions
- **Tools required:** Bash, Read
- **Chains into:** Nothing — terminal skill

---

## writing-skills

- **Purpose:** TDD-based methodology for creating and improving skills
- **Triggers when:** Creating a new skill or editing an existing one
- **Inputs:** Skill concept or existing skill to improve
- **Outputs:** Tested and deployed skill file
- **Tools required:** Read, Write, Agent
- **Chains into:** Nothing — terminal skill

---

## tdd

- **Purpose:** Test-Driven Development — write tests before implementation code
- **Triggers when:** About to write any implementation code for a feature or bugfix
- **Inputs:** Feature description or bug report
- **Outputs:** Tests written and passing; implementation guided by tests
- **Tools required:** Bash, Read, Write
- **Chains into:** `verification-before-completion`, `requesting-code-review`

---

## systematic-debugging

- **Purpose:** Structured root-cause analysis for bugs and test failures
- **Triggers when:** Encountering a bug, test failure, or unexpected behaviour
- **Inputs:** Bug description, failing test output, or unexpected behaviour description
- **Outputs:** Root cause identified; minimal fix applied; tests passing
- **Tools required:** Bash, Read, Grep
- **Chains into:** `tdd` (if fix requires new tests), `verification-before-completion`

---

## verification-before-completion

- **Purpose:** Final verification gate before claiming work is done
- **Triggers when:** About to claim work is complete, fixed, or ready for review
- **Inputs:** List of requirements or acceptance criteria
- **Outputs:** Verification report; confirmed pass or list of remaining issues
- **Tools required:** Bash, Read
- **Chains into:** `requesting-code-review`

---

## requesting-code-review

- **Purpose:** Structured code review of completed implementation
- **Triggers when:** Implementation complete and verified; ready for review before merging
- **Inputs:** Git diff or file list; spec or requirements
- **Outputs:** Code review report with prioritised findings
- **Tools required:** Bash, Read, Agent
- **Chains into:** `git-worktree-workflow` (finish phase)

---

## receiving-code-review

- **Purpose:** Structured handling of incoming code review feedback
- **Triggers when:** Receiving review comments and about to act on them
- **Inputs:** Review comments
- **Outputs:** Implemented fixes; re-review confirmation
- **Tools required:** Read, Write, Bash
- **Chains into:** `verification-before-completion`, `requesting-code-review`

---

## simplify

- **Purpose:** Post-implementation cleanup — reduce complexity, improve clarity
- **Triggers when:** Implementation is working and tests pass; time to refine
- **Inputs:** Recently written or modified files
- **Outputs:** Cleaner, simpler code with same behaviour
- **Tools required:** Read, Write, Bash
- **Chains into:** `requesting-code-review`

---

## git-worktree-workflow

- **Purpose:** Full worktree lifecycle — create isolated workspace and complete/merge work
- **Triggers when:** Starting feature work needing isolation (setup phase) OR implementation is complete (finish phase)
- **Inputs:** Branch name and feature description (setup) OR completed branch (finish)
- **Outputs:** Ready worktree with clean baseline (setup) OR merged/PR'd branch with cleaned-up worktree (finish)
- **Tools required:** Bash
- **Chains into:** Implementation skills (after setup); nothing after finish
```

- [ ] **Step 4: Update the Chaining Patterns section**

Add these patterns:

```markdown
### Full Feature Flow (with planning)
```
simple-orchestrator → complex-orchestrator
  → brainstorming (idea → spec)
  → writing-plans (spec → plan)
  → git-worktree-workflow (setup worktree)
  → subagent-driven-development (execute plan)
  → git-worktree-workflow (finish + merge)
```

### Quality Gate Flow
```
tdd (write tests first)
  → [implementation]
  → verification-before-completion
  → requesting-code-review
  → git-worktree-workflow (finish)
```

### Parallel Debug
```
simple-orchestrator → dispatching-parallel-agents
  → systematic-debugging × N (one per independent failure domain)
```
```

### manifest.toml

- [ ] **Step 5: Update bin install list**

In `manifest.toml`, update the `[bin]` section:

```toml
[bin]
install = ["cf-worktree", "cf-status", "cf-context", "cf-versions", "cf-routes", "cf-note", "cf-init", "cf-read", "cf-agents", "cf-setup", "cf-check"]
```

- [ ] **Step 6: Add new skill entries to manifest.toml**

Add after the existing skill entries:

```toml
[skills.brainstorming]
tools = ["Read", "Write", "Glob", "Agent"]

[skills.writing-plans]
tools = ["Read", "Write"]

[skills.executing-plans]
tools = ["Read", "Agent"]

[skills.dispatching-parallel-agents]
tools = ["Agent"]

[skills.subagent-driven-development]
tools = ["Read", "Agent"]

[skills.skill-manager]
tools = ["Bash", "Read"]

[skills.writing-skills]
tools = ["Read", "Write", "Agent"]

[skills.tdd]
tools = ["Bash", "Read", "Write"]

[skills.systematic-debugging]
tools = ["Bash", "Read", "Grep"]

[skills.verification-before-completion]
tools = ["Bash", "Read"]

[skills.requesting-code-review]
tools = ["Bash", "Read", "Agent"]

[skills.receiving-code-review]
tools = ["Read", "Write", "Bash"]

[skills.simplify]
tools = ["Read", "Write", "Bash"]

[skills.git-worktree-workflow]
tools = ["Bash"]
```

- [ ] **Step 7: Commit**

```bash
git add dev-suite/registry.md manifest.toml
git commit -m "feat: update registry and manifest for all new skills"
```

---

## Task 12: Rewrite cf-setup Python → awk

**Files:**
- Modify: `bin/cf-setup`

The Python block (lines 71–186) parses `manifest.toml`, checks CLI dependencies, and formats output. Replace it with a pure bash+awk equivalent. Same behavior: same CLI flags, same output format, same `--write` behavior.

- [ ] **Step 1: Capture baseline output for comparison**

```bash
# Save output from current Python-based version
./bin/cf-setup --skills "git-expert,docs-agent" > /tmp/cf-setup-baseline.txt 2>&1
echo "Exit: $?" >> /tmp/cf-setup-baseline.txt
cat /tmp/cf-setup-baseline.txt
```

- [ ] **Step 2: Replace Python block with awk**

Replace the section from `OUTPUT="$(python3 -` through the closing `PYEOF` with a bash+awk implementation.

The awk implementation must:
1. Parse `[skills.NAME]` sections from `manifest.toml` — extract `tools`, `mcp`, `cli` arrays per skill
2. Parse `[cli.NAME]` sections — extract `manager`, `package`, `description`, `install` fields
3. For each installed skill name in `$INSTALLED_SKILLS`:
   - Look up its `cli` array from the parsed skills
   - For each CLI tool name: check `command -v TOOL` to detect if on PATH
   - Look up the tool's manager, package, description, install command from cli registry
   - Check if the package manager itself is on PATH
   - Format output: `  ✓  TOOL  [manager]  installed` or `  ✗  TOOL  [manager]  MISSING` with install instructions
4. Summarize used package managers (only those needed by the checked skills)
5. Print `All dependencies satisfied.` if no missing tools

Use a multi-pass approach with awk (or two awk invocations + bash loops) to build up the data and then format it.

- [ ] **Step 3: Run awk version and compare**

```bash
./bin/cf-setup --skills "git-expert,docs-agent" > /tmp/cf-setup-awk.txt 2>&1
diff /tmp/cf-setup-baseline.txt /tmp/cf-setup-awk.txt
```

Expected: no meaningful diff (whitespace differences acceptable; same ✓/✗ decisions and install commands)

- [ ] **Step 4: Test --write flag**

```bash
cd /tmp && mkdir -p test-cf-setup && cd test-cf-setup && git init -q
mkdir -p .claudefiles
~/projects/claudefiles/bin/cf-setup --skills "git-expert" --write
cat .claudefiles/deps.md
```

Expected: deps.md written with skill dependency report

- [ ] **Step 5: Commit**

```bash
git add bin/cf-setup
git commit -m "fix: replace Python TOML parser in cf-setup with pure awk"
```

---

## Task 13: Create bin/cf-check

**Files:**
- Create: `bin/cf-check`

`cf-check` walks `dev-suite/` for leaf skill SKILL.md files and verifies each has an entry in `registry.md`. A leaf skill is one whose directory contains no further subdirectories with SKILL.md files.

- [ ] **Step 1: Write cf-check**

```bash
#!/usr/bin/env bash
# cf-check — verify all leaf skills in dev-suite have a registry entry
#
# Usage:
#   cf-check           # check from current directory or installed location
#   cf-check --verbose # show passing entries too

set -euo pipefail

VERBOSE=false
for arg in "$@"; do
    [[ "$arg" == "--verbose" ]] && VERBOSE=true
done

# Locate dev-suite
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
SUITE="$SCRIPT_DIR/../dev-suite"
REGISTRY="$SUITE/registry.md"

if [[ ! -d "$SUITE" ]]; then
    echo "Error: dev-suite not found at $SUITE" >&2
    exit 1
fi

if [[ ! -f "$REGISTRY" ]]; then
    echo "Error: registry.md not found at $REGISTRY" >&2
    exit 1
fi

bold=""  green=""  red=""  reset=""
if [[ -t 1 ]]; then
    bold="\033[1m"; green="\033[0;32m"; red="\033[0;31m"; reset="\033[0m"
fi

missing=()
found=()

while IFS= read -r skill_md; do
    # Determine if this is a leaf skill: its directory has no child SKILL.md files
    skill_dir="$(dirname "$skill_md")"
    child_skills="$(find "$skill_dir" -mindepth 2 -name "SKILL.md" 2>/dev/null | head -1)"
    [[ -n "$child_skills" ]] && continue  # dispatcher — skip

    name="$(awk '/^name:/ { gsub(/^name: */, ""); print; exit }' "$skill_md" 2>/dev/null)"
    [[ -z "$name" ]] && continue

    if grep -q "^## $name" "$REGISTRY" 2>/dev/null; then
        found+=("$name")
        $VERBOSE && echo -e "  ${green}✓${reset}  $name"
    else
        missing+=("$name")
    fi
done < <(find "$SUITE" -name "SKILL.md" | sort)

echo ""
if [[ ${#missing[@]} -eq 0 ]]; then
    echo -e "  ${green}✓${reset}  Registry in sync — ${#found[@]} skills, all have entries"
    echo ""
    exit 0
else
    echo -e "  ${red}✗${reset}  ${#missing[@]} skill(s) missing from registry:"
    for name in "${missing[@]}"; do
        echo "       - $name"
    done
    echo ""
    echo "  Add entries to dev-suite/registry.md for the above skills."
    echo ""
    exit 1
fi
```

- [ ] **Step 2: Make executable**

```bash
chmod +x bin/cf-check
```

- [ ] **Step 3: Run against current state (should pass)**

```bash
./bin/cf-check --verbose
```

Expected: all skills pass (✓ for each). If any fail, the registry was not fully updated in Task 11 — fix those entries before continuing.

- [ ] **Step 4: Test failure case**

```bash
# Temporarily add a skill without a registry entry, verify cf-check catches it
mkdir -p dev-suite/coding/quality/fake-test-skill
echo -e "---\nname: fake-test-skill\ndescription: temporary test\n---" > dev-suite/coding/quality/fake-test-skill/SKILL.md
./bin/cf-check
echo "Exit code: $?"
# Expected: exits 1, lists fake-test-skill as missing

# Clean up
rm -rf dev-suite/coding/quality/fake-test-skill
./bin/cf-check
echo "Exit code: $?"
# Expected: exits 0
```

- [ ] **Step 5: Commit**

```bash
git add bin/cf-check
git commit -m "feat: add cf-check — registry sync verification tool"
```

---

## Task 14: Update bootstrap.sh

**Files:**
- Modify: `bootstrap.sh`

Two changes: (1) add pre-flight dependency checks, (2) update all `agent-manager` references to `skill-manager`.

- [ ] **Step 1: Add pre-flight block**

After the `set -euo pipefail` line (line 24) and before the variable declarations, add:

```bash
# ── Pre-flight checks ─────────────────────────────────────────────────────────

for cmd in git bash curl; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: '$cmd' is required but not installed." >&2
        echo "Install $cmd before running bootstrap.sh." >&2
        exit 1
    fi
done
```

- [ ] **Step 2: Update agent-manager → skill-manager references**

In `bootstrap.sh`:
- Section header: `"2 / 3  Installing agent-manager skill"` → `"2 / 3  Installing skill-manager skill"`
- Comment: `# Find agent-manager by searching...` → `# Find skill-manager by searching...`
- Variable: `if [[ "$found_name" == "agent-manager" ]]` → `if [[ "$found_name" == "skill-manager" ]]`
- Error message: `agent-manager skill not found` → `skill-manager skill not found`
- Variable: `LINK="$SKILLS_TARGET/agent-manager"` → `LINK="$SKILLS_TARGET/skill-manager"`
- ok messages: `agent-manager already linked` → `skill-manager already linked`
- Footer text: `agent-manager is installed globally` → `skill-manager is installed globally`
- Footer instruction: update "Set up this project" message to reference `skill-manager`

- [ ] **Step 3: Test the pre-flight**

```bash
# Verify the pre-flight block runs (these tools exist so it should pass through)
bash -c 'source bootstrap.sh 2>&1 | head -5' || true
```

Actually just verify syntax is valid:

```bash
bash -n bootstrap.sh
echo "Syntax OK: $?"
```

Expected: `Syntax OK: 0`

- [ ] **Step 4: Commit**

```bash
git add bootstrap.sh
git commit -m "fix: add pre-flight checks to bootstrap.sh; rename agent-manager to skill-manager"
```

---

## Task 15: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the taxonomy in Key Facts**

In the `Key Facts` section, update the registry line to reference the new 4-category structure:
- Change `management/`, `coding/`, `research/` to mention `planning/` as well

- [ ] **Step 2: Add cf-check instruction**

In the `Registry Sync Rule` section, add:

```
Run `cf-check` before committing any changes to `dev-suite/` to verify all leaf
skills have registry entries.
```

- [ ] **Step 3: Update agent-manager references**

Search for `agent-manager` in CLAUDE.md and replace with `skill-manager`.

- [ ] **Step 4: Verify**

```bash
grep -n "agent-manager" CLAUDE.md
```

Expected: no output

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md — cf-check instruction, skill-manager rename, planning category"
```

---

## Task 16: Expand python-expert

**Files:**
- Modify: `dev-suite/coding/languages/python/SKILL.md`

The current skill has a solid base. Expand with missing sections to match git-expert depth.

- [ ] **Step 1: Add Testing Workflow section**

Add after the `## Anti-patterns` section:

```markdown
## Testing

**Framework:** pytest — always `uv run pytest`, never `python -m pytest` directly

**Structure:**
```
tests/
  conftest.py         # shared fixtures
  unit/               # pure function tests, no I/O
  integration/        # tests that hit real deps (db, filesystem, network)
```

**Fixtures over setUp/tearDown:**
```python
@pytest.fixture
def db_session():
    session = create_session()
    yield session
    session.rollback()
    session.close()
```

**Parametrize for coverage:**
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("", ""),
    ("123", "123"),
])
def test_upper(input, expected):
    assert input.upper() == expected
```

**Run subset during development:**
```bash
uv run pytest tests/unit/ -v           # unit only
uv run pytest -k "test_auth" -v        # by name pattern
uv run pytest --tb=short               # concise tracebacks
```

**Coverage:**
```bash
uv run pytest --cov=src --cov-report=term-missing
```
```

- [ ] **Step 2: Add Package Management section**

Add after Testing:

```markdown
## Package Management (uv)

**New project:**
```bash
uv init my-project          # creates pyproject.toml, .python-version, .venv
uv add requests fastapi     # add dependencies
uv add --dev pytest ruff    # dev-only dependencies
```

**Lock file:** `uv.lock` — always commit this. Reproduces exact dependency tree.

**Run commands:**
```bash
uv run python main.py       # runs in project venv
uv run pytest               # runs pytest from project venv
uv sync                     # install all deps from lock file
```

**Tools (global installs):**
```bash
uv tool install ruff         # install globally, not per-project
uvx ruff check .             # run without installing
```

**Workspace (monorepo):**
```toml
# pyproject.toml at root
[tool.uv.workspace]
members = ["packages/*"]
```
```

- [ ] **Step 3: Add Common Mistakes section**

```markdown
## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `python` instead of `uv run` | Always `uv run python` — ensures correct venv |
| Committing without running `ruff format` | Add `uv run ruff format .` to pre-commit |
| Missing type hints on public functions | Add them — pyright can't help without them |
| `from module import *` | Always explicit imports |
| Pinning to exact versions in library code | Use `>=` ranges in libraries, `uv.lock` for apps |
| Catching `Exception` in tests | Let it propagate — don't hide failures |
```

- [ ] **Step 4: Commit**

```bash
git add dev-suite/coding/languages/python/SKILL.md
git commit -m "feat: expand python-expert with testing, package management, common mistakes"
```

---

## Task 17: Expand typescript-expert

**Files:**
- Modify: `dev-suite/coding/languages/typescript/SKILL.md`

- [ ] **Step 1: Add Testing Workflow section**

Add after `## Anti-patterns`:

```markdown
## Testing

**Runner:** `bun test` — built-in, no config needed. Falls back to vitest for complex setups.

**Structure:**
```
src/
  feature.ts
  feature.test.ts    # co-locate tests with source
tests/
  integration/       # tests that need real deps
```

**bun test basics:**
```typescript
import { describe, test, expect, beforeEach } from 'bun:test'

describe('UserService', () => {
  beforeEach(() => { /* reset state */ })

  test('creates a user with valid input', () => {
    const user = createUser({ name: 'Alice', email: 'alice@example.com' })
    expect(user.id).toBeDefined()
    expect(user.name).toBe('Alice')
  })

  test('throws on invalid email', () => {
    expect(() => createUser({ name: 'Bob', email: 'not-an-email' }))
      .toThrow('Invalid email')
  })
})
```

**Run:**
```bash
bun test                      # all tests
bun test --watch              # re-run on change
bun test src/feature.test.ts  # specific file
```

**Mock with bun:test:**
```typescript
import { mock, spyOn } from 'bun:test'
const fetchMock = mock(() => Promise.resolve({ ok: true }))
```
```

- [ ] **Step 2: Add Package Management section**

```markdown
## Package Management

**New project:**
```bash
bun init              # creates package.json, tsconfig.json, index.ts
bun add express       # add dependency
bun add -d @types/node vitest  # dev dependency
```

**Lock file:** `bun.lockb` — binary lockfile, always commit. Use `bun install --frozen-lockfile` in CI.

**Scripts in package.json:**
```json
{
  "scripts": {
    "dev": "bun run --watch src/index.ts",
    "build": "bun build src/index.ts --outdir dist",
    "test": "bun test",
    "typecheck": "tsc --noEmit"
  }
}
```

**Workspaces:**
```json
{
  "workspaces": ["packages/*"]
}
```

**Run a file directly:**
```bash
bun src/index.ts     # no compile step needed
```
```

- [ ] **Step 3: Add Common Mistakes section**

```markdown
## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Missing `"strict": true` in tsconfig | Always start strict — costs more to add later |
| `as any` to silence type errors | Fix the type — `any` breaks the whole safety model |
| Mutating objects directly | Prefer immutable updates: `{ ...obj, field: newValue }` |
| Floating promises `doThing()` without await | `void doThing()` if intentional, `await` otherwise |
| `require()` in new code | Always `import` — `require()` loses types |
| `JSON.parse()` without validation | Use zod or valibot to parse external data |
| Class for a single function | Plain function or object literal instead |
```

- [ ] **Step 4: Commit**

```bash
git add dev-suite/coding/languages/typescript/SKILL.md
git commit -m "feat: expand typescript-expert with testing, package management, common mistakes"
```

---

## Task 18: Expand rust-expert

**Files:**
- Modify: `dev-suite/coding/languages/rust/SKILL.md`

Read the current `dev-suite/coding/languages/rust/SKILL.md` first to understand what's already there, then add the missing sections following the same pattern as python-expert and typescript-expert expansions.

- [ ] **Step 1: Read current skill**

```bash
cat dev-suite/coding/languages/rust/SKILL.md
```

- [ ] **Step 2: Add any missing sections from this list**

Ensure the skill covers:
- LSP (rust-analyzer): diagnostics, hover, inlay hints
- Toolchain: rustup, cargo, rustfmt, clippy, cargo-nextest
- Testing workflow: `cargo test`, `#[cfg(test)]`, `cargo nextest run`, integration tests in `tests/`
- Package management: Cargo.toml, workspace members, features, `cargo add`
- Idiomatic patterns: ownership, borrowing, error handling with `?` and `thiserror`/`anyhow`, iterators over loops
- Anti-patterns: `clone()` overuse, `unwrap()` in production code, ignoring `clippy` warnings
- Common mistakes with fixes

- [ ] **Step 3: Commit**

```bash
git add dev-suite/coding/languages/rust/SKILL.md
git commit -m "feat: expand rust-expert with testing, package management, common mistakes"
```

---

## Task 19: Expand typst-expert

**Files:**
- Modify: `dev-suite/coding/languages/typst/SKILL.md`

- [ ] **Step 1: Read current skill**

```bash
cat dev-suite/coding/languages/typst/SKILL.md
```

- [ ] **Step 2: Add any missing sections from this list**

Ensure the skill covers:
- LSP (tinymist): diagnostics, hover, symbol completion
- Toolchain: `typst compile`, `typst watch`, tinymist server
- Document structure: `set`, `show`, `let`, import patterns, `#include`
- Common document types: article, thesis, CV, slides (using `polylux` or `touying`)
- Package management: `typst.toml`, universe packages via `#import "@preview/..."`
- Anti-patterns: inline styles instead of `show` rules, hardcoded spacing
- Common mistakes: missing `#` for code, string vs content, math mode

- [ ] **Step 3: Commit**

```bash
git add dev-suite/coding/languages/typst/SKILL.md
git commit -m "feat: expand typst-expert with toolchain, document patterns, common mistakes"
```

---

## Task 20: Final verification

- [ ] **Step 1: Run cf-check**

```bash
./bin/cf-check --verbose
```

Expected: all leaf skills have registry entries, exit code 0

- [ ] **Step 2: Verify no superpowers: references remain**

```bash
grep -r "superpowers:" dev-suite/ --include="*.md"
```

Expected: no output

- [ ] **Step 3: Verify agent-manager is fully replaced**

```bash
grep -r "agent-manager" dev-suite/ bin/ bootstrap.sh CLAUDE.md
```

Expected: no output

- [ ] **Step 4: Verify all 14 absorbed skill directories exist**

```bash
find dev-suite -name "SKILL.md" | wc -l
```

Expected: at least 31 (the File Map at the top of this plan lists all created files). Cross-check against that list if the count is lower.

- [ ] **Step 5: Validate YAML frontmatter on all new skills**

```bash
# Check all new skills have both name and description fields
find dev-suite -name "SKILL.md" | while read f; do
  name=$(grep "^name:" "$f")
  desc=$(grep "^description:" "$f")
  if [[ -z "$name" || -z "$desc" ]]; then
    echo "MISSING FRONTMATTER: $f"
  fi
done
```

Expected: no output

- [ ] **Step 6: Final commit if any loose ends**

```bash
git add -A
git status
# Only commit if there are meaningful changes not yet committed
```

- [ ] **Step 7: Summary**

Run `cf-agents --tree` to verify the full live hierarchy matches the spec.
