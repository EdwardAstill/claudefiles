---
name: simplify
description: >
  Use when implementation is working and tests pass, to review recently changed
  code for unnecessary complexity. Covers DRY violations, dead code,
  over-engineering, poor naming, long functions, and clever-but-opaque logic.
  Does not add features or change behavior — only makes correct code clearer.
next: [verification-before-completion]
---

# Simplify

## Overview

Working code is the baseline, not the goal. The goal is working code that the next
reader (including you, six months from now) can understand without effort.

**Core principle:** Simplify only what was recently changed. Don't roam. Don't improve
things just because you noticed them. Finish by running the tests — behavior must be
identical.

## When to Use

After implementation is working and tests pass:
- You finished a feature or bugfix and the code feels tangled
- A function grew during debugging and is now longer than it needs to be
- You made something work but aren't sure it's as clear as it could be
- Code review feedback says "this is hard to follow"

**Don't use when:**
- Tests are not passing (fix the bug first — use `systematic-debugging`)
- The goal is adding capability (use `test-driven-development`)
- You're rewriting code that wasn't recently touched

## What to Check

### Duplication (DRY violations)

Repeated logic that has to be maintained in multiple places is a bug waiting to happen.

```
Look for:
- Near-identical blocks differing only in a variable
- The same computation repeated in two functions
- Copy-pasted conditionals with minor variations
```

Extract to a well-named function or constant. One definition, many uses.

### Dead code

Code that cannot run or is never called adds noise without benefit.

```
Look for:
- Variables assigned but never read
- Functions defined but never called
- Branches that can never be reached
- Commented-out code blocks
```

Delete it. If it's needed later, git history has it.

### Over-engineering

Abstractions built for one use case. Generality introduced before there's a second use case.

```
Look for:
- Interfaces with a single implementation
- Strategy/factory patterns with one strategy or one product
- Parameters that are always called with the same value
- Configuration that is never varied
```

Flatten it. YAGNI — you ain't gonna need it. Add the abstraction when the second case arrives.

### Naming

Names carry meaning. Bad names force the reader to re-derive what you already know.

```
Look for:
- Single-letter variables outside of tight loops
- Generic names: data, result, temp, obj, item, thing
- Boolean names that don't read as true/false: processed, flag, status
- Function names that describe implementation rather than intent: doStuff, handleIt
```

Rename to what the value _is_ or what the function _does_. Names should make the code
self-documenting.

### Long functions

A function doing more than one thing is hard to name, hard to test, and hard to reason about.

```
Signs a function is too long:
- Needs comments inside the body to explain sections
- More than ~20-30 lines (context-dependent)
- Has multiple levels of indentation for unrelated reasons
- The name can't be written without using "and"
```

Extract sub-operations into named helpers. The top-level function becomes a readable
summary; the helpers contain the detail.

### Unnecessary complexity

Clever code that requires effort to decode. Optimizations that aren't needed at this scale.

```
Look for:
- Bit manipulation where arithmetic is clearer
- Nested ternaries
- Chained method calls that obscure the data flow
- Early returns nested inside each other for no readability benefit
- Regex for something a simple string method handles
```

Prefer the boring, obvious solution. Clarity beats brevity.

## What Simplify Does NOT Do

- **No new features.** YAGNI.
- **No behavior changes.** The output of the code must be identical before and after.
- **No refactoring for its own sake.** Only change what is genuinely unclear.
- **No touching code that wasn't recently changed.** Scope creep turns a cleanup into a
  rewrite.

## The Process

1. **Identify scope.** What code changed? Use `git diff` to confirm.
2. **Read it.** Go through the changed code cold, as if seeing it for the first time.
   Note anything that requires re-reading.
3. **List candidates.** What triggers the checks above?
4. **Simplify one thing at a time.** Small, verifiable steps.
5. **Run tests after each change.** Behavior must stay identical.
6. **Stop when it reads clearly.** Not when it's perfect — when it's clear.

## Anti-patterns

| Pattern | Why it's wrong |
|---------|---------------|
| Simplifying code you didn't touch | Scope creep — save it for a dedicated cleanup pass |
| Combining simplify with feature work | Mixed commits are hard to review and hard to revert |
| Removing code "just in case" | Check it's actually dead before deleting |
| Renaming everything at once | High risk, hard to review — do one rename, verify, continue |
| Over-extracting tiny helpers | 3-line helpers that are called once don't reduce complexity |

## Output

- Cleaner, readable code in the changed files
- Tests still passing
- A commit that changes structure without changing behavior (suitable for a clean
  `git log` message like `refactor: simplify X`)
