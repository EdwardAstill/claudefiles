# Example: Real-time Notification System

**The request:** "Add a real-time notification system to the app."

Illustrates: executor → manager escalation, design-advisor invocation, brainstorming
gate before parallel agent dispatch.

---

## 1. executor kicks off

Runs `cf context` + `cf status` to orient. Assesses: does this need parallel agents?

Yes — likely frontend (UI components, websocket client), backend (websocket server,
event emitter), and a database schema change. Three separate domains that could run
in parallel. Escalates to manager.

---

## 2. manager — planning phase

Reads `coding/REGION.md` and `planning/REGION.md`.

Asks the three planning questions:

**Git strategy?** New feature, parallel agents, risky changes. Obviously needs
worktrees. git-advisor skipped, answered inline.

**Coordination?** Frontend and backend are mostly independent but the API contract
between them is a dependency. The schema change must happen before both.
coordination-advisor skipped, answered inline: schema first, then frontend + backend
in parallel.

**Design/spec needed?** This is where manager pauses. "Real-time notification system"
could mean:
- WebSockets
- Server-Sent Events
- Polling
- A third-party service (Pusher, Ably)
- Push notifications (mobile)

The technology choice changes the entire architecture. The API contract between
frontend and backend agents can't be defined until this decision is made. If manager
dispatches agents now, they'll build against different assumptions.

**Manager loads `design-advisor`.**

---

## 3. design-advisor

Single question: does this need brainstorming or a spec, or can we proceed?

Its analysis:
- Multiple valid technology choices with real trade-offs (SSE vs WebSockets vs third-party)
- Frontend and backend agents need a shared contract before they can work independently
- Requirements are underspecified — "notifications" could mean in-app toasts, email,
  push, or all three

Verdict: **brainstorm first**. The technology decision and scope need to be resolved
before any implementation plan can be written. Without it, frontend and backend agents
will make conflicting assumptions.

---

## 4. manager adjusts the plan and confirms

Manager presents the revised plan:

> Before dispatching agents, we need to resolve the technology choice and define the
> API contract. I'll run brainstorming first to produce a spec, then dispatch three
> agents: schema migration, backend event system, and frontend components.
>
> Confirm?

---

## 5. execution

`brainstorming` runs → produces `docs/specs/2026-04-11-notifications-design.md`:
- SSE chosen (simpler than WebSockets, no third-party dependency)
- Event schema defined
- API contract specified
- Notification types scoped (in-app only, v1)

Three agents dispatched in parallel, all briefed against the spec:

| Agent | Scope |
|-------|-------|
| Agent 1 | Database schema migration |
| Agent 2 | Backend SSE endpoint + event emitter |
| Agent 3 | Frontend notification component + SSE client |

Manager synthesises outputs, runs tests, resolves any conflicts.

---

## Why design-advisor was loaded

Manager had the design question in its planning checklist but couldn't answer it
confidently. The technology ambiguity was real: proceeding without resolving it would
have caused parallel agents to build against incompatible assumptions. That's the
condition design-advisor exists for — not every task, only when the design decision
is genuinely non-obvious.

The two other advisors (git-advisor, coordination-advisor) were skipped because
those questions had obvious answers. Loading advisors when the answer is already
clear is overhead with no return.
