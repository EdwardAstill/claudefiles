# af install

Install agentfiles skills, hooks, and CLI tools.

**Source:** `tools/python/src/af/install.py`

## Usage

```bash
af install                               # full global install (default)
af install --local                       # install to current project
af install --skill git-expert            # one skill globally
af install --category research           # one category globally
af install --local /path/to/project      # project install
af install --remove                      # uninstall globally
af install --dry-run                     # preview
af install --list-categories             # show categories
af install --from github:owner/repo      # install from GitHub
```

Global install includes all skills, hooks, and missing CLI tools from `manifest.toml`.
