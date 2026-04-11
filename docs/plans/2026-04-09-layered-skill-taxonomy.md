# Layered Skill Taxonomy — Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure dev-suite/ into a layered category taxonomy (management, coding, research) with category dispatcher skills, update cf agents and agent-manager to display the hierarchy as a tree, and add --category support to install.sh.

**Architecture:** Move existing skills into category subdirectories, create a SKILL.md dispatcher at each category and sub-category level, update all internal references, then update tooling to be hierarchy-aware.

**Tech Stack:** Bash, SKILL.md (YAML frontmatter + markdown)

---

## File Structure

### Files to move (git mv)
- `dev-suite/simple-orchestrator/` → `dev-suite/management/orchestration/simple-orchestrator/`
- `dev-suite/complex-orchestrator/` → `dev-suite/management/orchestration/complex-orchestrator/`
- `dev-suite/agent-manager/` → `dev-suite/management/agent-manager/`
- `dev-suite/git-expert/` → `dev-suite/coding/version-control/git-expert/`
- `dev-suite/github-expert/` → `dev-suite/coding/version-control/github-expert/`
- `dev-suite/api-architect/` → `dev-suite/coding/api/api-architect/`
- `dev-suite/docs-agent/` → `dev-suite/research/docs-agent/`
- `dev-suite/research-agent/` → `dev-suite/research/research-agent/`

### Files to create
- `dev-suite/management/SKILL.md`
- `dev-suite/coding/SKILL.md`
- `dev-suite/coding/quality/SKILL.md`
- `dev-suite/research/SKILL.md`
- `dev-suite/management/planning/` (empty dir, placeholder for future)

### Files to update
- `dev-suite/registry.md` — update all paths and add category section
- `dev-suite/management/orchestration/complex-orchestrator/SKILL.md` — registry path
- `dev-suite/coding/version-control/git-expert/SKILL.md` — lib/ path refs
- `install.sh` — add --category flag
- `manifest.toml` — update skill paths
- `bin/cf agents` — show tree structure
- `dev-suite/management/agent-manager/SKILL.md` — document hierarchy
- `README.md` — update structure diagram
- `CLAUDE.md` — update structure description

---

## Task 1: Move skill directories

**Files:**
- All existing skill dirs under dev-suite/

- [ ] **Step 1: Create category directory scaffold**

```bash
mkdir -p dev-suite/management/orchestration
mkdir -p dev-suite/management/planning
mkdir -p dev-suite/management/agent-manager
mkdir -p dev-suite/coding/version-control
mkdir -p dev-suite/coding/api
mkdir -p dev-suite/coding/quality
mkdir -p dev-suite/research
```

- [ ] **Step 2: git mv all skills into new locations**

```bash
git mv dev-suite/simple-orchestrator dev-suite/management/orchestration/simple-orchestrator
git mv dev-suite/complex-orchestrator dev-suite/management/orchestration/complex-orchestrator
git mv dev-suite/agent-manager dev-suite/management/agent-manager
git mv dev-suite/git-expert dev-suite/coding/version-control/git-expert
git mv dev-suite/github-expert dev-suite/coding/version-control/github-expert
git mv dev-suite/api-architect dev-suite/coding/api/api-architect
git mv dev-suite/docs-agent dev-suite/research/docs-agent
git mv dev-suite/research-agent dev-suite/research/research-agent
```

- [ ] **Step 3: Verify structure**

```bash
find dev-suite -name "SKILL.md" | sort
```

Expected: 8 SKILL.md files in their new locations, none at dev-suite root level (except registry.md stays).

---

## Task 2: Write category dispatcher SKILL.md files

**Files:**
- Create: `dev-suite/management/SKILL.md`
- Create: `dev-suite/coding/SKILL.md`
- Create: `dev-suite/coding/quality/SKILL.md`
- Create: `dev-suite/research/SKILL.md`

- [ ] **Step 1: Write dev-suite/management/SKILL.md**

