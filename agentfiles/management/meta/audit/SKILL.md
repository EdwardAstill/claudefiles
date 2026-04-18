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

## Checks

| # | Check | Pass condition |
|---|---|---|
| 1 | Skill dirs → manifest | Every `agentfiles/**/SKILL.md` has a `[skills.<name>]` entry |
| 2 | Manifest → skill dirs | Every `[skills.*]` has a matching `SKILL.md` on disk |
| 3 | Agent files → manifest | Every `agentfiles/agents/<name>.md` has a `[agents.<name>]` entry |
| 4 | Manifest → agent files | Every `[agents.*]` has a matching `.md` on disk |
| 5 | Skill `cli` → `[cli.*]` | Every CLI name a skill declares is defined under `[cli.<name>]` |
| 6 | `[cli.*]` → skill reference | Every `[cli.*]` is referenced by at least one skill |
| 7 | `[cli.*]` in PATH | Every registered CLI tool is on PATH |
| 8 | `skills/` registry | Every `skills/<name>` resolves and every on-disk skill has a symlink |
| 9 | Hook script health | Every `hooks/*.py` uv-script block declares only resolvable deps; every shell hook's referenced binaries are on PATH; every `hooks.json` command resolves to an executable file |

Check 9 catches the silent-failure case where a hook imports a missing
package — previously the failure only surfaced when the hook ran, and
nobody noticed it stopped doing its job.

## When to use this skill instead of the subagent directly

Almost never. This skill exists only so that a `/audit` invocation routes
to the subagent.
