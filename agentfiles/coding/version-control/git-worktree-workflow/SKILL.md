---
name: git-worktree-workflow
description: >
  Use for the full git-worktree lifecycle — starting isolated feature
  work in a new worktree and, later, merging/PR'ing/cleaning up when the
  work is done. Trigger phrases: "start a new feature in a worktree",
  "set up an isolated workspace for this", "spin up a worktree for
  parallel work", "I'm done with this worktree — merge and clean up",
  "create a PR from this worktree", "finalize and remove the
  worktree", "verify tests pass before merging the worktree", "split
  off parallel agent work", "which worktree am I supposed to be in",
  "bootstrap the worktree with a clean test baseline". Handles
  directory selection, safety verification on create, and
  verify→present-options→execute+cleanup on finish. Do NOT use for
  one-off git commands / history / branches (use git-expert), for
  GitHub-side operations like opening the PR itself (use
  github-expert), or for CI config (use github-actions-expert).
---

# Git Worktree Workflow

Manages the full worktree lifecycle: create an isolated workspace to start,
clean up and integrate when done.

**Core principle:** Systematic directory selection + safety verification on
creation; verify tests → present options → execute + clean up on completion.

---

## Phase 1: Setup — Creating a Worktree

**Announce at start:** "Using git-worktree-workflow to set up an isolated workspace."

### Directory Selection

Follow this priority order:

**1. Check existing directories**

```bash
ls -d .worktrees 2>/dev/null     # preferred (hidden)
ls -d worktrees 2>/dev/null      # alternative
```

If found, use that directory. If both exist, `.worktrees` wins.

**2. Check CLAUDE.md**

```bash
grep -i "worktree.*director" CLAUDE.md 2>/dev/null
```

If a preference is specified, use it without asking.

**3. Ask the user**

If no directory exists and no CLAUDE.md preference:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden)
2. ~/.config/worktrees/<project-name>/ (global location)

Which would you prefer?
```

### Safety Verification

**For project-local directories (.worktrees or worktrees):**

Verify the directory is git-ignored before creating the worktree:

```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

If NOT ignored — add the line to `.gitignore`, commit the change, then proceed.

Why this matters: prevents accidentally committing worktree contents to the repository.

**For global directories** (`~/.config/worktrees`): no .gitignore verification needed — outside the project entirely.

### Creation Steps

#### Fast path — `gwt`

For the common case of "create the worktree, allocate a free dev port,
maybe launch something in it", use the
[`gwt`](https://github.com/EdwardAstill/gwt) CLI (install:
`pipx install gwt` or `uv pip install -e ~/projects/gwt`):

```bash
# Create only — prints WORKTREE CONTEXT block with path/branch/port.
gwt <branch> [base]

# Create + launch Claude Code in a new terminal window.
gwt <branch> [base] --launch 'claude {path}'

# Or any other command template — {path} expands to the worktree dir.
gwt <branch> [base] --launch 'code {path}'
```

`gwt` places the worktree at `<parent>/<repo>-<branch>`, which is the
sibling-directory convention. If the user wants it under `.worktrees/`
or another location, drop to the manual steps below instead — `gwt`
doesn't take a destination override.

The `--launch` template accepts `{path}` as the worktree-path
placeholder; the spawn goes via `$TERMINAL -e <cmd>` when `$TERMINAL`
is set, otherwise the resolved command is just printed. Env-var
fallback: `GWT_LAUNCH_CMD`.

#### Manual path

**1. Detect project name**

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

**2. Create worktree**

```bash
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

**3. Run project setup**

Auto-detect and run appropriate setup:

```bash
if [ -f package.json ]; then bun install 2>/dev/null || npm install; fi
if [ -f Cargo.toml ]; then cargo build; fi
if [ -f pyproject.toml ]; then uv sync 2>/dev/null || pip install -e .; fi
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f go.mod ]; then go mod download; fi
```

**4. Verify clean baseline**

```bash
# Use project-appropriate command
npm test / bun test / cargo test / pytest / go test ./...
```

If tests fail: report failures and ask whether to proceed or investigate first.

**5. Report**

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

### Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check CLAUDE.md → ask user |
| Directory not ignored | Add to .gitignore + commit first |
| Tests fail at baseline | Report failures + ask to proceed |

### Setup: Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping ignore verification | Always `git check-ignore` before project-local worktree |
| Assuming directory location | Follow priority: existing > CLAUDE.md > ask |
| Proceeding with failing tests | Report failures, get explicit permission |
| Hardcoding setup commands | Auto-detect from project files |

### Setup: Red Flags

Never:
- Create a project-local worktree without verifying it's ignored
- Skip baseline test verification
- Proceed with failing tests without asking
- Assume directory location when ambiguous

---

## Phase 2: Finishing — Completing the Work

**Announce at start:** "Using git-worktree-workflow to complete this work."

### Step 1: Verify Tests

Before presenting options:

```bash
npm test / bun test / cargo test / pytest / go test ./...
```

If tests fail:

```
Tests failing (<N> failures). Must fix before completing:

[show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Don't continue to Step 2.

### Step 2: Determine Base Branch

```bash
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

Or ask: "This branch split from main — is that correct?"

### Step 3: Present Options

Present exactly these 4 options:

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

Don't add explanation — keep options concise.

### Step 4: Execute Choice

**Option 1 — Merge locally**

```bash
git checkout <base-branch>
git pull
git merge <feature-branch>
<run tests>
git branch -d <feature-branch>
```

Then cleanup worktree (Step 5).

**Option 2 — Push and create PR**

```bash
git push -u origin <feature-branch>

gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
EOF
)"
```

Then cleanup worktree (Step 5).

**Option 3 — Keep as-is**

Report: "Keeping branch `<name>`. Worktree preserved at `<path>`."

Do NOT cleanup worktree.

**Option 4 — Discard**

Confirm first:

```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

Wait for exact confirmation. If confirmed:

```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

Then cleanup worktree (Step 5).

### Step 5: Cleanup Worktree

For Options 1, 2, and 4:

```bash
git worktree list | grep $(git branch --show-current)
git worktree remove <worktree-path>
```

For Option 3: keep worktree.

### Finish: Quick Reference

| Option | Merge | Push | Keep Worktree | Delete Branch |
|--------|-------|------|---------------|---------------|
| 1. Merge locally | ✓ | — | — | ✓ |
| 2. Create PR | — | ✓ | ✓ | — |
| 3. Keep as-is | — | — | ✓ | — |
| 4. Discard | — | — | — | ✓ (force) |

### Finish: Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping test verification | Always verify tests before offering options |
| Open-ended "what next?" | Present exactly 4 structured options |
| Auto-cleanup for Option 2/3 | Only cleanup worktree for Options 1 and 4 |
| No confirmation for discard | Require typed "discard" before deleting |

### Finish: Red Flags

Never:
- Proceed with failing tests
- Merge without verifying tests on the merged result
- Delete work without typed confirmation
- Force-push without explicit request

---

## Integration

**Setup is called by:**
- `brainstorming` — when design is approved and implementation follows
- `subagent-driven-development` — before executing any tasks
- `executing-plans` — before executing any tasks

**Finish is called by:**
- `subagent-driven-development` — after all tasks complete
- `executing-plans` — after all batches complete