```markdown
---
name: management
description: >
  Category dispatcher for management and orchestration tasks. Use when the task
  involves planning a multi-step workflow, managing Claude Code agents and skills,
  or understanding the current agent setup. Routes to: simple-orchestrator (always-on
  triage), complex-orchestrator (full multi-skill planning), agent-manager (skill
  visibility and install management), or planning sub-skills.
---

# Management

Routes to the right management or orchestration skill based on the task.

## Sub-skills

| Skill | Use when |
|-------|----------|
| `simple-orchestrator` | Start of any task — assesses complexity and routes |
| `complex-orchestrator` | Escalated tasks needing full multi-skill planning |
| `agent-manager` | Viewing or managing installed skills across scopes |
| `planning/*` | Brainstorming, writing plans, executing plans |
```

- [ ] **Step 2: Write dev-suite/coding/SKILL.md**

```markdown
---
name: coding
description: >
  Category dispatcher for coding tasks. Use when the task involves writing,
  reviewing, or improving code. Routes to: quality sub-skills (tdd, debugging,
  verification, code-review), version-control (git-expert for local git ops,
  github-expert for GitHub/gh CLI), or api-architect (API design and review).
---

# Coding

Routes to the right coding skill based on the task.

## Sub-categories and skills

| Skill | Use when |
|-------|----------|
| `coding-quality` | Any code quality concern — TDD, debugging, verification, review |
| `git-expert` | Local git operations, worktrees, branching, merge |
| `github-expert` | GitHub — PRs, issues, Actions, browsing external repos |
| `api-architect` | Designing or reviewing API contracts |
```

- [ ] **Step 3: Write dev-suite/coding/quality/SKILL.md**

```markdown
---
name: coding-quality
description: >
  Sub-category dispatcher for code quality. Use when writing new features (TDD),
  encountering bugs (systematic-debugging), about to claim work is done
  (verification-before-completion), or handling code review (requesting or
  receiving). Routes to the appropriate quality skill based on the situation.
---

# Coding Quality

Routes to the right code quality skill.

## Skills (coming soon)

| Skill | Use when |
|-------|----------|
| `tdd` | Before writing any implementation code |
| `systematic-debugging` | Bug, test failure, or unexpected behaviour |
| `verification-before-completion` | Before claiming work is done or creating a PR |
| `requesting-code-review` | After implementation, before merging |
| `receiving-code-review` | When acting on review feedback |
| `simplify` | After implementation — clean up and refine |
```

- [ ] **Step 4: Write dev-suite/research/SKILL.md**

```markdown
---
name: research
description: >
  Category dispatcher for research tasks. Use when you need information before
  acting. Routes to: docs-agent for technical reference (exact APIs, library usage,
  versioned documentation) or research-agent for broader analysis (trade-offs,
  consensus, risks, critical thinking across sources).
---

# Research

Routes to the right research skill based on the task.

## Sub-skills

| Skill | Use when |
|-------|----------|
| `docs-agent` | "How do I use X?" — exact API, config option, working example |
| `research-agent` | "Should I use X?" — trade-offs, risks, expert consensus |
```

- [ ] **Step 5: Verify all 4 category SKILL.md files exist**

```bash
find dev-suite -name "SKILL.md" | sort
```

Expected: 12 SKILL.md files total (8 leaf + 4 category).

---

## Task 3: Update internal references

**Files:**
- Modify: `dev-suite/management/orchestration/complex-orchestrator/SKILL.md`
- Modify: `dev-suite/coding/version-control/git-expert/SKILL.md`
- Modify: `dev-suite/registry.md`

- [ ] **Step 1: Fix registry.md — add category context and update structure**

Add a TAXONOMY section at the top of registry.md describing the three categories
and their sub-skills. No path changes needed since registry is read by name not path.

- [ ] **Step 2: Fix complex-orchestrator registry path reference**

The complex-orchestrator reads `dev-suite/registry.md` — check it still references
the right relative path. No change needed if it uses a relative path from the claudefiles root.

- [ ] **Step 3: Fix git-expert lib/ path reference**

git-expert/SKILL.md references `lib/port-finder.sh` and `bin/cf status` — these
paths are relative to the claudefiles root, not the skill file. Verify the references
still make sense and are clear to the reader.

---

## Task 4: Update install.sh with --category support

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add CATEGORY variable and argument parsing**

Add `--category <name>` flag. Valid categories: `management`, `coding`, `research`, `all` (default).

- [ ] **Step 2: Update symlink logic to respect category**

When `--category coding` is given, symlink `dev-suite/coding/` as `~/.claude/skills/cf-coding/`
instead of the full `dev-suite/` as `~/.claude/skills/dev-suite/`.

Full install (no --category) still symlinks the entire dev-suite/.

- [ ] **Step 3: Verify dry-run shows correct paths**

```bash
./install.sh --user --category coding --dry-run
./install.sh --user --dry-run
```

---

## Task 5: Update cf agents to show tree structure

**Files:**
- Modify: `bin/cf agents`

- [ ] **Step 1: Replace flat skill listing with tree rendering**

When displaying user skills or project skills, detect if the directory contains
category subdirectories (has SKILL.md at non-leaf level) and render as a tree:

```
dev-suite/
├── management/         [category]
│   ├── orchestration/
│   │   ├── simple-orchestrator
│   │   └── complex-orchestrator
│   └── agent-manager
├── coding/             [category]
│   ├── quality/        [category — 0 skills installed]
│   ├── version-control/
│   │   ├── git-expert
│   │   └── github-expert
│   └── api/
│       └── api-architect
└── research/           [category]
    ├── docs-agent
    └── research-agent
```

- [ ] **Step 2: Add --tree flag to always show tree regardless of scope**

```bash
cf agents --tree
```

- [ ] **Step 3: Test tree output**

```bash
bash bin/cf agents --available
bash bin/cf agents --tree
```

---

## Task 6: Update agent-manager SKILL.md

**Files:**
- Modify: `dev-suite/management/agent-manager/SKILL.md`

- [ ] **Step 1: Add hierarchy section explaining the category structure**

Document the three categories, how to install per-category, and how cf agents --tree
shows the full picture.

---

## Task 7: Update README.md and CLAUDE.md

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update README structure diagram to show layered taxonomy**

- [ ] **Step 2: Update CLAUDE.md adding-a-new-skill checklist to include category placement**

---

## Task 8: Commit and push

- [ ] **Step 1: Stage all changes**

```bash
git add -A
git status   # review what's staged
```

- [ ] **Step 2: Commit**

```bash
git commit -m "refactor: restructure dev-suite into layered category taxonomy

management/ (orchestration, planning, agent-manager)
coding/ (quality, version-control, api)
research/ (docs-agent, research-agent)

Add category dispatcher SKILL.md at each level.
Add --category flag to install.sh.
Update cf agents to render skills as a tree.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

- [ ] **Step 3: Push**

```bash
git push
```

---

## Verification

After all tasks:

1. `find dev-suite -name "SKILL.md" | sort` — 12 files in correct locations
2. `./install.sh --user --dry-run` — symlinks dev-suite/ correctly
3. `./install.sh --user --category coding --dry-run` — symlinks only coding/
4. `bash bin/cf agents --tree` — renders tree with categories
5. New Claude Code session — all 12 skills appear in system-reminder
6. Invoke `/management` — routes correctly
7. Invoke `/research` — routes to docs-agent or research-agent correctly
