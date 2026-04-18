---
name: constraint-solver
description: >
  Take a natural-language problem (scheduling, packing, assignment,
  timetable, cryptarithm, graph-colouring, puzzle) and produce a runnable
  solver. Encode to OR-Tools CP-SAT (for large combinatorial / optimisation
  problems) or Z3 (for exact logical / arithmetic constraints). Always
  report the encoding choice, the model's decision variables, each
  constraint in plain English, the returned solution, and alternative
  solutions when asked. Use when the problem can be stated declaratively
  ("I need X such that Y") rather than procedurally.
---

# constraint-solver

Declarative problem-solving. User describes a feasibility / optimisation
problem; you pick the right back-end (CP-SAT or SMT), encode it, run it,
and explain the result.

## When to use

- **Scheduling / timetabling**: "8 workers, 5 shifts, these constraints."
- **Assignment / matching**: "Assign 12 tasks to 4 people minimising load."
- **Packing**: "Pack these items into these bins."
- **Routing (small)**: "TSP over 20 cities."
- **Puzzles**: Sudoku, KenKen, Latin squares, cryptarithms, nonograms.
- **Graph problems**: colouring, independent set, vertex cover (small).
- **Mixed logic + arithmetic**: "These vars are in this range, this
  formula holds, find all satisfying assignments."

**Don't use** for: continuous optimisation (that's SciPy / CVXPY),
machine-learning fits, general numerical iteration, or anything where
the state space is infinite or continuous (SMT handles some reals but
rarely practical at scale).

## Back-end choice

| Use | Back-end | Why |
|-----|----------|-----|
| Combinatorial + optimisation (scheduling, assignment, routing) | **OR-Tools CP-SAT** | Fast, industrial-strength, great at optimisation, `ortools` on PyPI |
| Pure satisfiability + exact arithmetic (number theory, proofs, mixed theories) | **Z3 SMT** | Rich theory support (bitvectors, arrays, reals), excellent for "find all solutions" |
| Tiny problem, learning mode | Hand-rolled backtracker | Sometimes the pedagogical clarity wins |

Default to **CP-SAT** unless the problem specifically needs Z3's strengths
(rationals, quantifiers, bit-vector arithmetic, find-all-models).

## Output contract

Every solver script must print:

```
# <Problem name>
## Variables
- x_<i><j> ∈ {…}  — <what it means>

## Constraints
1. <plain-English>
2. …

## Objective
<min/max expression, or "feasibility only">

## Solution
<the answer, clearly laid out — not just a raw list>

## Alternatives
<N more solutions, or "proven unique">
```

The user should be able to verify the solution is correct without reading
your code.

## Template — OR-Tools CP-SAT

Save as `solve_<name>.py`, run with `./solve_<name>.py`.

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["ortools"]
# ///
"""Template: shift scheduling.

Workers W cover shifts S. Each shift needs a given head-count,
each worker works at most D shifts in a row and at least M total.
"""
from __future__ import annotations
from ortools.sat.python import cp_model

WORKERS = ["A", "B", "C", "D", "E"]
SHIFTS  = ["Mon-AM", "Mon-PM", "Tue-AM", "Tue-PM", "Wed-AM"]
NEED    = {"Mon-AM": 2, "Mon-PM": 2, "Tue-AM": 1, "Tue-PM": 2, "Wed-AM": 2}
MAX_RUN = 3          # max consecutive shifts
MIN_TOT = 1          # min total shifts per worker

def main():
    m = cp_model.CpModel()
    x = {(w, s): m.NewBoolVar(f"x_{w}_{s}") for w in WORKERS for s in SHIFTS}

    # each shift has exactly NEED[s] workers
    for s in SHIFTS:
        m.Add(sum(x[w, s] for w in WORKERS) == NEED[s])

    # each worker does >= MIN_TOT shifts
    for w in WORKERS:
        m.Add(sum(x[w, s] for s in SHIFTS) >= MIN_TOT)

    # no worker does more than MAX_RUN in a row
    for w in WORKERS:
        for i in range(len(SHIFTS) - MAX_RUN):
            m.Add(sum(x[w, SHIFTS[i + k]] for k in range(MAX_RUN + 1)) <= MAX_RUN)

    solver = cp_model.CpSolver()
    status = solver.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("no feasible assignment"); return

    print(f"{'':8}", *[f"{s:8}" for s in SHIFTS])
    for w in WORKERS:
        print(f"{w:8}", *[f"{'X':^8}" if solver.Value(x[w, s]) else f"{'.':^8}" for s in SHIFTS])

if __name__ == "__main__":
    main()
