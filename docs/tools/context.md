# af context

Fingerprint the current project — language, runtime, package manager, framework, git state.

**Source:** `tools/python/src/af/context.py`

## Usage

```bash
af context             # print to stdout
af context --write     # also save to .agentfiles/context.md
```

## Options

| Flag | Description |
|------|-------------|
| `--write` | Save output to `.agentfiles/context.md` |

## Detection

Detects the following automatically by scanning project files:

**Languages/Runtimes:** Node.js, Bun, Rust, Go, Python, Ruby, Java/JVM, PHP

**Package managers:** bun, pnpm, yarn, npm, cargo, go mod, uv, poetry

**Frameworks:** Next.js, React, Vue, Svelte, Express, Fastify, Hono, Astro, Axum, Actix, Rocket, FastAPI, Django, Flask

**Git state:** current branch, dirty files, unpushed commits
