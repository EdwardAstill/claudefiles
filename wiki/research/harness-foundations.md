# Harness Foundations

An **agent harness** is everything between the language model and the real world: the
tool loop, the context window manager, the permissions layer, the session state, the
skill/rule injection mechanism, and the dispatch logic for subagents. The model is the
engine; the harness is the chassis. Most "agent" capability gaps are harness bugs, not
model bugs.

This page inventories the primitives every production coding agent exposes, then
compares how eight widely-used harnesses implement them. It ends with the implications
for agentfiles — where our executor + manager design already aligns, and where the
literature suggests we should tighten.

> Cross-reference: `docs/reference/agent-orchestration-patterns.md` covers routing
> architectures and failure modes. `docs/reference/orchestration.md` documents the
> current agentfiles design. This page is the foundational literature they rest on.

---

## 1. Core primitives

Every serious harness implements the same seven primitives. The design choices inside
each primitive are where harnesses diverge.

| Primitive | What it does | Why it matters |
|-----------|-------------|----------------|
| **Tool loop** | The ReAct-style `think → act → observe → repeat` cycle. | The agent's entire capacity to act. A bad loop amplifies every other flaw. |
| **Context window** | The working buffer of text the model sees on each call. | The binding resource constraint — 200k–1M tokens, managed with compaction, RAG, and eviction. |
| **Session state** | What persists across turns and across sessions. | Without it, every turn is amnesia. With too much, tokens vanish into noise. |
| **Skill / rule injection** | How domain-specific instructions get in front of the model. | Replaces fine-tuning. The most powerful — and most fragile — primitive. |
| **Subagent dispatch** | Launching child agents with their own context windows. | Parallelism and context isolation. Also the source of the biggest failure class (see multi-agent page). |
| **Verification gates** | Explicit checks that outputs meet criteria before they ship. | The difference between "looks done" and "is done." The single largest quality lever. |
| **Permission governance** | What the harness allows or blocks per tool. | Trust boundary. Decides whether the agent can be left unattended. |

