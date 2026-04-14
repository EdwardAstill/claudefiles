# Andrej Karpathy's Agent Skills

*Reference: [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)*

This repository outlines key principles for improving agent performance by moving away from chaotic "vibe coding" toward structured, reliable execution. 

## Core Principles

1. **Think Before Coding**
   - **Practice:** Require agents to surface their assumptions, evaluate tradeoffs, and map out a plan before writing or modifying any code.
   - **Why it works:** Prevents silent confusion and hallucinated approaches. Thinking steps out constraints that ground the agent.

2. **Simplicity First**
   - **Practice:** Write the simplest possible code to achieve the goal. Avoid overengineering, unnecessary abstractions, and "just-in-case" generalizations.
   - **Why it works:** Complex abstractions confuse both humans and LLMs. Simpler code is easier for agents to reason about, test, and debug.

3. **Surgical Changes**
   - **Practice:** Make minimal, targeted edits strictly related to the current objective. Avoid unrelated "drive-by" refactoring.
   - **Why it works:** Minimizes regressions and side effects. Narrowly scoped changes keep the agent's context and attention focused.

4. **Goal-Driven Execution**
   - **Practice:** Transform imperative, step-by-step instructions into declarative goals with clear, verifiable success criteria.
   - **Why it works:** Allows agents to operate autonomously with a defined verification loop. The agent knows exactly when it has succeeded or failed based on objective checks (e.g., passing tests).
