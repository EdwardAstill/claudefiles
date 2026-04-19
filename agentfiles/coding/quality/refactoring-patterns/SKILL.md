---
name: refactoring-patterns
description: >
  Use for deliberate large-scale restructuring of existing code — not
  quick cleanup, but a multi-step transformation that keeps tests green
  throughout. Trigger phrases: "refactor this module", "apply strangler
  fig to migrate off X", "extract this method", "break up this god
  object", "replace this conditional with polymorphism", "introduce a
  parameter object", "parallel change to swap implementations", "feature
  work is blocked by structural debt", "split this file into smaller
  modules", "migrate from pattern A to pattern B without a rewrite". Do
  NOT use for recently written messy code (use simplify), for code
  that works and doesn't need to change (leave it alone), for
  performance (use performance-profiling), for bugs (use
  systematic-debugging), or for greenfield rewrites (use the strangler
  fig pattern here instead).
---

# Refactoring Patterns

Large-scale, deliberate restructuring of existing code using proven patterns.
Every step keeps tests green — no big-bang rewrites.

**Core principle:** Refactoring changes structure without changing behavior.
If behavior changes, it's not refactoring — it's a feature or a bug.

## When to Use

- Codebase has grown organically and is hard to extend
- Feature work is blocked by structural debt
- Same change requires touching many unrelated files
- New team members can't understand the code
- God objects, god functions, or tangled dependencies
- Migrating from one architecture pattern to another
- Preparing code for a major feature addition

## When NOT to Use

- **Recently written code that's just messy** — use `simplify`
- **Code that works and doesn't need to change** — leave it alone
- **Performance problems** — use `performance-profiling` first, refactor only if structure is the bottleneck
- **Bugs** — use `systematic-debugging` to fix first, then refactor
- **Rewriting from scratch** — almost always wrong; use strangler fig instead

## The Iron Law

```
EVERY REFACTORING STEP MUST KEEP TESTS GREEN
```

If tests fail after a refactoring step, revert that step. Refactoring is
behavior-preserving by definition. Red tests mean you changed behavior.

## Process

### Phase 1: Assess and Plan

1. **Map the current structure** — understand what exists before changing it
   - Draw dependency graph (who calls whom)
   - Identify the pain points — where does development slow down?
   - Measure: how many files does a typical change touch?

2. **Define the target structure** — what should it look like after?
   - Don't design the ideal system — design the next step
   - Smaller target = higher success rate

3. **Ensure test coverage** — you cannot refactor what you cannot verify
   - Run existing tests — what's the coverage?
   - If coverage is low, write characterization tests first
   - Characterization tests capture current behavior, right or wrong

4. **Choose the pattern** — pick from the catalog below

### Phase 2: Execute Incrementally

1. **One pattern at a time** — don't combine Extract Method with Move Class
2. **Small commits** — each commit is a complete, green refactoring step
3. **Run tests after every step** — not after "a batch of changes"
4. **Review the diff** — does this commit change behavior? If yes, split it

### Phase 3: Verify

1. **All tests pass** — no exceptions, no skips, no "we'll fix that later"
2. **Behavior is identical** — same inputs produce same outputs
3. **Structure is improved** — the pain point from Phase 1 is reduced
4. **New structure is documented** — update architecture docs if they exist

## Pattern Catalog

### Strangler Fig

**When:** Migrating from old system to new system incrementally.

1. Build new implementation alongside old
2. Route traffic/calls to new implementation one piece at a time
3. Old and new coexist — no big-bang cutover
4. Remove old code only after new code handles all cases

**Key:** Both implementations must be runnable simultaneously.

### Extract Method / Extract Function

**When:** Function is too long or does too many things.

1. Identify a coherent block of code within the function
2. Extract it into a new function with a descriptive name
3. Replace the original block with a call to the new function
4. Run tests

### Introduce Parameter Object

**When:** Multiple functions share the same group of parameters.

```python
# Before: same params everywhere
def create_order(customer_id, customer_name, customer_email, ...):
def send_receipt(customer_id, customer_name, customer_email, ...):

# After: parameter object
@dataclass
class Customer:
    id: str
    name: str
    email: str

def create_order(customer: Customer, ...):
def send_receipt(customer: Customer, ...):
```

### Replace Conditional with Polymorphism

**When:** Switch statements or if/elif chains that dispatch on type.

```python
# Before: conditional dispatch
def calculate_price(item):
    if item.type == "book":
        return item.base_price * 0.9
    elif item.type == "electronics":
        return item.base_price * 1.2
    elif item.type == "food":
        return item.base_price

# After: polymorphism
class Book(Item):
    def calculate_price(self):
        return self.base_price * 0.9

class Electronics(Item):
    def calculate_price(self):
        return self.base_price * 1.2
```

### Parallel Change (Expand-Migrate-Contract)

**When:** Changing an interface that has many callers.

1. **Expand** — add new interface alongside old (both work)
2. **Migrate** — move callers from old interface to new, one at a time
3. **Contract** — remove old interface once all callers have migrated

**Key:** At no point does any caller break.

### Move to Layered Architecture

**When:** Business logic is tangled with I/O, HTTP, or database code.

1. Identify pure business logic buried in handlers/controllers
2. Extract into domain layer (no I/O imports)
3. Have handlers call domain layer, passing data in and out
4. Domain layer becomes testable without mocking infrastructure

## Anti-patterns

| Anti-pattern | Why It Fails | Instead |
|-------------|-------------|---------|
| Big-bang rewrite | Months of parallel work, never reaches parity | Strangler fig — incremental migration |
| Refactoring without tests | No way to verify behavior is preserved | Write characterization tests first |
| Mixing refactoring with features | Can't tell if test failure is from refactoring or feature | Separate commits: refactor, then feature |
| "While I'm here" refactoring | Scope creep, harder to review, riskier | One purpose per commit |
| Refactoring working code that nobody changes | No return on investment | Only refactor code that's actively painful |
| Designing the perfect architecture | Analysis paralysis, over-engineering | Design the next step, not the final state |
| Skipping the planning phase | Refactoring in circles, no clear target | Map current → define target → execute |
| Not committing between steps | Large, unrecoverable diff | Small commits, each one green |

## Measuring Success

| Metric | Before | After |
|--------|--------|-------|
| Files touched per feature | Many unrelated files | Localized changes |
| Time to understand code area | Hours | Minutes |
| Test execution time for affected area | N/A (no tests) | Seconds |
| Cyclomatic complexity of hot spots | High | Reduced |

## Outputs

- Refactoring plan with pattern selection and step sequence
- Characterization tests for untested code (if needed)
- Series of green commits, each a complete refactoring step
- Updated architecture documentation
- Chain into `tdd` for new tests, `verification-before-completion` to confirm
