# Workflows Reference

End-to-end traces of what happens at each stage — user input, scripts that run, files read, files written.

---

## 1. Bootstrap — New Machine

**User action:**
```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
```

**Script:** `bootstrap.sh`

| Step | What happens | Files written |
|------|-------------|---------------|
| Clone | `git clone https://github.com/EdwardAstill/claudefiles ~/.claudefiles/` | `~/.claudefiles/**` |
| Link skill | `ln -s ~/.claudefiles/dev-suite/management/agent-manager ~/.claude/skills/agent-manager` | `~/.claude/skills/agent-manager` → symlink |
| Link bin tools | `ln -s ~/.claudefiles/bin/cf-* ~/.local/bin/` | `~/.local/bin/cf-agents`, `cf-status`, `cf-context`, `cf-versions`, `cf-routes`, `cf-note`, `cf-init`, `cf-read`, `cf-setup`, `cf-worktree` |

**Result:** One skill globally active (`agent-manager`). All bin tools on PATH. Everything else lives in `~/.claudefiles/` waiting to be installed per-project.

---

## 2. Project Setup — /setup

**User action:** Opens a project in Claude Code, says "set up this project" or `/setup`

**Skill invoked:** `agent-manager` (reads `~/.claudefiles/dev-suite/management/agent-manager/SKILL.md`)

| Step | What happens | Scripts/files |
|------|-------------|---------------|
| Fingerprint | `cf-context --write` runs | Reads: project files, `package.json`, `Cargo.toml`, `go.mod`, etc. Writes: `.claudefiles/context.md` |
| Question | Claude asks: "Describe your project in a few sentences" | — |
| Skill selection | Claude maps description to skills using the selection table in agent-manager SKILL.md | Reads: `~/.claudefiles/dev-suite/*/SKILL.md` frontmatter (in-context) |
| Present | Claude shows what will be installed and why, what will be skipped and why | — |
| Confirm | User says yes / adjusts | — |
| Install skills | `~/.claudefiles/install.sh --local --skill <name>` for each selected skill | Writes: `.claude/skills/<skill-name>` → symlink to `~/.claudefiles/dev-suite/.../` |
| Check deps | `cf-setup --write` | Reads: `~/.claudefiles/manifest.toml`, scans `.claude/skills/` for installed skill names. Checks PATH for each declared CLI tool. Writes: `.claudefiles/deps.md` |
| Gitignore | `.claudefiles/` added if missing | Writes: `.gitignore` |

**Files written:**
```
<project>/
├── .claude/skills/
│   ├── simple-orchestrator  → symlink
│   ├── git-expert           → symlink
│   └── ...
├── .claudefiles/
│   ├── context.md           ← project fingerprint
│   └── deps.md              ← tool dependency report
└── .gitignore               ← .claudefiles/ added
```

---

## 3. Daily Use — Task Routing

**User action:** Asks Claude to do anything — "add auth to this API", "what's on this branch", etc.

**Skill invoked:** `simple-orchestrator` (if installed in this project)

| Step | What happens |
|------|-------------|
| Assessment | simple-orchestrator reads its own body (loaded on invocation), assesses task on three axes: scope, research needed, agent coordination needed |
| Low complexity | Routes directly to the right specialist skill |
| High complexity | Passes to `complex-orchestrator` with a context summary |

**Complex orchestrator path:**

| Step | What happens | Files read |
|------|-------------|------------|
| Read context | `cf-context --write`, `cf-status --write`, `cf-note --read` | `.claudefiles/context.md`, `.claudefiles/repo-map.md`, `.claudefiles/notes.md` |
| Read registry | Open `~/.claudefiles/dev-suite/registry.md` | Registry: skill inputs, outputs, chain targets |
| Plan | Decide which skills to invoke, in what order, parallel or sequential | — |
| Present plan | Show user the execution plan, wait for approval | — |
| Execute | Dispatch skills/agents, collect outputs, hand results between skills | — |

---

## 4. Git Workflow — git-expert

