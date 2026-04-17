# Lessons Learned

Short, in-the-field observations from running agentfiles. This directory is the
**episodic layer** of the system's memory (see
[`../research/memory-and-learning.md`](../research/memory-and-learning.md)):
concrete things that happened, what was learned from them, and what changed (or
should change) as a result.

Research pages in `../research/` are the semantic layer — what we believe is true
about agent harnesses in general. Lessons-learned are the episodic layer — what
we've actually seen happen in this system.

---

## When to write a lesson

- A skill loaded three times in one session and burned context without adding value.
- The manager was invoked when executor would have sufficed (or vice versa).
- A workaround was needed more than once for a recurring pattern.
- A verification step caught a bug that would have shipped.
- A router decision was wrong and required manual correction.
- A paper from `../papers/` turned out to apply directly (or not apply) to our case.

If it happened once and was idiosyncratic, capture it in `.agentfiles/notes.md`
instead. If it happened twice or more, promote it here.

---

## File format

One lesson per file. Filename: `YYYY-MM-DD-short-slug.md` (date first so grep-by-month
works). Template:

```markdown
# Short descriptive title

**Date:** YYYY-MM-DD
**Session:** (optional — branch name, project, or task reference)
**Severity:** low | medium | high (medium = worth a skill edit; high = worth a design change)

## Context

One paragraph. What task, what skill, what prompted the observation.

## What happened

Concrete facts. Tool calls, error messages, actual file paths. Not speculation.

## Lesson

One or two sentences. The generalisable claim, not just the specific incident.

## Action taken / proposed

- [ ] Concrete next step. Skill edit, hook change, doc update, research page bullet.
- [ ] Owner: (human / retrospective skill / executor)

## Related

- Link to relevant `../research/*.md` page.
- Link to `../papers/` if a paper frames the pattern.
- Link to previous lesson if this is a recurrence.
```

---

## Promotion pipeline

Lessons feed the self-improvement loop described in
[`../research/self-improving-agents.md`](../research/self-improving-agents.md):

```
session log → observation → lesson (this dir) → skill edit / hook / doc change
```

When a lesson recurs (two lessons with overlapping content), promote to a
`SKILL.md` rule or an `AGENTS.md` entry. Record the promotion in the original
lesson's "Action taken" section and add a cross-link.

**Who promotes:** the `retrospective` skill, run periodically. Human review on
the draft before any skill file is edited. Never allow autonomous skill
modification (see `self-improving-agents.md` — drift is the main risk with
unbounded self-editing).

---

## Not yet populated

No lessons yet — this directory was scaffolded as part of the initial wiki build.
First lessons should come from the first `af log review` → `retrospective`
cycle after the wiki ships.

The `retrospective` skill should check this directory and its conventions before
writing its first lesson, and can refine the template above based on practical
experience.
