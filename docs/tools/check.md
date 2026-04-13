# af check

Verify all leaf skills have entries in their category's REGION.md.

**Source:** `tools/python/src/af/check.py`

## Usage

```bash
af check               # run verification
af check --verbose     # detailed output
```

## Options

| Flag | Description |
|------|-------------|
| `--verbose` | Show detailed output |

## Details

Scans `skills/` and `agentfiles/` directories and validates that each REGION.md contains a matching `### <skill-name>` header for every leaf skill present.
