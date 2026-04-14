# Orchestration and Workflows

As agent systems grow, they rely on a diverse set of specialized skills. Orchestrating these skills—whether through multi-agent collaboration or complex single-agent state machines—is critical for performance and scalability.

## 1. Hierarchical Routing
A flat structure where an agent has access to 50 tools and skills often leads to confusion, tool-selection hallucinations, and context exhaustion.
*   **The Router/Manager Pattern:** Use a lightweight, fast model whose *only* job is to understand the user's intent, break it down, and select the appropriate specialist skill. The router does not execute the task itself.
*   **Specialist Agents:** Agents initialized with a highly specific system prompt (e.g., `infrastructure-expert`) and only the exact tools necessary for their domain.

## 2. Shared Workspaces vs. Message Passing
When one skill finishes and hands control back to the orchestrator or to another skill, how is context shared?
*   **The Anti-Pattern:** Passing massive, raw JSON blobs or the entire conversation history between agents. This degrades context and spikes token costs.
*   **The Best Practice (Stigmergy):** Skills should communicate through the environment. The file system, git repository, or a shared database is the ultimate source of truth. Agent A writes a spec to `spec.md`; Agent B reads `spec.md` to write the code.
*   **Handoff Summaries:** When an agent yields control, it should only provide a dense, high-level summary of what changed in the environment so the next agent knows where to look.

## 3. Declarative Workflows (State Machines)
Instead of letting an LLM dynamically decide every next step endlessly (which is prone to loops and derailment), enforce a structured workflow for known processes.
*   *Example DAG (Directed Acyclic Graph):* `Planning Phase` -> (Wait for User Approval) -> `Implementation Phase` -> `Verification Phase`.
*   If the `Verification Phase` fails, the state machine explicitly routes back to the `Implementation Phase` with the error context. This prevents a single, unconstrained agent from thrashing wildly between writing and testing.

## 4. Dynamic Tool and Skill Loading
To preserve the system prompt size and focus the agent's attention, do not inject the instructions for every possible skill at all times.
*   **Just-in-Time (JIT) Loading:** Use a "Skill Library" tool where the agent can search for available skills and dynamically load the instructions, or invoke a sub-agent only when that specific expertise is needed.

## 5. The Fallback Mechanism
Always provide a fallback mechanism if a router isn't sure which skill to use.
*   This is often an `executor` or `generalist` agent that can perform basic tasks or do further research in the codebase to determine if a specialized skill is actually required.
