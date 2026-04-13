# Similar Projects

Comparative analysis of public Claude Code skill/plugin suites and related projects.
Each document covers: what the project is, what it does well, its weaknesses, and concrete ideas agentfiles could implement.

| Project | Type | Stars | Key Differentiator |
|---------|------|-------|--------------------|
| [obra/superpowers](obra-superpowers.md) | Skills framework & methodology | ~147,000 | Enforced sequential dev methodology, cross-agent portability (6 AI coding agents) |
| [SuperClaude-Org/SuperClaude_Framework](superclaude-framework.md) | Meta-programming framework | ~22,000 | Behavioral modes, agent personas with model preferences, PyPI distribution |
| [disler/claude-code-hooks-mastery](disler-hooks-mastery.md) | Educational hooks deep-dive | ~5,800 | All 13 hook types, UV single-file scripts, security gate patterns |
| [wshobson/commands](wshobson-commands.md) | Slash command collection | ~2,300 | Clean two-tier workflow/tool split with namespace prefixes |
| [qdhenry/Claude-Command-Suite](qdhenry-claude-command-suite.md) | Mega collection | ~1,200 | 216+ commands, external integrations (Linear, Cloudflare) as named skills |
| [ChrisWiles/claude-code-showcase](chriswiles-claude-code-showcase.md) | Integration showcase | ~300 | Hooks × skills integration, `af check` as CI, scheduled maintenance Actions |
| [zircote/.claude](zircote-claude.md) | Personal dotfiles config | ~21 | `includes/` fragments per-language standards, 100+ deep domain agents |

---

## Cross-Cutting Themes

### What agentfiles has that comparable projects don't

- Actual installer (`install.sh`) with scoped installs and granular skill/category control
- A CLI tool (`af`) with context gathering, integrity checking, and agent inventory
- Explicit routing/executor layer — user never has to pick a skill manually
- `manifest.toml` tracking tool requirements and category per skill
- Category-level dispatchers and `REGION.md` for manager planning
- **Grouped `af agents` output** — skills displayed by category namespace, not a flat dump
- **Hooks layer** — `PreToolUse` safety gate blocking dangerous Bash commands; `PostToolUse` skill logger recording every SKILL.md invocation to `~/.claude/logs/agentfiles.jsonl`
- **`af log`** — skill usage history with per-skill filtering and frequency stats

### What comparable projects do that agentfiles currently doesn't

| Gap | Best Reference | Priority | Status |
|-----|----------------|----------|--------|
| **`SessionStart` hook** — auto-run `af context` + `af status` so executor skips manual orientation | hooks-mastery | High | open |
| **Behavioral modes** — operating posture switches (token-efficiency, deep-research) orthogonal to skill routing | SuperClaude | Medium | open |
| **`includes/` fragments** — per-language standards injected at invocation time, not embedded in skill prose | zircote | Medium | open |
| **`finishing-a-development-branch` skill** — done checklist (tests, REGION.md, PR drafted) executor calls at feature end | superpowers | Medium | open |
| **Agent model preferences** — `model = "opus"` per skill in manifest.toml | zircote, SuperClaude | Low | open |
| **`af check` as CI** — GitHub Actions workflow enforcing REGION.md integrity on every PR | showcase | Low | open |
| **Scheduled maintenance Actions** — weekly skill integrity checks, monthly doc freshness | showcase | Low | open |
