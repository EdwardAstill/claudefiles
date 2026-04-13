---
name: code-review
description: >
  Use when requesting a code review of completed work, or when receiving and processing
  code review feedback. Two modes: requesting (dispatch a reviewer subagent with focused
  context) and receiving (evaluate feedback technically before implementing — verify,
  push back if wrong, no performative agreement).
---

# Code Review

Two distinct workflows depending on where you are in the process.

---

## Requesting a review

Dispatch a review agent with precisely crafted context — never your session's history.
The reviewer stays focused on the work product, not your thought process.

### When to request

**Mandatory:** After completing a major feature; before merging to main; after each task
in subagent-driven-development.

**Optional:** When stuck (fresh perspective); after fixing a complex bug.

### How to request

1. Get the commit range:
   ```bash
   git rev-parse HEAD~1   # or origin/main for the base
   git rev-parse HEAD
   ```

2. Dispatch a reviewer subagent (Agent tool) with:
   - What was implemented and what it should do
   - The commit range to review (`BASE_SHA..HEAD_SHA`)
   - Any specific areas of concern
   - Clear output format: Critical / Important / Minor issues

3. Act on feedback:
   - **Critical** — fix immediately before proceeding
   - **Important** — fix before merging
   - **Minor** — note for later or fix now
   - **Wrong** — push back with technical reasoning (see below)

---

## Receiving feedback

Code review requires technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming.

### The response pattern

1. **Read** — complete feedback without reacting
2. **Understand** — restate each item in your own words, or ask for clarification
3. **Verify** — check against the codebase; does this actually apply here?
4. **Evaluate** — technically sound for this codebase and context?
5. **Implement** — one item at a time, test each; or push back if wrong

### Never

- "You're absolutely right!" / "Great point!" / "Thanks for catching that!" — performative, adds nothing
- Implement before understanding — partial understanding = wrong implementation
- Proceed with unfixed Critical or Important issues

### If feedback is unclear

Stop. Clarify all unclear items before implementing anything. Items may be related;
fixing some without understanding others leads to wrong implementations.

### Pushing back

Push back when the suggestion:
- Breaks existing functionality
- Adds unused features (YAGNI — grep the codebase first)
- Is technically incorrect for this stack
- Conflicts with prior architectural decisions

**How:** Use technical reasoning. Reference working tests/code. Ask specific questions.
State corrections factually: "Checked — this breaks X because Y. Current implementation
handles Z which the suggestion doesn't account for."

### Acknowledging correct feedback

```
✓ "Fixed. [Brief description of what changed]"
✓ "Good catch — [specific issue]. Fixed in [location]."
✓ [Just fix it and show in the code]
```

Actions speak. The code itself shows you heard the feedback.

### Common mistakes

| Mistake | Fix |
|---------|-----|
| Performative agreement | State the fix or just act |
| Implementing before verifying | Check against codebase first |
| Fixing all at once without testing | One item at a time |
| Assuming reviewer is right | Verify; push back if wrong |
| Avoiding pushback | Technical correctness over comfort |
| Proceeding with unclear items | Ask first, implement after |
