# af read

Dump `.agentfiles/` bus state.

**Source:** `tools/python/src/af/read.py`

## Usage

```bash
af read                # all bus files
af read context        # single file (context.md)
af read notes          # notes.md
af read repo-map       # repo-map.md
af read versions       # versions.md
af read routes         # routes.md
```

## Arguments

| Argument | Description |
|----------|-------------|
| `target` | Specific bus file to read: `context`, `versions`, `routes`, `repo-map`, `notes` (optional — omit for all) |