```

CP-SAT idioms you'll reuse:
- `m.NewIntVar(lo, hi, name)`, `m.NewBoolVar(name)`.
- `m.AddAllDifferent([…])` for Latin-square and assignment structure.
- `m.AddCircuit([…])` for TSP / Hamiltonian cycle constraints.
- `m.Maximize(expr)` / `m.Minimize(expr)` for optimisation.
- `m.AddBoolAnd / AddBoolOr / OnlyEnforceIf` for conditional constraints.

## Template — Z3 SMT

For precise logic / number-theoretic problems.

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["z3-solver"]
# ///
"""Template: find all 10-digit numbers using each digit exactly once
such that the first N digits form a number divisible by N for N in 1..10."""
from z3 import Distinct, Int, Solver, sat, And

def main():
    d = [Int(f"d{i}") for i in range(10)]
    s = Solver()
    for v in d: s.add(v >= 0, v <= 9)
    s.add(Distinct(*d))
    s.add(d[0] != 0)
    for n in range(1, 11):
        num = 0
        for i in range(n): num = num * 10 + d[i]
        s.add(num % n == 0)

    solutions = []
    while s.check() == sat:
        m = s.model()
        sol = [m[v].as_long() for v in d]
        solutions.append(sol)
        # block this solution, search for another
        s.add(Or([v != val for v, val in zip(d, sol)]))

    for s_ in solutions:
        print("".join(map(str, s_)))
    print(f"\n{len(solutions)} solution(s).")

if __name__ == "__main__":
    main()
```

Z3 idioms:
- `Int`, `Bool`, `Real`, `BitVec(name, bits)`.
- `Distinct`, `And`, `Or`, `Implies`, `Not`.
- `solver.check()` → `sat | unsat | unknown`.
- `solver.model()[var]` returns the concrete value; `.as_long()`,
  `.as_fraction()`.
- "Find all": add a blocking clause and re-check until `unsat`.

## Encoding recipes

### All-different
```python
# CP-SAT
model.AddAllDifferent([x[i] for i in range(n)])
# Z3
from z3 import Distinct
s.add(Distinct(*xs))
```

### Element (a[i] == v where i is a variable)
```python
# CP-SAT
model.AddElement(index, table, target)   # table[index] == target
```

### Cumulative / bin-packing
```python
# CP-SAT
model.AddCumulative(intervals, demands, capacity)
```

### Big-M linearisation (avoid when possible)
If you find yourself writing `x <= M * (1 - b)`, you probably want
`model.OnlyEnforceIf(b).Add(…)` instead — CP-SAT supports real
reification natively.

### Symmetry breaking
Order variables to break permutation symmetries (e.g. `x[0] <= x[1]` for
interchangeable workers). Massive speed-ups on symmetric problems.

## Method

1. **Translate the problem.** Identify: entities (workers, jobs, cells),
   decisions (who/what assigned where), constraints (hard + soft),
   objective (if any).
2. **Write the output contract first.** Decide how the solution will be
   printed before you code. If you can't describe the solution cleanly,
   the model's wrong.
3. **Start with feasibility.** Drop the objective, get *any* solution,
   then add cost minimisation.
4. **Model one constraint at a time.** Run after each addition; if the
   model becomes infeasible, the last constraint is the culprit or an
   interaction with an earlier one.
5. **Symmetry and bounds.** Tight variable domains and symmetry-breaking
   constraints dominate solver time.
6. **Explain the solution.** Walk through the constraints, showing each
   one is satisfied.

## Pitfalls

- **Over-constraining.** Users often state soft preferences as hard
  constraints. Ask: "is this a must or a prefer?"
- **Ignoring scale.** CP-SAT handles thousands of booleans easily but
  millions hit memory. For large TSP/routing, use `ortools.routing`, not
  CP-SAT's `AddCircuit`.
- **Real numbers in CP-SAT.** CP-SAT is integer-only. Multiply by 100 or
  1000 to keep precision; convert back at output. Or switch to Z3 for
  genuine reals/rationals.
- **One-off solutions.** If the user wants "all" solutions, use the
  blocking-clause pattern (Z3) or `solver.SearchForAllSolutions` callback
  (CP-SAT).
- **Assuming unique solution.** Many real-world problems have many equal
  optima. Break ties with a secondary objective or symmetry-breaking
  constraints.

## Handoff

- Puzzle-specific use cases → `logic-puzzle-designer` (it dispatches to
  this skill for Slitherlink / Heyawake / global-constraint puzzles).
- Results need narrative explanation → `note-taker`.
- Solution feeds a downstream script or dashboard → emit JSON alongside
  the human-readable print.