**User action:** "Create a worktree for the auth feature" or any git operation

**Skill invoked:** `git-expert`

| Step | What happens | Scripts/files |
|------|-------------|---------------|
| Situation assessment | `cf-status --write` | Reads: git state. Writes: `.claudefiles/repo-map.md` |
| Display | Claude presents Situation Summary: branch, status, worktrees, upstream | — |
| Recommend | Claude offers 2–3 next paths with exact commands and explanations | — |
| Worktree creation (if requested) | `lib/port-finder.sh` finds free port | Reads: nothing. Returns: port number |
| Create worktree | `git worktree add ../worktree-<branch> -b <branch> <base>` | Writes: `../worktree-<branch>/` directory |
| Emit context | Claude outputs WORKTREE CONTEXT block | Other skills read this to know where to work |
| Open terminal (optional) | `cf-worktree <branch>` | Launches new terminal window at worktree path with Claude Code |

**WORKTREE CONTEXT block (published by git-expert, consumed by other skills):**
```
WORKTREE CONTEXT
  Path:    /path/to/worktree-feature-auth
  Branch:  feature/auth
  Port:    3001
  Status:  ready
```

---

## 5. Research Workflow — docs-agent / research-agent

**User action:** "How do I use Hono's streaming API?" or "Should I use Prisma or Drizzle?"

**Skill invoked:** `docs-agent` (how do I) or `research-agent` (should I)

### docs-agent

| Step | What happens | Tools used |
|------|-------------|------------|
| Identify library + version | `cf-versions` (if needed) | Reads: `package.json`, lockfiles. Writes: `.claudefiles/versions.md` |
| Fetch docs | context7 MCP → resolve library ID → fetch current docs | External: context7 MCP server |
| Supplement | WebSearch / WebFetch for examples or changelogs | External: web |
| Output | Exact API signature, working example, source URL, version note | — |
| Record (optional) | `cf-note --agent docs "finding"` | Writes: `.claudefiles/notes.md` |

### research-agent

| Step | What happens | Tools used |
|------|-------------|------------|
| Search | WebSearch across multiple sources | External: web |
| Fetch | WebFetch on top results | External: web |
| Synthesise | Build structured report: consensus, nuances, pitfalls, contradictions | — |
| Output | Report with confidence levels, recommended direction, further investigation pointers | — |
| Record | `cf-note --agent research "finding"` | Writes: `.claudefiles/notes.md` |

---

## 6. Agent Communication Bus

`.claudefiles/` is the shared state layer. Any agent can write to it; any agent can read from it.

| File | Written by | Read by | Purpose |
|------|-----------|---------|---------|
| `context.md` | `cf-context --write` | complex-orchestrator, any skill | Project fingerprint — language, stack, framework, git state |
| `repo-map.md` | `cf-status --write` | git-expert, complex-orchestrator | Git topology — branches, worktrees, ahead/behind |
| `versions.md` | `cf-versions --write` | docs-agent | Dependency versions for doc lookups |
| `routes.md` | `cf-routes --write` | api-architect | API surface map |
| `notes.md` | `cf-note` | Any skill via `cf-note --read` | Free-form findings, decisions, context from any agent |
| `deps.md` | `cf-setup --write` | agent-manager | Tool dependency status for installed skills |

**Reading all bus state at once:**
```bash
cf-read              # dump all files
cf-read notes        # single file
```

**Initialising from scratch:**
```bash
cf-init              # creates .claudefiles/, populates all files, adds to .gitignore
```

`.claudefiles/` is gitignored — it's session state, not source.

---

## 7. Updating claudefiles

**User action:** "Update claudefiles" or re-run bootstrap

```bash
bootstrap.sh   # re-running pulls latest from GitHub (git pull --ff-only)
```

Because skills are symlinks, the updated files are live immediately in the next Claude Code session — no reinstall needed.

To update what skills are installed in a project:
```bash
~/.claudefiles/install.sh --local --skill <new-skill>
~/.claudefiles/install.sh --local --remove --skill <old-skill>
```
