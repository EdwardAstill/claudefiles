---
name: audit
description: Use when verifying the agentfiles manifest is consistent — ensure every skill on disk is in manifest.toml, every manifest entry exists on disk, cli/mcp tools are properly wired, and registry symlinks point correctly so af install works.
---

# Audit

Verifies `manifest.toml` matches actual project state: every skill registered, every CLI/MCP tool documented, registry symlinks valid.

## Checks

| # | Check | Pass condition |
|---|-------|---------------|
| 1 | Skill dirs → manifest | Every `agentfiles/**/SKILL.md` skill has a `[skills.<name>]` entry |
| 2 | Manifest → skill dirs | Every `[skills.*]` entry has a corresponding `SKILL.md` on disk |
| 3 | Skill `cli` → `[cli.*]` | Every name in a skill's `cli = [...]` has a `[cli.<name>]` entry |
| 4 | `[cli.*]` → skill reference | Every `[cli.*]` entry is referenced by at least one skill's `cli = [...]` |
| 5 | Skill `mcp` → docs | Every name in a skill's `mcp = [...]` appears in `docs/tools/` or `.claude/settings.json` |
| 6 | `[cli.*]` in PATH | Every registered CLI tool exists on PATH (flag missing with install hint) |
| 7 | `skills/` registry symlinks | Every `skills/<name>` is a symlink into `agentfiles/<category>/<name>` (flag real dirs as uninstalled) and every `agentfiles/**/SKILL.md` skill has a matching `skills/<name>` symlink so `af install` can find it |

## How to Run

```bash
# Full audit
af audit

# Or invoke this skill and Claude runs the checks manually using Bash + Read
```

If `af audit` is not yet implemented, run checks manually — see steps below.

## Manual Procedure

**Step 1 — collect skill names from disk:**
```bash
find agentfiles -name SKILL.md | grep -v '/SKILL.md$' | sed 's|.*/||' | sort
# (or use the directory names one level above each SKILL.md)
```

Actually, skill name = the directory containing SKILL.md (leaf dir):
```bash
find ~/projects/agentfiles/agentfiles -name SKILL.md \
  | xargs -I{} dirname {} | xargs -I{} basename {} | sort
```

**Step 2 — collect skill names from manifest:**
```bash
grep '^\[skills\.' manifest.toml | sed 's/\[skills\.\(.*\)\]/\1/' | sort
```

**Step 3 — diff:**
```bash
comm -23 <(find ... | sort) <(grep ... manifest.toml | sort)
# left-only  = on disk, missing from manifest  → add [skills.<name>] entry
# right-only = in manifest, missing from disk  → add SKILL.md or remove entry
```

**Step 4 — check cli cross-refs:**
```bash
# cli tools declared by skills
grep 'cli = \[' manifest.toml | grep -oP '"[^"]+"' | tr -d '"' | sort -u

# cli tools registered in [cli.*]
grep '^\[cli\.' manifest.toml | sed 's/\[cli\.\(.*\)\]/\1/' | sort -u
```

**Step 5 — check PATH:**
```bash
while IFS= read -r tool; do
  command -v "$tool" >/dev/null 2>&1 && echo "✓ $tool" || echo "✗ $tool (not in PATH)"
done < <(grep '^\[cli\.' manifest.toml | sed 's/\[cli\.\(.*\)\]/\1/')
```

**Step 6b — check registry symlinks (`skills/` is what `af install` reads):**
```bash
# Flag any skills/<name> that is a real directory rather than a symlink — means
# the skill was authored under skills/ but never moved into agentfiles/<cat>/
for d in ~/projects/agentfiles/skills/*/; do
  name=$(basename "$d")
  [ -L "${d%/}" ] || echo "✗ skills/$name — not a symlink (move into agentfiles/<cat>/$name and re-link)"
done

# Flag agentfiles skills with no skills/<name> symlink — invisible to af install
comm -23 \
  <(find ~/projects/agentfiles/agentfiles -name SKILL.md -exec dirname {} \; | xargs -n1 basename | sort) \
  <(ls ~/projects/agentfiles/skills | sort)
# left-only = needs `ln -s ../agentfiles/<cat>/<name> skills/<name>`
```

**Step 7 — check MCP docs:**
```bash
grep 'mcp = \[' manifest.toml | grep -oP '"[^"]+"' | tr -d '"' | sort -u
# for each: check docs/tools/ files and ~/.claude/settings.json mcpServers keys
```

## Output Format

Group by check, show pass/fail summary, then list each failure with a fix hint:

```
CHECK 1: Skill dirs → manifest
  ✓ 42 skills match
  ✗ browser-control — add [skills.browser-control] to manifest.toml

CHECK 3: Skill cli → [cli.*]
  ✗ skill 'browser-control' declares cli = ["foxpilot"] but [cli.foxpilot] missing
    → add [cli.foxpilot] entry with manager/package/install/description

CHECK 6: CLI tools in PATH
  ✗ foxpilot — not found
    → uv tool install /home/eastill/projects/foxpilot

SUMMARY: 5/6 checks passed, 3 issues found
```

## Common Fixes

| Issue | Fix |
|-------|-----|
| Skill dir missing from manifest | Add `[skills.<name>]\ntools = []\ncategory = "<cat>"` |
| Manifest entry, no SKILL.md | Create `agentfiles/<cat>/<name>/SKILL.md` or remove entry |
| cli declared, no `[cli.*]` | Add `[cli.<name>]` block with manager/package/install/description |
| `[cli.*]` orphan | Add `cli = ["<name>"]` to relevant skill, or remove the `[cli.*]` block |
| MCP undocumented | Add row to `docs/tools/external-tools.md` |
| Tool not in PATH | Run the install command from the `[cli.*]` entry |
| `skills/<name>` is real dir (not symlink) | `mkdir -p agentfiles/<cat>/<name> && mv skills/<name>/SKILL.md agentfiles/<cat>/<name>/ && rmdir skills/<name> && ln -s ../agentfiles/<cat>/<name> skills/<name>` |
| `agentfiles/<cat>/<name>` has no `skills/<name>` symlink | `ln -s ../agentfiles/<cat>/<name> skills/<name>` so `af install` can discover it |
