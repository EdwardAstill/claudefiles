# Skill Design Patterns

A "Skill" is a specialized persona or bounded procedure that an agent adopts to accomplish a specific type of task (e.g., "UI Expert", "Database Architect", "Code Reviewer"). Moving from open-ended prompts to structured skills is essential for reliable performance.

## 1. The Single Responsibility Principle
Just like functions in software engineering, a skill should do one thing exceptionally well.
*   **Avoid "God Skills":** Do not create a single skill that tries to be a full-stack developer, security auditor, and deployment engineer simultaneously.
*   **Focused Scope:** If a skill is "Code Reviewer," its instructions should focus strictly on reviewing code, identifying bugs, and outputting structured feedback. It should *not* have the tools to actually implement the fixes (that should be handed off to an implementation skill).

## 2. Explicit Negative Constraints
Agents often fail because they try to be overly helpful, leading to hallucinations or out-of-scope actions. Explicitly telling an agent what *not* to do is as important as telling it what to do.
*   *Example:* "Do NOT attempt to write or modify code. Your only output should be a markdown summary."
*   *Example:* "Never assume a library is installed. Always check the `package.json` first."
*   *Example:* "Do NOT hallucinate file paths. If you cannot find the file using `search`, inform the user."

## 3. Structured Output Formats
Define exactly what the skill must produce to ensure downstream processes or other agents can parse the result.
*   **Tags:** Force the agent to wrap its final answer in XML tags (e.g., `<result>`, `<plan>`).
*   **JSON:** If the output needs to be programmatically consumed, enforce a strict JSON schema.

## 4. Forced Chain-of-Thought (CoT)
Encourage the agent to "think" before it acts, especially for complex skills.
*   **Practice:** Include a mandatory directive: "Before executing any commands or writing code, you MUST wrap your strategy, assumptions, and plan in `<thought>` tags."
*   **Benefit:** This surfaces the agent's logic, making debugging easier and significantly reducing the likelihood of impulsive, incorrect tool usage. It allows the model to "talk itself" into the correct action.

## 5. The "Plan -> Act -> Validate" Cycle
A robust skill should never follow a fire-and-forget execution model. It must include instructions on how to verify its own success.
*   **Practice:** "After making a code change, you MUST run the associated test suite. If the tests fail, you must attempt to fix the error."
*   **Benefit:** This creates a self-correcting loop, shifting the burden of QA from the user back to the agent.
