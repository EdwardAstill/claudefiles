# af search

Search indexed data sources via mks (BM25 full-text + vector search).

**Source:** `tools/python/src/af/search.py`

## Usage

```bash
af search --source notes calcium signalling     # search a specific source
af search complex analysis                      # search across all sources
af search --tree --source notes                 # show structural file tree
af search --list                                # list registered sources
af search --source notes --mode search topic    # BM25 only (fast)
af search --source notes --mode vsearch topic   # vector similarity
af search --source notes --snippets topic       # show text snippets
af search --source notes -n 20 topic            # max 20 results
```

## Arguments

| Argument | Description |
|----------|-------------|
| `query` | Search query — words or quoted phrase (optional) |

## Options

| Flag | Description |
|------|-------------|
| `--source <name>`, `-s` | Data source to search |
| `--mode <mode>`, `-m` | `query`/`search` (BM25) or `vsearch` (vector). Default: `query` |
| `--limit <n>`, `-n` | Max results (default: 10) |
| `--snippets` | Show text snippets in results |
| `--tree`, `-t` | Show structural file tree for a source |
| `--list`, `-l` | List registered sources |

## Search Modes

| Mode | Speed | Quality | Requires |
|------|-------|---------|----------|
| `query` / `search` | Fast | BM25 keyword match | Nothing |
| `vsearch` | Medium | Semantic similarity | [Ollama](https://ollama.ai) + `mks embed` + `nomic-embed-text` |

**Dependencies:** [mks](https://github.com/EdwardAstill/markstore) (`cargo install markstore`)
