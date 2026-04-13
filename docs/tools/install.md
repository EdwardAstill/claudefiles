# af install

Install agentfiles skills. Thin wrapper that delegates to `install.sh`.

**Source:** `tools/python/src/af/install.py`

## Usage

```bash
af install --global                      # full install
af install --global --skill git-expert   # one skill
af install --global --category research  # one category
af install --local /path/to/project      # project install
af install --global --remove             # uninstall
af install --global --dry-run            # preview
```

All arguments pass through verbatim to `install.sh` at the repo root.
