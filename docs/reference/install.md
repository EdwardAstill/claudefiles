# Install Reference

## Two-Step Install

### Step 1 — Bootstrap (`install.sh`)

The bootstrap is minimal. It installs two things:
1. The `af` CLI (via `uv tool install`)
2. The `agentfiles-manager` skill globally (symlinked into `~/.claude/skills/` and `~/.gemini/skills/`)

```bash
# New machine (clone + bootstrap in one step):
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/agentfiles/main/bootstrap.sh | bash

# Existing clone:
./install.sh
```

### Step 2 — Install skills (`af install`)

After bootstrap, use `af install` for everything else.

```bash
# Install all skills + CLI tools globally:
af install

# Install skills into the current project:
af install --local
```

---

## Two Modes

### Mode A — Install everything globally

All skills available in every Claude Code session, on every project.

```bash
./install.sh && af install
```

What `af install` adds:
- All skills → `~/.claude/skills/` and `~/.gemini/skills/`
- Hook scripts wired into settings
- All missing CLI tools from `manifest.toml`

### Mode B — agentfiles-manager only, everything else per-project

Bootstrap installs `agentfiles-manager` globally. Then in each project, say
"set up this project" and the manager selects and installs the relevant skills
locally to `.claude/skills/`. Projects get only what they actually need.

```bash
./install.sh
# That's it — agentfiles-manager is already installed globally.
# Then inside any project:
#   you: set up this project
```

---

## Which mode should I use?

| | Mode A (global all) | Mode B (manager only) |
|---|---|---|
| Setup effort | Two commands, done | Bootstrap + per-project `/setup` |
| Skills available | Everywhere, always | Only what each project needs |
| Project isolation | None | Each project has its own skill set |
| Best for | Personal machines, solo dev | Teams, or keeping things lean |

For a personal machine, **Mode A is simpler**. Mode B makes more sense if you want
to keep track of which skills are actually relevant per project.

---

## Updating

Re-run the same commands. Both `install.sh` and `af install` are idempotent —
existing symlinks are replaced, new ones are added.

```bash
# If installed from GitHub via bootstrap:
bash ~/.local/share/agentfiles-src/bootstrap.sh

# If working from a local clone:
git pull && ./install.sh && af install
```

---

## `af install` reference

The main installer. Handles skills, hooks, and CLI tools.

### Scope flags

| Flag | Installs to |
|------|-------------|
| `--global` (default) | `~/.claude/skills/` + `~/.gemini/skills/` + hooks + CLI tools |
| `--local [path]` (or `--project`) | `<project>/.claude/skills/` + `<project>/.gemini/skills/` |

### Granularity flags

| Flag | What gets installed |
|------|---------------------|
| (none) | All skills |
| `--category <name>` | One category (management, coding, planning, research) |
| `--skill <name>` | One skill by its SKILL.md `name` field |

### Source flags

| Flag | Source |
|------|--------|
| (none) | Auto-detected repo root |
| `--from github:owner/repo` | Clones to `~/.local/share/agentfiles-src/`, installs from there |

### Other flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Preview without making changes |
| `--remove` | Remove installed symlinks |
| `--list-categories` | Show available categories |

### Examples

```bash
af install                                  # full global install (default)
af install --local                          # install all skills to current project
af install --local --skill python-expert    # one skill to current project
af install --local --category research      # one category to current project
af install --global --remove                # uninstall globally
af install --dry-run                        # preview
af install --list-categories                # show categories
```

---

## `install.sh` reference

Minimal bootstrap script. Only installs `af` CLI + `agentfiles-manager` skill.

```bash
./install.sh              # bootstrap
./install.sh --dry-run    # preview
./install.sh --remove     # remove bootstrap
```

---

## `bootstrap.sh`

Thin shim for new-machine setup from GitHub. Clones (or pulls) the repo to
`~/.local/share/agentfiles-src/`, then runs `install.sh`.

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/agentfiles/main/bootstrap.sh | bash
```

---

## Design notes

**Symlinks, not copies.** Changes to skill files are live on the next session —
no re-install needed after editing a SKILL.md.

**Two-step install.** `install.sh` is a minimal shell bootstrap (no Python needed
beyond uv). `af install` is the full installer written in Python with proper
argument parsing, manifest reading, and CLI tool installation.

**Individual skill symlinks.** Each skill gets its own symlink. This enables
`/skill-name` slash commands in Claude Code.
