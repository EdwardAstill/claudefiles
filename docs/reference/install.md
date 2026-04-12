# Install Reference

## Two Ways to Use claudefiles

### Mode A — Install everything globally

All skills available in every Claude Code session, on every project. No per-project setup.

```bash
# New machine (clone + full install in one step):
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash

# Existing clone:
./install.sh --global
```

What this installs:
- All 39 skills → `~/.claude/skills/`
- `cf` CLI → available on PATH via uv
- Hook scripts → `~/.claude/skills/hooks/`
- Hooks wired into `~/.claude/settings.json` (safety gate + skill logger)

---

### Mode B — skill-manager only globally, everything else per-project

Install one skill globally. Then in each project, say "set up this project" and
skill-manager asks what the project does, selects relevant skills, and installs them
locally to `.claude/skills/`. Projects get only what they actually need.

```bash
# New machine:
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash -- --skill skill-manager

# Existing clone:
./install.sh --global --skill skill-manager
```

Then inside any project:

```
you: set up this project
```

skill-manager fingerprints the project, asks one question, proposes a skill set,
and installs on confirmation. See [skill-manager](../../claudefiles/management/meta/skill-manager/SKILL.md)
for the full workflow.

What this installs globally:
- `skill-manager` → `~/.claude/skills/`
- `cf` CLI → available on PATH via uv
- Hook scripts → `~/.claude/skills/hooks/`
- Hooks wired into `~/.claude/settings.json`

---

## Which mode should I use?

| | Mode A (global all) | Mode B (skill-manager only) |
|---|---|---|
| Setup effort | One command, done | One command + per-project `/setup` |
| Skills available | Everywhere, always | Only what each project needs |
| Project isolation | None | Each project has its own skill set |
| Best for | Personal machines, solo dev | Teams, or if you care about keeping things lean |

For a personal machine, **Mode A is simpler**. Mode B makes more sense if you want
to keep track of which skills are actually relevant per project.

---

## Updating

Re-run the same command. `install.sh` is idempotent — symlinks that exist are skipped,
new ones are added, the cf CLI is reinstalled with `--force`.

```bash
# If installed from GitHub via bootstrap:
bash ~/.local/share/claudefiles-src/bootstrap.sh

# If working from a local clone:
git pull && ./install.sh --global
```

---

## install.sh reference

**Single source of truth for all install logic.** `bootstrap.sh` and `cf install`
both delegate to this script.

### Scope flags

| Flag | Installs to |
|------|-------------|
| `--global` (or `--user`) | `~/.claude/skills/` + hooks + cf CLI |
| `--local [path]` (or `--project`) | `<project>/.claude/skills/` |

### Granularity flags

| Flag | What gets installed |
|------|---------------------|
| (none) | All skills as individual symlinks |
| `--category <name>` | One category (management, coding, planning, research) |
| `--skill <name>` | One skill by its SKILL.md `name` field |

### Source flags

| Flag | Source |
|------|--------|
| (none) | Local repo (where install.sh lives) |
| `--from github:owner/repo` | Clones to `~/.local/share/claudefiles-src/`, installs from there |

### Other flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Preview without making changes |
| `--remove` | Remove installed symlinks |
| `--list-categories` | Show available categories |

### Examples

```bash
./install.sh --global                          # full global install
./install.sh --global --skill skill-manager    # Mode B: skill-manager only
./install.sh --global --category research      # one category globally
./install.sh --local /path/to/project          # project-level install
./install.sh --global --remove                 # uninstall
./install.sh --global --dry-run                # preview
```

---

## bootstrap.sh

Thin shim for new-machine setup from GitHub. Clones (or pulls) the repo to
`~/.local/share/claudefiles-src/`, then hands off to `install.sh --global`.

```bash
# Full install:
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash

# skill-manager only (Mode B):
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash -s -- --skill skill-manager
```

---

## Design notes

**Symlinks, not copies.** Changes to skill files are live on the next Claude Code
session — no re-install needed after editing a SKILL.md.

**One installer.** All install logic lives in `install.sh`. `cf install` and
`bootstrap.sh` both delegate to it.

**Individual skill symlinks.** Each skill gets its own symlink rather than one
directory symlink. This is what enables `/skill-name` slash commands in Claude Code.
