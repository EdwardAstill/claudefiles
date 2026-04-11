# Install Reference

## bootstrap.sh

The entry point for new machines. No local clone needed.

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
```

Installs the `agent-manager` skill and all bin tools globally, cloning the repo to `~/.local/share/claudefiles-src/`. Re-running pulls the latest and skips already-linked entries.

## install.sh

Full control over what gets installed and where.

### Scopes

| Flag | Installs to |
|------|-------------|
| `--global` | `~/.claude/skills/` + `~/.local/bin/` |
| `--local [path]` | `<project>/.claude/skills/` |

### Granularity

| Flag | What gets installed |
|------|---------------------|
| (none) | Full claudefiles |
| `--category <name>` | One category (`management`, `coding`, `research`) |
| `--skill <name>` | One skill by its SKILL.md `name` field |

### Source

| Flag | Source |
|------|--------|
| (none) | Local repo |
| `--from github:owner/repo` | Clones/updates to `~/.local/share/claudefiles-src/` |

### Other flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Preview without making changes |
| `--remove` | Remove installed symlinks |
| `--list-categories` | Show available categories |

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

## Agent Communication Bus

Each project gets a `.claudefiles/` folder when any `--write` tool runs. Gitignored — session state, not source.

```
.claudefiles/
├── context.md    ← cf-context output
├── versions.md   ← cf-versions output
├── routes.md     ← cf-routes output
├── repo-map.md   ← cf-status output
└── notes.md      ← cf-note target
```

## Structure

```
claudefiles/
├── claudefiles/           ← skills
├── bin/                 ← CLI tools → ~/.local/bin/
├── lib/                 ← shared scripts (no install needed)
├── manifest.toml        ← per-skill tool requirements + bin entries + CLI deps
├── install.sh           ← install/remove
└── bootstrap.sh         ← new machine entry point
```

## Design principles

**One file beats a wrapper.** If a script is useful standalone, put it in `bin/`. If it's internal to one skill, put it in `scripts/`. If it's shared across skills, put it in `lib/`.

**Symlinks, not copies.** Changes to skill files are live on the next Claude Code session — no re-install needed.
