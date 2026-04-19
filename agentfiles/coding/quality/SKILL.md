---
name: coding-quality
description: >
  Sub-category dispatcher for code quality workflows. Use when the user is
  about to start, finish, debug, review, or clean up an implementation and
  the right sub-skill isn't yet chosen. Trigger phrases: "start a new
  feature the right way", "something's broken, what do I do", "before I
  mark this done", "ready to request review", "got review feedback", "this
  code is tangled, clean it up", "how do I test this properly", "document
  this module". Routes to tdd, systematic-debugging,
  verification-before-completion, code-review, simplify, or documentation.
  Do NOT use as a leaf skill — always dispatch downward. Do NOT use for
  security audits (use security-review) or performance tuning (use
  performance-profiling).
---

# Coding Quality

Routes to the right code quality skill based on the situation.

## Skills

| Skill | Use when |
|-------|----------|
| `tdd` | Before writing any implementation code |
| `systematic-debugging` | Bug, test failure, or unexpected behaviour |
| `verification-before-completion` | Before claiming work is done or creating a PR |
| `requesting-code-review` | After implementation, before merging |
| `receiving-code-review` | When acting on review feedback |
| `simplify` | After implementation — clean up and refine |
| `documentation` | Writing or updating READMEs, API docs, guides, changelogs |
