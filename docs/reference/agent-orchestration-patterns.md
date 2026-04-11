# Agent Orchestration Patterns (2024-2026)

Research synthesis on LLM agent routing, scaling, and failure modes.

---

## 1. Routing Architectures

### Two-Level Router (Executor + Manager)

The dominant production pattern: a single orchestrator handles 80%+ of work inline,
escalating to multi-agent coordination only when genuine parallelism is needed.

**Evidence:**
- Anthropic's "Building Effective Agents" guide explicitly recommends starting with a
  single agent, adding multi-agent only when simpler solutions fall short.
- LangChain 2025 usage data: 73% of production systems use simple chains, only 12%
  use full agents.
- Google DeepMind scaling study (Dec 2025, arxiv 2512.08296): adding agents can
  **degrade performance by up to 70%** for sequential reasoning tasks because
  communication disrupts chain-of-thought.

### Common Production Patterns

| Pattern | Description | When |
|---------|-------------|------|
| **Router** | Classifies input, dispatches to specialist | ~40% latency reduction vs sequential |
| **Orchestrator-Workers** | Central LLM decomposes, delegates, synthesizes | Complex parallel work |
| **Supervisor** | Single supervisor manages routing + decisions | Most common for personal tools |
| **Evaluator-Optimizer** | One agent generates, another evaluates in loop | Quality-critical outputs |

### Anti-Pattern: Over-Routing

Multi-agent systems consume approximately **15x more tokens** than single-agent
interactions. The escalation gate matters more than the routing logic.

