# af index

Build a structural file tree for a directory and register it as a searchable data source.

**Source:** `tools/python/src/af/index.py`

## Usage

```bash
af index /path/to/dir                  # index, named after directory
af index /path/to/dir --name notes     # explicit name
af index --list                        # show registered sources
af index --no-mks /path/to/dir         # tree only, skip mks ingestion
af index --files /path/to/dir          # show all files (default: dirs + leaf files)
af index --depth 3 /path/to/dir        # limit tree depth
af index --remove notes                # unregister a source
```

## Arguments

| Argument | Description |
|----------|-------------|
| `path` | Directory to index (default: cwd) |

## Options

| Flag | Description |
|------|-------------|
| `--name <name>`, `-n` | Custom source name |
| `--depth <d>`, `-d` | Max tree depth (0 = unlimited) |
| `--files`, `-f` | Show all files (default: dirs + leaf files) |
| `--no-mks` | Skip mks collection registration |
| `--list`, `-l` | Show registered sources |
| `--remove <name>` | Unregister a source |

## Details

Stores tree in `~/.claude/data/<name>/tree.md` and ingests markdown files via [mks](https://github.com/EdwardAstill/markstore) for full-text search. Registry at `~/.claude/data/registry.json`.

**Dependencies:** [mks](https://github.com/EdwardAstill/markstore) (`cargo install markstore`)
