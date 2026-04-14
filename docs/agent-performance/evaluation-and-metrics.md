# Evaluation and Metrics

You cannot optimize what you cannot measure. Improving agent performance requires moving beyond "vibes" and anecdotal testing toward rigorous, repeatable evaluation frameworks.

## 1. Deterministic Benchmarking
To test if a new skill, tool, or prompt actually improves performance, you need a baseline.
*   **Test Suites:** Create a repository of standard tasks (e.g., "Fix this specific bug in this repository," "Refactor this component to use hooks").
*   **Success Criteria:** The criteria must be binary and verifiable without human intervention.
    *   *Did the test suite pass?*
    *   *Does the file compile?*
    *   *Is the specific string present in the output?*

## 2. LLM-as-a-Judge
For tasks where success is subjective (e.g., "Write a clear architectural plan" or "Design a beautiful UI component"), use a stronger LLM (like Claude 3.5 Sonnet or GPT-4o) to evaluate the output against a strict rubric.
*   **Rubrics:** The judge model needs explicit grading criteria. (e.g., "Score 0-5. 5 means the code handles all edge cases, includes comments, and follows the existing project style guidelines. 1 means it hallucinates libraries.")
*   **Pairwise Comparison:** To test a new system prompt, run the old prompt and the new prompt on the same task, and ask the judge model which output is better and why.

## 3. Tracking Intermediate Metrics
Final success/failure is not the only metric that matters. Tracking intermediate steps helps identify bottlenecks.
*   **Token Efficiency:** How many tokens did the agent consume to solve the problem? (A solution that takes 10,000 tokens is better than one that takes 100,000 tokens, assuming both succeed).
*   **Tool Error Rate:** How often did the agent's tool calls fail due to malformed JSON or incorrect arguments? High error rates indicate poorly designed tool schemas.
*   **Trajectory Length:** How many turns did it take to reach the solution? Thrashing (many turns, little progress) indicates a lack of planning or poor context management.

## 4. The Evals Flywheel
*   **Log Failures:** Whenever the agent fails in a real-world scenario, extract that conversation.
*   **Create a Benchmark:** Turn that specific failure into a reproducible test case.
*   **Iterate:** Adjust the prompt, tools, or orchestration until the agent can pass the new benchmark consistently without regressing on old benchmarks.
*   **The `skill-tester` Pattern:** In advanced setups (like the Agentfiles framework), dedicated skills (`skill-tester`) are built explicitly to run these evaluations autonomously across different iterations of a skill.
