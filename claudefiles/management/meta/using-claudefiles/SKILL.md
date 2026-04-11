---
name: using-claudefiles
description: >
  Use when starting any conversation — establishes how skills work, the default
  routing rule (executor for new tasks), and when to invoke specialist skills.
  Follow-up messages within ongoing work do not re-invoke executor.
---

# Using Claudefiles

## The Rule

**Every new task starts with executor.** Executor orients, makes the routing
decision inline, and handles the work — escalating to manager if parallel
multi-agent coordination turns out to be needed.

Invoke with the `Skill` tool:
- `Skill("executor")` — default for every new task
- `Skill("brainstorming")` — before any feature or design work (executor will
  remind you, but invoking it directly skips the reminder)
- `Skill("systematic-debugging")` — before investigating any bug

## New task vs follow-up

Invoke executor on **new tasks**. Continue inline on **follow-ups**.

**New task (invoke executor):**
- Session opens with a first request
- User starts a genuinely new independent problem
- "Now I want to...", "Can you also build...", "Next, let's..."

**Follow-up (continue inline):**
- "yes", "ok", "go ahead", "do it"
- Answering a question you asked ("use PostgreSQL", "make it blue")
- Refining current work ("actually change X to Y", "also add Z")
- Feedback on something just done ("that's wrong, try X")

**The test:** Continuing work in flight → continue inline.
New independent problem → executor.

## How routing works

Executor makes the routing decision in its first step — no separate routing skill needed:

| Outcome | When |
|---------|------|
| Executor proceeds | Everything a single agent can handle (the common case) |
| Executor escalates to manager | Genuinely parallel multi-agent work or overwhelming scale |

## Skill priority

1. **executor** — every new task
2. **brainstorming** — before any feature, component, or design work
3. **systematic-debugging** — before any bug fix or unexpected behaviour
4. **Specialist skills** — loaded inline by executor as needed

## Red Flags — Stop, You're Rationalizing

| Thought | Reality |
|---------|---------|
| "This is too simple for executor" | Executor calibrates to size — no overhead for simple tasks. |
| "Let me just answer quickly without invoking executor" | Executor's orient step takes seconds and catches wrong-turn assumptions. |
| "I already know what to do, I'll skip executor" | Executor's orient step is where you confirm that. Skip it and you're guessing. |
| "This is a follow-up, not a new task" | Correct — then don't invoke executor. Continue inline. |
| "This is complex so it needs manager" | Complexity is not the signal. Parallelism is. |

## Skills are independent

Each skill works standalone. Executor and manager add coordination on top — they
don't replace direct skill invocation when you know exactly what you need.
