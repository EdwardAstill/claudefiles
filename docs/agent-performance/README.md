# Agent Performance: The Pillars

This directory contains comprehensive documentation on maximizing the performance, reliability, and autonomy of Large Language Model (LLM) agents. Agent performance isn't just about prompt engineering; it's about system architecture, efficient tool design, and robust error recovery.

## The Pillars of Performance

This documentation is structured around the core domains required to optimize an agentic system:

1.  **[Context and Memory](context-and-memory.md)**: Optimizing token usage, managing conversation history, truncating tool outputs, and preventing context degradation.
2.  **[Tool Engineering](tool-engineering.md)**: Designing tools for machines rather than humans. Covers idempotency, strict I/O schemas, and ensuring actionable error messages instead of silent failures.
3.  **[Skill Design Patterns](skill-design-patterns.md)**: Frameworks for creating robust, constrained skills (e.g., forcing Chain-of-Thought, single-responsibility principle, explicit negative constraints).
4.  **[Orchestration and Workflows](orchestration-and-workflows.md)**: Routing between skills, multi-agent delegation, shared workspaces vs. message passing, and declarative state machines.
5.  **[Reliability and Recovery](reliability-and-recovery.md)**: Building self-correction loops, mandatory verification steps (test-time compute), and handling hallucinations or environment failures.
6.  **[Evaluation and Metrics](evaluation-and-metrics.md)**: How to measure agent performance rigorously using deterministic benchmarking, LLM-as-a-judge, and defining clear success criteria.

## Resources & Literature

The `resources/` directory contains summaries of community best practices and academic research:
-   [Andrej Karpathy's Agent Skills](resources/karpathy-skills.md)
-   [Claude Code Best Practices](resources/claude-code-best-practices.md)
-   [Research Papers](resources/research-papers.md)
