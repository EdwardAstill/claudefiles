# Tool Engineering for Machines

Tools (or functions) are how agents interact with the world. However, tools designed for human developers (like CLI utilities or REST APIs) are often terrible for LLM agents. Agents need tools designed specifically for machine consumption.

## 1. Strict I/O Schemas
An LLM struggles to guess parameter names or formats.
*   **Strong Typing:** Define exact types (string, integer, boolean). Avoid generic `object` or `any` types.
*   **Enums:** If a parameter only accepts specific values (e.g., `"GET"`, `"POST"`), use an Enum in the schema. This dramatically reduces hallucinated arguments.
*   **Minimize Optionality:** Tools with 15 optional parameters confuse the model. Break complex tools down into simpler, atomic tools if necessary, or provide sensible defaults on the backend.

## 2. Actionable Error Reporting
When a tool fails, it is critical that the failure message teaches the agent how to fix the problem.
*   **Bad:** `Error 500: Internal Server Error` or `FileNotFoundError`.
*   **Good:** `Error: Directory 'src/components' not found. Did you mean to use an absolute path? Current working directory is '/app'.`
*   **Graceful Degradation:** If an agent attempts to edit a file that doesn't exist, the tool shouldn't just crash; it should return a message suggesting the creation of the file or prompting the agent to verify the path.

## 3. Idempotency and Side-Effect Management
Agents often retry identical tool calls if they get confused, if a network request hangs, or if the orchestrator restarts them.
*   **Idempotent Design:** A tool like `create_directory` should not throw a fatal error if the directory already exists; it should just return success.
*   **State Verification:** If an action is irreversible (like dropping a database table), the tool itself should require a confirmation flag, or the workflow should enforce a "Plan -> Wait for Approval -> Execute" cycle.

## 4. Prompting via Tool Descriptions
The `description` field in a tool schema is effectively a system prompt injection.
*   **Be explicit about *when* to use it:** "Use this tool to find all occurrences of a variable. Do NOT use this for replacing text."
*   **Provide examples:** "Example: `pattern: 'function init'`"
*   **Warn about limits:** "Note: This tool will truncate output over 100 results. Be specific in your query."

## 5. Granularity vs. Autonomy
Finding the right level of abstraction is key.
*   **Too atomic:** Forcing an agent to use `ls`, then `cd`, then `cat` wastes tokens and increases the chance of reasoning errors.
*   **Too abstract:** A "build_and_deploy_app" tool gives the agent no way to debug intermediate failures.
*   **The Sweet Spot:** Align tools with logical, composable developer actions: `search_codebase`, `read_file_section`, `replace_text`, `run_command`.
