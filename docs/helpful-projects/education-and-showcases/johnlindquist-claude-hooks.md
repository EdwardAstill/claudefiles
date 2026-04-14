# johnlindquist/claude-hooks

**URL:** https://github.com/johnlindquist/claude-hooks
**Type:** Programmatic Hooks Framework (TypeScript)

## What It Is

A TypeScript-based framework for building programmatic Claude Code hooks. It moves away from simple shell/python scripts and provides a typed, structured way to interact with Claude's lifecycle events (`PreToolUse`, `PostToolUse`, etc.).

---

## What It Does Well

- **Type Safety** — Provides full auto-completion and type-checking for hook payloads, making hook development much faster and less error-prone.
- **Rich Context** — Makes it easier to parse and manipulate the complex JSON payloads that Claude passes to hooks.
- **Developer Experience** — Optimized for developers who are already comfortable in the TypeScript/Node ecosystem.
- **Reusability** — Allows for the creation of shared "Hook Libraries" that can be imported and composed across different projects.

---

## Weaknesses

- **Language Locked** — Requires a Node/Bun runtime, which might not be available in every environment.
- **Build Step** — Unlike simple shell scripts, these hooks may require a transpilation step (unless using `ts-node` or `bun`).
- **Complexity** — Can be "over-engineering" for simple tasks like blocking a specific command.

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Typed Hook Payloads** | Create a TypeScript library in `hooks/` that provides types for the `PreToolUse` and `PostToolUse` events to simplify our own hook logic. |
| **Hook Marketplace** | Allow `af add` to also install specific "Hook Middlewares" (e.g., "The Security Gate," "The Skill Logger"). |
| **Programmatic Validation** | Use typed hooks to perform more complex validations (like checking ASTs before allowing a code change) that are difficult in shell scripts. |
