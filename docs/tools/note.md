# af note

Shared scratchpad for cross-agent communication.

**Source:** `tools/python/src/af/note.py`

## Usage

```bash
af note "message"              # append to .agentfiles/notes.md
af note --agent research "x"   # tag note by agent name
af note --read                 # read all notes
af note --clear                # clear notes file
```

## Arguments

| Argument | Description |
|----------|-------------|
| `message` | Text to append (optional) |

## Options

| Flag | Description |
|------|-------------|
| `--agent <name>` | Tag note by agent (default: "agent") |
| `--read` | Read all notes |
| `--clear` | Clear notes file |

## Details

Appends timestamped, agent-tagged notes to `.agentfiles/notes.md`. Useful for passing findings between parallel agents or recording observations during multi-step workflows.
