# af tools

List all available tools — internal af subcommands and external CLI dependencies.

**Source:** `tools/python/src/af/tools_cmd.py`

## Usage

```bash
af tools               # human-readable list
af tools --json        # machine-readable JSON output
```

## Options

| Flag | Description |
|------|-------------|
| `--json` | Machine-readable JSON output |

## Details

Reads `tools.json` and displays tool type (internal/external), description, and usage. External tools are marked as installed or missing.
