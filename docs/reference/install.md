# Install Reference

## Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
```

## bootstrap.sh

New machine entry point. Does three things:

1. Clones repo to `~/.local/share/claudefiles-src/` (or pulls latest if it exists)
2. Installs `cf` Python CLI via `uv tool install --force -e tools/python/`
3. Runs `install.sh --global` for skills and bin tools

Re-running pulls the latest and re-installs — safe to use as an update mechanism.

## install.sh

**Single source of truth for all install logic.** Both `bootstrap.sh` and `cf install`
delegate to this script.

### Scopes

| Flag | Installs to |
|------|-------------|
| `--global` (or `--user`) | `~/.claude/skills/` |
| `--local [path]` (or `--project`) | `<project>/.claude/skills/` |

### Granularity

| Flag | What gets installed |
|------|---------------------|
| (none) | All 39 skills as individual symlinks + bin wrappers |
| `--category <name>` | One category directory |
| `--skill <name>` | One skill by its SKILL.md `name` field |

### Source

| Flag | Source |
|------|--------|
| (none) | Local repo (where install.sh lives) |
| `--from github:owner/repo` | Clones to `~/.claudefiles/`, installs from there |

### Other flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Preview without making changes |
| `--remove` | Remove installed symlinks |
| `--list-categories` | Show available categories |

### How It Works

1. Finds all leaf skills (SKILL.md files with no children)
2. Builds a flat `skills/` directory with symlinks to each leaf
3. Symlinks each skill individually into the target directory
4. On `--local`, adds `.claudefiles/` to project `.gitignore`

Individual skill symlinks enable `/skill-name` slash commands in Claude Code.

### Examples

```bash
./install.sh --global                                          # full install
./install.sh --global --from github:EdwardAstill/claudefiles   # from GitHub
./install.sh --global --category research                      # one category
./install.sh --global --skill git-expert                       # one skill
./install.sh --local /path/to/project                          # project install
./install.sh --global --remove                                 # uninstall
./install.sh --global --dry-run                                # preview
```

## cf install

Thin Python wrapper that delegates to `install.sh` with full argument passthrough.

```bash
cf install --global --dry-run    # identical to: bash install.sh --global --dry-run
```

## Design Principles

**Symlinks, not copies.** Changes to skill files are live on the next Claude Code
session — no re-install needed.

**One installer.** `install.sh` is the only place install logic lives. `cf install`
and `bootstrap.sh` both delegate to it, preventing behavioral drift.

**Individual skill symlinks.** Each skill gets its own symlink (not a single directory
symlink). This enables `/skill-name` slash commands in Claude Code.