The ReAct loop itself was formalised by Yao et al. in 2022 ([arxiv 2210.03629](https://arxiv.org/abs/2210.03629)),
and every tool-using LLM since — including Claude Code — is a descendant. Toolformer
([arxiv 2302.04761](https://arxiv.org/abs/2302.04761)) demonstrated self-supervised
tool-use learning that informs how later systems teach models to decide *when* to
call a tool.

---

## 2. Comparative review of production harnesses

Ordered by release maturity as of April 2026. All data cross-checked against primary
vendor documentation and third-party architecture breakdowns.

| Harness | Tool loop | Context strategy | Skills / rules | Subagents | Verification |
|---------|-----------|------------------|----------------|-----------|--------------|
| **Claude Code** | Single main loop + subagent fan-out | Auto-compaction at ~95% fill; on-demand skill loading | `SKILL.md` + `CLAUDE.md` injected lazily | First-class (`Agent` tool) with fresh contexts | Hook-driven (`PostToolUse`, `Stop`) |
| **Aider** | Single loop, no subagents | Repo-map truncation; git commit per turn | `.aider.conf.yml`, repo conventions file | None | Built-in linters + test runners |
| **Cursor** | IDE-integrated loop | Active file + open-tab priority; Composer for multi-file | `.cursorrules` file | Background agents for long tasks | Manual review in-IDE |
| **Cline** | Plan → Act two-phase loop | MCP-exposed tools; compaction on demand | `.clinerules` directory | None (single loop) | User approves each action |
| **OpenHands** | CodeAct: write code, execute, observe | Explicit history compression | Microagents (trigger-based prompts) | Delegation via `AgentDelegateAction` | Sandbox + tests |
| **Devin** | Autonomous multi-day sessions | Proprietary episodic memory ("Devin's brain") | Knowledge base of learned facts | Internal planning agents | Self-verification + PR CI |
| **Gemini CLI** | ReAct loop with Gemini 2.5+ | 1M token window, minimal compaction needed | `GEMINI.md` files (like CLAUDE.md) | Tool-based dispatch | Custom commands for verify |
| **Codex CLI** | Lightweight loop, minimal config | Short sessions, frequent restarts | `AGENTS.md` | None in open-source edition | Via test runner tools |

**Sources:**
- [Claude Code Docs — How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)
- [Anthropic — Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Anthropic — Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Aider docs — repo-map](https://aider.chat/docs/repomap.html)
- [Cursor — Background Agents](https://docs.cursor.com/background-agent)
- [Cline — Plan/Act modes](https://docs.cline.bot/exploring-clines-tools/plan-and-act-modes)
- [OpenHands — CodeAct paradigm](https://docs.all-hands.dev/modules/usage/agents)
- [Cognition Labs — Introducing Devin](https://www.cognition.ai/blog/introducing-devin)
- [Gemini CLI docs](https://ai.google.dev/gemini-api/docs/cli)
- [OpenAI Codex CLI](https://github.com/openai/codex)
- [WaveSpeedAI — Claude Code Agent Harness: Architecture Breakdown](https://wavespeed.ai/blog/posts/claude-code-agent-harness-architecture/)
- [Sid Bharath — The Anatomy of Claude Code And How To Build Agent Harnesses](https://sidbharath.com/blog/the-anatomy-of-claude-code/)
- [Dive into Claude Code — arxiv 2604.14228](https://arxiv.org/html/2604.14228v1)

---

## 3. What makes a harness robust vs fragile

From the comparative review and the literature, the patterns cluster cleanly.

### Robust harness properties

1. **Demand-loaded skills.** Only skill *names and descriptions* are in the default
   context; full content loads when invoked. This is effectively tool-RAG applied to
   instructions and triples tool-selection accuracy at scale
   ([RAG-MCP, arxiv 2505.03275](https://arxiv.org/abs/2505.03275)).
2. **Deterministic compaction triggers.** Compaction fires on a measurable threshold
   (Claude Code: ~95% of context budget) rather than "when it feels full." Anthropic's
   Sept 2025 context-engineering post names compaction, structured notes, and
   sub-agent isolation as the three survival techniques for long sessions
   ([Anthropic, 2025](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)).
3. **Single main-loop + optional fan-out.** The agent loop stays flat; parallelism is
   an escape hatch, not the default. LangChain's 2025 usage data shows 73% of
   production systems are simple chains; only 12% use full multi-agent. DeepMind's
   scaling study found that forcing multi-agent onto sequential reasoning tasks can
   degrade accuracy by up to 70% ([arxiv 2512.08296](https://arxiv.org/abs/2512.08296)).
4. **Explicit verification gates in the harness, not the model.** Hooks
   (`PostToolUse`, `Stop`) or a deterministic test-runner step catch "looks correct"
   regressions the model would otherwise skip. SWE-agent's Agent-Computer Interface
   work showed that small harness changes — e.g. a syntax-checking file editor —
   produced outsized quality gains without touching the model
   ([arxiv 2405.15793](https://arxiv.org/abs/2405.15793)).
5. **Structured handoff between phases.** Devin-style multi-day agents and
   Anthropic's published orchestrator-worker pattern both use an explicit state
   document (plan, decisions, next steps) rather than trusting the conversation
   buffer.

### Fragile harness properties

1. **Flat "bag of agents" topology.** No hierarchy, no verification plane — reported
   to amplify errors up to 17x vs single-agent baselines
   ([Towards Data Science, 2025](https://towardsdatascience.com/why-your-multi-agent-system-is-failing-escaping-the-17x-error-trap-of-the-bag-of-agents/)).
2. **Static instruction injection.** Dumping a 20k-token rule file into every prompt
   burns tokens, increases latency, and correlates with worse instruction-following
   as irrelevant rules leak into attention.
3. **Implicit dependency ordering.** Multiple agents writing to shared state without
   dependency edges produces order-dependent bugs. Prompt2DAG
   ([arxiv 2509.13487](https://arxiv.org/abs/2509.13487)) shows explicit dependency
   graphs produce more reliable pipelines.
4. **No re-planning mechanism.** Static plan-then-execute is a named MAST failure
   mode ([Cemri et al., arxiv 2503.13657](https://arxiv.org/abs/2503.13657)): once
   execution reveals a flaw in the plan, the agent presses on regardless.

---

## 4. The Agent-Computer Interface thesis

A theme across the 2024-2025 literature is that harness quality matters more than
model quality for frontier coding performance. SWE-agent's authors coined the term
**Agent-Computer Interface (ACI)**: the set of tools and observability shapes the
agent's ability more than raw parameter count
([Yang et al., arxiv 2405.15793](https://arxiv.org/abs/2405.15793)). Concretely, a
file editor that validates syntax before accepting an edit outperforms a raw `write`
tool on SWE-bench, even with the same model underneath.

This reframes the agentfiles design question: skills and hooks *are* the harness
ACI. Improving them has a higher expected value than swapping models.

---

## Implications for agentfiles

- **Treat every skill description as ACI surface area.** Descriptions are what the
  router sees; sloppy descriptions cause mis-routes far more than model weakness.
  `af check` should evolve to score description distinctiveness, not just existence.
- **Make verification a first-class hook, not a habit.** `verification-before-completion`
  is currently a skill the executor chooses to load. Consider a `Stop`-hook that
  refuses session end unless a verification artefact (test output, command log) is
  present. The SWE-agent result argues this delta is larger than any model upgrade.
- **Keep the single-main-loop + fan-out topology.** The comparative table and the
  DeepMind/LangChain data validate the current executor-default-then-escalate design.
  Do not regress toward "bag of agents" even under pressure to parallelise.
- **Adopt a deterministic compaction/handoff trigger.** Executor's HANDOFF CONTEXT
  block is already a structured handoff, but there is no automated trigger. A hook
  measuring context fill and prompting for handoff when > 80% would close the gap
  Anthropic identifies as the #1 context failure.
- **Document the permission model alongside skills.** Claude Code's permission layer
  is under-used in agentfiles; `manifest.toml` lists tools but not permission
  policies. A future iteration should let each skill declare "I need Bash with these
  allowlist entries" so `af install` can configure `settings.json` deterministically.
