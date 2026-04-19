# Tools

Documentation for every `af` subcommand and the external tools they depend on.

## Internal Tools (af CLI)

### Context & Project State

- [context](context.md) — Project fingerprint (languages, frameworks, git state)
- [status](status.md) — Branch/worktree topology map
- [versions](versions.md) — Dependency version inventory
- [routes](routes.md) — API route definitions
- [note](note.md) — Shared scratchpad for cross-agent communication
- [read](read.md) — Dump `.agentfiles/` bus state
- [init](init.md) — Bootstrap `.agentfiles/` directory

### Skill & Tool Management

- [agents](agents.md) — Skill/MCP server inventory
- [log](log.md) — Skill invocation log, session traces, and review
- [test-skill](test-skill.md) — Scaffold skill test workspace for benchmarking
- [check](check.md) — Verify REGION.md sync with skills
- [setup](setup.md) — Check skill dependencies
- [tools](tools.md) — List available tools

### Secrets

- [secrets](secrets.md) — Manage API keys and tokens

### Data Sources & Search

- [index](index.md) — Index directories for search
- [search](search.md) — Full-text and semantic search via mks

### UI Preview & Browser

- [preview](preview.md) — Serve HTML mockups with auto-refresh
- [screenshot](screenshot.md) — Capture browser screenshots
- [browser](browser.md) — Browser automation via CDP

### File System

- [tree](tree.md) — Show folder structure as tree

### Installation

- [install](install.md) — Install agentfiles skills

## External Tools

- [external-tools](external-tools.md) — Third-party CLI tools and services used by agentfiles
