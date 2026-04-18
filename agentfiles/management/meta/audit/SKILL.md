---
name: audit
description: Use when verifying the agentfiles manifest is consistent — ensure every skill on disk is in manifest.toml, every manifest entry exists on disk, cli/mcp tools are properly wired, and registry symlinks point correctly so af install works.
---

# Audit (dispatcher)

This capability now runs as a **subagent** — see
`agentfiles/agents/audit.md`. It's a subagent because the tool list is
restricted to read-only (no accidental edits during a consistency check)
and the output is a structured pass/fail report.

## How to invoke

Dispatch via the Agent tool:

```
subagent_type: audit
prompt: |
  Run the full manifest consistency audit on the agentfiles repo at
  /home/eastill/projects/agentfiles. Report per-check results and fix hints.
```

Or run the CLI wrapper if it's available:

```bash
af audit
```

The subagent returns the full report inline — findings are short enough
that the parent can act on them directly.

## When to use this skill instead of the subagent directly

Almost never. This skill exists only so that a `/audit` invocation routes
to the subagent.
