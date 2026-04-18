---
name: codebase-explainer
description: >
  Use when building a mental model of an unfamiliar repo. Trigger phrases:
  "how does this codebase work", "walk me through this project", "explain the
  architecture", "what does this service do", "trace how a request flows",
  "where does X live in the code", "onboard me to this repo", "I need to change
  Y, what does it touch", "map out the layers", "give me the tour". Reads the
  source to map architecture layers, trace execution paths end-to-end, and
  surface key abstractions + dependencies. Do NOT use for external library or
  framework docs (use docs-agent), for comparing approaches or tech choices
  (use research-agent), or for planning a concrete change (use writing-plans).
---

# Codebase Explainer

Systematic codebase analysis: maps architecture, traces execution paths, identifies
patterns, and documents dependencies to give you a working mental model fast.

## Step 1: Orient at the Top Level

```bash
af context   # project fingerprint: name, language, build system
af status    # recent commits — what's actively changing?
```

Then scan:

```bash
ls -la                    # top-level layout
cat README.md             # stated architecture
cat CLAUDE.md 2>/dev/null # engineering conventions
```

Key questions:
- What is the entry point? (main.py, index.ts, src/main.rs, etc.)
- What are the top-level directories and their responsibilities?
- What does the build system tell us about the project shape?

## Step 2: Map the Architecture Layers

Identify the layers and name each one. Common patterns:

| Pattern | Layers |
|---------|--------|
| Web app | Routes → Handlers → Services → Repository → Database |
| CLI tool | Command parser → Command handlers → Core logic → I/O |
| Library | Public API → Internal modules → Utilities |
| Event-driven | Producers → Queue → Consumers → Side effects |

For each layer: which directories/files implement it? What does it receive and what
does it return?

## Step 3: Trace a Key Execution Path

Pick the most important user action (a web request, a CLI command, a library call)
and trace it end-to-end:

1. Find the entry point (route handler, main function, exported API)
2. Follow the call chain — use `Grep` to find function definitions
3. Note where data is transformed, validated, or persisted
4. Identify all external calls (database, network, filesystem)

Document as a numbered sequence:
```
1. Request hits POST /api/tasks → TaskController.create()
2. Controller validates input → TaskSchema.parse()
3. Service creates record → TaskService.create()
4. Repository persists → db.insert(tasks, ...)
5. Returns created task
```

## Step 4: Identify Key Abstractions

Look for:
- Shared types/interfaces — what are the core data shapes?
- Dependency injection patterns — how are services wired together?
- Error handling conventions — how do errors propagate?
- Configuration — how is the system configured at startup?

```bash
# Find exported types/interfaces
grep -r "^export (type|interface|class)" src/ --include="*.ts" | head -20

# Find dependency wiring
grep -r "new " src/ --include="*.ts" -l   # constructors (DI candidates)
```

## Step 5: Produce the Mental Model

Write a brief summary covering:

1. **What it does** — one sentence
2. **Architecture** — layers and their responsibilities (the table from Step 2)
3. **Key execution path** — the traced sequence from Step 3
4. **Key abstractions** — 3-5 core types/interfaces with their roles
5. **Where to look** — which files/directories to touch for common change types

## When to Stop

You have enough when you can answer:
- "Where would I add X?" (naming the file and function)
- "What would break if I changed Y?" (naming the callers)
- "What does Z depend on?" (naming the dependencies)

Stop before you've read everything — goal is a working model, not complete knowledge.