**Sources:**
- [Anthropic: Building Effective AI Agents](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic Architecture Patterns PDF](https://resources.anthropic.com/hubfs/Building%20Effective%20AI%20Agents-%20Architecture%20Patterns%20and%20Implementation%20Frameworks.pdf)
- [AI Agent Orchestration Patterns (2026)](https://thinking.inc/en/blue-ocean/agentic/agent-orchestration-patterns/)
- [Multi Agent Architecture: Patterns & Production Reality](https://www.truefoundry.com/blog/multi-agent-architecture)

---

## 2. Tool Scaling and Selection

### Tool Count Degradation

Tool-selection accuracy degrades as pool size increases. Measured across 1 to 11,100
tools:

- Context window overload reduces distinguishability between similar tools
- Hallucinations increase with tool count
- **Cursor enforces a hard limit of 40 MCP tools**
- OpenAI caps at 128 but performance degrades much sooner

### Tool RAG

Retrieving relevant tools per query (rather than loading all) **triples tool invocation
accuracy** while cutting prompt tokens by 50%. This is the recommended pattern for
systems with 20+ tools.

**Implication:** Demand-loading skills via the Skill tool (showing only names/descriptions
until invoked) is effectively tool-RAG.

### Skill Granularity

The key metric is not count but **distinguishability**. Skills that are too similar cause
routing confusion. 30-40 skills is a reasonable range if descriptions are maximally
distinct.

Academic definition (arxiv 2602.12430): skills are bundles of instructions, workflow
guidance, scripts, reference docs, and metadata — loaded dynamically when relevant.

**Sources:**
- [How many tools can an AI Agent have?](https://achan2013.medium.com/how-many-tools-functions-can-an-ai-agent-has-21e0a82b7847)
- [RAG-MCP: Mitigating Prompt Bloat in LLM Tool Selection](https://arxiv.org/pdf/2505.03275)
- [MCP and the "too many tools" problem](https://demiliani.com/2025/09/04/model-context-protocol-and-the-too-many-tools-problem/)
- [Agent Skills for LLMs](https://arxiv.org/html/2602.12430v3)
- [SoK: Agentic Skills](https://arxiv.org/html/2602.20867v1)

---

## 3. Multi-Agent Failure Modes

### MAST Taxonomy (Cemri et al., March 2025)

Analyzed 1,600+ traces across 7 MAS frameworks. **14 failure modes in 3 categories:**

1. **System design issues** — poor agent topology, missing error handling, inadequate
   tool design
2. **Inter-agent misalignment** — agents working at cross purposes, contradictory
   outputs, coordination failures. **Single most common failure category.**
3. **Task verification** — no mechanism to verify outputs before returning them

### "Bag of Agents" Anti-Pattern

- Flat topology with no hierarchy = **17x error amplification** vs single-agent baselines
- Agents descend into circular logic or hallucination loops
- Open-loop execution with no verification plane

### Context Loss

**The #1 identified failure mode.** When agents hand off work, critical context degrades.
Anthropic's analysis of 200+ enterprise agent deployments found **57% of project failures
originated in orchestration design.**

### DeepMind Scaling Study Key Findings

- If a single agent already solves a task at ~45% accuracy, adding agents gives
  diminishing or negative returns
- The "coordination tax" (tokens and time spent communicating) reduces capacity for
  actual reasoning
- Multi-agent helps ONLY for genuinely parallelizable tasks

**Sources:**
- [Why Do Multi-Agent LLM Systems Fail? (MAST)](https://arxiv.org/abs/2503.13657)
- [The Multi-Agent Trap (TDS)](https://towardsdatascience.com/the-multi-agent-trap/)
- [17x Error Trap of the "Bag of Agents"](https://towardsdatascience.com/why-your-multi-agent-system-is-failing-escaping-the-17x-error-trap-of-the-bag-of-agents/)
- [Towards a Science of Scaling Agent Systems (DeepMind)](https://arxiv.org/abs/2512.08296)
- [Google Research: Scaling Agent Systems](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)

---

## 4. Specialization Evidence

### When Specialization Helps

1. **Provides information the base model lacks** — e.g., Typst-specific patterns,
   LSP integration, project-specific conventions
2. **Enforces methodology** — e.g., TDD forcing test-first, structured debugging.
   The model CAN do these but won't reliably without the skill's structure.
3. **Encodes project-specific context** — e.g., "use uv not pip, run ruff not black"

### When Specialization Adds Less Value

1. **When the skill is mostly "be good at [language]"** — Claude is already highly
   capable at Python/TypeScript/Rust. Value comes from the convention/tooling delta.
2. **When skills overlap significantly** — redundant capabilities increase coordination
   cost without improving output.

### Evidence

- Anthropic's Agent S2: generalist-specialist framework achieved 18.9% and 32.7%
  relative improvements via Mixture-of-Grounding
- anthropics/skills repo: 62,000+ GitHub stars within 4 months — massive adoption
  of skill-as-context-modifier pattern
- Claude docs: skills "transform general-purpose agents into specialists"

**Sources:**
- [Claude Agent Skills Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Agent Skills - Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Extend Claude with skills](https://code.claude.com/docs/en/skills)

---

## 5. Planning Phase Design

### Inline Planning vs Formal DAGs

- Formal DAGs add value for parallelizable work (independent nodes execute in parallel)
  but add overhead for sequential work
- Inline planning is appropriate for 80%+ of tasks
- The planner-executor split (capable model plans, cheaper models execute) is a proven
  cost optimization

### Adaptive Replanning

Plans should be living documents that adapt as execution reveals new information.
Static-plan-then-execute is identified as a limitation in the MAST research.

Key questions:
- If a dispatched agent fails, is there a replan mechanism?
- If execution reveals a design flaw, can the plan be updated?
- What's the protocol when review loops exceed iteration limits?

### Dependency Resolution

Explicit dependency graphs (even simple ones) produce more reliable results than
implicit ordering. Template-guided task decomposition outperforms monolithic generation.

**Sources:**
- [LLM Agent Task Decomposition Strategies](https://apxml.com/courses/agentic-llm-memory-architectures/chapter-4-complex-planning-tool-integration/task-decomposition-strategies)
- [Prompt2DAG: Modular LLM Pipeline Generation](https://arxiv.org/html/2509.13487v1)
- [Systematic Decomposition of Complex LLM Tasks](https://arxiv.org/html/2510.07772v1)

---

## 6. Common Capability Gaps in Developer Agent Systems

Based on survey of production systems and developer needs research:

| Capability | Priority | Notes |
|-----------|----------|-------|
| Security review / SAST | High | 30% of tech pros report low trust in AI code |
| Database / SQL expertise | High | Only 7.5% of orgs at full DB DevOps maturity |
| Performance profiling | Medium | "Correct but slow" has no standard skill |
| Infrastructure / IaC | Medium | Dockerfiles, K8s, Terraform |
| Refactoring patterns | Medium | Distinct from simplification |
| Dependency management | Low | Version bumps, CVE tracking, migration guides |
| Observability | Low | Structured logging, tracing, metrics |
| Accessibility | Low | Web/UI a11y compliance |

**Sources:**
- [State of Database DevOps 2025](https://www.liquibase.com/blog/state-of-database-devops-report-as-of-1h-2025)
- [Must-Have Skills for Claude in 2026](https://medium.com/@unicodeveloper/10-must-have-skills-for-claude-and-any-coding-agent-in-2026-b5451b013051)
- [Top 12 AI Developer Tools 2026](https://checkmarx.com/learn/ai-security/top-12-ai-developer-tools-in-2026-for-security-coding-and-quality/)
