# af routes

Scan codebase for API route definitions.

**Source:** `tools/python/src/af/routes.py`

## Usage

```bash
af routes              # print to stdout
af routes --write      # also save to .agentfiles/routes.md
```

## Options

| Flag | Description |
|------|-------------|
| `--write` | Save output to `.agentfiles/routes.md` |

## Supported Frameworks

| Framework | Language |
|-----------|----------|
| Express | Node.js |
| Fastify | Node.js |
| Hono | Node.js |
| Next.js (file-based) | Node.js |
| Axum | Rust |
| Actix-web | Rust |
| FastAPI | Python |
| net/http, chi, gin | Go |

Extracts HTTP methods and paths. For Next.js, also scans `pages/api/` and `app/api/` directories for file-based routes.
