# Improving LLM Agent Performance: Research & Literature

Research into maximizing LLM agent capabilities has rapidly evolved from prompt engineering to sophisticated architectural frameworks. Below is a summary of key optimization strategies based on recent research (2024-2025).

## 1. Test-Time Scaling & Inference Optimization
Rather than retraining models, these approaches allocate more compute during inference ("thinking longer") to improve accuracy.

*   **Decocted Experience Improves Test-Time Inference in LLM Agents (2025):** Introduces "experience decoction" to distill long, noisy agent trajectories into concise lessons using hierarchical concept trees. This improves the retrieval of past knowledge at test time, significantly boosting performance.
*   **Disentangling Test-Time and Parameter Scaling (2025):** Demonstrates that for complex reasoning tasks, scaling test-time compute (e.g., extensive Chain-of-Thought) on smaller models is often more cost-effective and performant than using a larger, more expensive model with minimal thinking time.
*   **Agentic Reasoning Frameworks:** Utilizing specialized sub-agents (e.g., dedicated search or mapping agents) to assist a core reasoning model.

## 2. Planning & Sequential Decision Making
Addressing the myopic nature of standard autoregressive generation by forcing agents to plan, verify, and backtrack.

*   **Pre-Act: Multi-Step Planning (2025):** Proposes that agents should create a detailed, multi-step execution plan *before* taking any actions in the environment. This framework outperforms standard ReAct (Reasoning + Acting) by significantly reducing hallucinated or dead-end actions.
*   **Natural Plan (Google DeepMind, 2024):** Highlights that LLMs often fail at complex planning because they lack self-doubt. Introducing self-verification and explicit planning steps is crucial for success in long-horizon tasks.

## 3. Reward Models & Feedback Loops
Evaluating an agent's intermediate steps to guide its trajectory, rather than only evaluating the final output.

*   **AgentPRM (Process Reward Models, 2025):** Introduces process-level rewards that score intermediate steps based on "promise" (likelihood of success) and "progress" (distance covered). This allows agents to recognize dead ends early and backtrack, improving compute efficiency by 8x over standard reward models.
*   **Reflexion (2023/2024):** A seminal technique where agents "reflect" on their failures, generate verbal feedback about what went wrong, and use that feedback to improve in subsequent trials without human intervention.

## Summary of Techniques

| Technique | Primary Benefit |
| :--- | :--- |
| **Experience Decoction** | Reduces context noise and improves retrieval of past lessons. |
| **Pre-Planning** | Reduces hallucinated actions by enforcing a roadmap. |
| **Process Rewards (PRM)** | Enables early backtracking by scoring intermediate steps. |
| **Self-Reflection** | Allows iterative, autonomous improvement via verbal feedback. |
