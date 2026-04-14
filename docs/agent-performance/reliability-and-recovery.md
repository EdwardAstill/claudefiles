# Reliability and Recovery

An agent's performance is not just measured by what it does when things go right, but how it recovers when things go wrong. Building resilient systems requires moving from "fire-and-forget" execution to verified, self-correcting loops.

## 1. Test-Time Compute (Verification)
The most powerful way to increase an agent's reliability is to force it to verify its own work.
*   **Mandatory QA Steps:** Before an agent declares a task complete, it must prove it. If it wrote a function, it must run the unit tests. If it built a UI, it should (ideally) use a headless browser to verify the element renders.
*   **Empirical Evidence over Assumptions:** Agents are prone to "sycophancy" (saying "Yes, I fixed it!") without actually checking. System prompts must strictly forbid declaring victory without empirical evidence (e.g., a passing exit code from a test runner).

## 2. Self-Correction Loops
When a failure occurs (a test fails, a command returns an error), the agent must have the autonomy to attempt a fix.
*   **Error Injection:** The orchestrator must feed the exact error output back into the agent's context.
*   **Hypothesize before Fixing:** Force the agent to write a brief hypothesis about *why* the failure occurred before it is allowed to modify code again. This prevents blind "guess and check" thrashing.
*   **Max Retries:** Implement strict loop breakers. If an agent fails to fix a failing test after 3 attempts, it must stop and escalate to the user, summarizing what it tried.

## 3. Handling Hallucinations
Even the best models hallucinate tool calls, file paths, or API endpoints.
*   **Safe Defaults:** If an agent tries to read a non-existent file, the tool must return a helpful error, not crash the session.
*   **Grounding:** Force agents to use search tools (`grep`, `find`) to locate files before they are allowed to edit them, rather than guessing paths based on framework conventions.

## 4. Environment Sandboxing and Safety
Recovery is impossible if the agent destroys the environment.
*   **Git as a Safety Net:** Encourage workflows where the agent operates on an isolated git branch or worktree. If the agent gets irrecoverably confused, the orchestrator can simply `git reset --hard` or delete the worktree.
*   **Read-Only Modes:** For research or planning phases, enforce a read-only environment where tools like `write_file` or destructive shell commands are physically disabled.

## 5. The "Backtrack" Pattern
Advanced agents realize when they are in a dead end.
*   Provide mechanisms (or prompt instructions) that allow the agent to explicitly state: "This approach is fundamentally flawed. I am abandoning this plan and reverting to the previous state to try an alternative architecture."
