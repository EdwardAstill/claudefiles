# External Tools

Third-party CLI tools and services that agentfiles depends on.

## Language Servers (LSPs)

| Tool | Language | Install | Docs |
|------|----------|---------|------|
| `pyright` | Python | `bun install -g pyright` | [GitHub](https://github.com/microsoft/pyright) |
| `typescript-language-server` | TypeScript | `bun install -g typescript-language-server` | [GitHub](https://github.com/typescript-language-server/typescript-language-server) |
| `rust-analyzer` | Rust | `rustup component add rust-analyzer` | [Website](https://rust-analyzer.github.io/) |
| `tinymist` | Typst | `cargo install tinymist` | [GitHub](https://github.com/Myriad-Dreamin/tinymist) |

## Data and Search

| Tool | Purpose | Install | Docs |
|------|---------|---------|------|
| `mks` | Markdown indexing and search | `cargo install markstore` | [GitHub](https://github.com/EdwardAstill/markstore) |
| `Ollama` | Local LLM for vector embeddings | [Download](https://ollama.ai) | [Website](https://ollama.ai) |
| `jq` | JSON processing | `bun install -g jq` | [Website](https://jqlang.github.io/jq/) |
| `rg` | ripgrep — fast recursive search | `cargo install ripgrep` | [GitHub](https://github.com/BurntSushi/ripgrep) |
| `sd` | search & displace — regex refactoring | `cargo install sd` | [GitHub](https://github.com/chmln/sd) |

## Browser and UI

| Tool | Purpose | Install | Docs |
|------|---------|---------|------|
| `Chromium` / `Chrome` | Browser backend for `af browser` | `apt install chromium-browser` | [Project](https://www.chromium.org/) |
| `Firefox` | Browser backend for `af screenshot` | `apt install firefox` | [Mozilla](https://www.mozilla.org/en-US/firefox/) |
| `Puppeteer` | Auto-installs browsers for `af browser` | `npm install -g puppeteer` | [Website](https://pptr.dev/) |
| `Playwright` | Backend for `af screenshot` | `npm install -g playwright` | [Website](https://playwright.dev/) |
| `Tailwind CSS` | Utility-first CSS framework | — | [Website](https://tailwindcss.com/) |
| `shadcn/ui` | Accessible component library | `npx shadcn@latest init` | [Website](https://ui.shadcn.com/) |

## Developer Utilities

| Tool | Purpose | Install | Docs |
|------|---------|---------|------|
| `uv` | Python package manager | [Install](https://docs.astral.sh/uv/getting-started/installation/) | [Website](https://astral.sh/uv) |
| `bun` | JS runtime and package manager | [Install](https://bun.sh) | [Website](https://bun.sh) |
| `cargo` | Rust package manager | [Install](https://rustup.rs) | [Website](https://doc.rust-lang.org/cargo/) |
