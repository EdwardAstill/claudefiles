# Context and Memory Optimization

An agent's context window is its working memory. How effectively that memory is managed is often the biggest predictor of an agent's success on long-horizon tasks. When the context fills with noise, the agent suffers from "attention degradation," forgetting its original instructions or hallucinating tool calls.

## 1. Truncating Tool Outputs
Tools must never overwhelm the context window.
*   **The Problem:** Running `ls -laR` in a large project or `cat` on a minified JS file can consume 50,000+ tokens instantly, blowing out the context and causing the agent to lose its place.
*   **The Solution:** All read tools MUST implement pagination or hard truncation limits. For example, a `run_shell_command` tool should cap stdout/stderr at a reasonable threshold (e.g., 2,000 characters) and append a warning: `(Output truncated. Use grep or pagination to view more)`.

## 2. Targeted Retrieval vs. Mass Ingestion
Instead of giving the agent a generic "read file" tool, provide surgical tools.
*   **Fast Search:** A `grep_search` tool allows the agent to find specific functions without reading entire files.
*   **Scoped Reading:** If reading is necessary, tools should accept `start_line` and `end_line` arguments.
*   **AST Parsers:** For code, a tool that returns the Abstract Syntax Tree (signatures only) is often more token-efficient than returning raw text.

## 3. History Compaction and Handoffs
In multi-turn or multi-agent systems, passing the entire raw chat history is inefficient.
*   **Summarization Handoffs:** When Subagent A finishes a task and hands control back to the Router, it should only return a dense summary: *"I accomplished X. The current state is Y. Here is the ID of the resource created."*
*   **Periodic Compaction:** For long-running single agents, the system should periodically pause to summarize the journey so far, replacing older raw turns with a compressed "memory" block.

## 4. State Externalization
Agents should not use their context window as a database.
*   **The Workspace is the Truth:** Prefer writing intermediate plans, thoughts, or findings to physical files (e.g., `PLAN.md` or `.agent_scratchpad`) rather than relying on the LLM to remember them across 50 conversational turns. The agent can then cheaply reference or re-read these small files as needed.
