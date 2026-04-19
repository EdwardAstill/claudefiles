---
name: logic-puzzle-designer
description: >
  Use when generating uniquely-solvable logic puzzles at a target difficulty —
  Sudoku, nonograms, Kakuro, Nurikabe, KenKen, cryptarithms, Slitherlink,
  Masyu, ASCII mazes. Trigger phrases: "make me a sudoku", "generate N puzzles
  at hard difficulty", "build a nonogram from this image", "create a
  cryptarithm whose answer is X", "I need puzzles for a puzzle book", "give me
  a kakuro", "design a slitherlink", "generate an easy / medium / hard puzzle",
  "build a logic puzzle where the solution encodes this word". Always runs the
  solver to confirm exactly one solution and grades difficulty by minimum
  technique required. Do NOT use for solving a puzzle the user already has
  (use constraint-solver or dsa-expert directly), for non-deductive word games
  like crosswords / word-search (needs dictionaries, out of scope), or for
  designing videogames / board games (use game-designer).
---

# logic-puzzle-designer

Generate puzzles that are (a) solvable by pure logic, (b) uniquely
solvable, and (c) graded for difficulty. Every generator script uses
`uv run --script` PEP 723 so there is zero install pollution.

## When to use

- "Make me a Sudoku / nonogram / Kakuro at <difficulty>."
- "Generate 20 puzzles for a puzzle book."
- "Build a puzzle where the solution encodes this word."
- "I need a cryptarithm whose answer is X."

**Don't use** for: solving a puzzle the user has (just write the solver
directly with dsa-expert), or for non-deductive puzzles (crosswords,
word-search — those need dictionaries, not logic).

## Core workflow

```
1. Parse request     →  puzzle family, size, difficulty, constraints
2. Pick generator    →  the right algorithm for that family
3. Generate candidate → random seed + valid fill
4. Dig holes         →  remove clues while preserving uniqueness
5. Grade difficulty  →  run the solver, measure required techniques
6. Render output     →  grid + solution + metadata
```

**Uniqueness is non-negotiable.** A puzzle with 2+ solutions is broken.
Every generator MUST run the solver to confirm exactly one solution
before returning. If not unique, dig fewer holes or restart.

## Puzzle families and algorithms

| Family | Generator | Solver / uniqueness check |
|--------|-----------|---------------------------|
| **Sudoku** (9×9, 4×4, 16×16) | Fill diagonal boxes → solve → remove cells | Backtracking solver; abort on 2nd solution |
| **Nonogram** (up to 25×25) | Draw random pattern → emit row/col clues | DP per-line, SAT for global; check uniqueness |
| **Kakuro** | Place sums → fill digits with no-repeat | Backtracking with domain propagation |
| **Nurikabe / Fillomino** | Lay island seeds → grow to target sizes | BFS with connectivity invariants |
| **KenKen / MathDoku** | Place Latin square → group cells into cages | Solve cage arithmetic + row/col uniqueness |
| **Cryptarithm** | Start from target assignment → pick words | Z3 / brute force; verify unique digit mapping |
| **Slitherlink** | Shade regions → read loop edges | SAT encoding (edges + parity) |
| **Masyu / Light Up / Heyawake** | Constraint-driven placement | SAT-encoded |

If the family isn't in this table, reach for **OR-Tools CP-SAT** or **Z3**
(see the `constraint-solver` skill) as a general puzzle back-end.

## Difficulty grading

Grade by **the minimum technique required** to solve by pure logic, not
by timing:

| Grade | Sudoku example | Nonogram example |
|-------|----------------|------------------|
| Easy | Only naked singles | Only row/col full/empty forced |
| Medium | Hidden singles, locked candidates | Overlap analysis only |
| Hard | X-wing, swordfish, pointing pairs | Edge-based chaining |
| Expert | Forcing chains, unique rectangles | SAT-complete, no single-line deduction |

A solver that only implements naked singles can't grade a hard puzzle —
grade by the weakest solver that succeeds without guessing.

## Output contract

Always produce three things:

1. **Puzzle** — the grid with clues and blanks, printed as ASCII or PNG.
2. **Solution** — the fully-filled grid (kept separate for unspoiled play).
3. **Metadata** — family, size, difficulty grade, generator seed (for
   reproducibility), and technique breakdown ("needs: naked single×12,
   hidden single×4, pointing pair×2").

Write to `./puzzle_<family>_<n>.txt` (or `.json` for machine-readable)
unless the user specifies otherwise.

## Reference template — Sudoku (runnable)

Save to `gen_sudoku.py` and run with `./gen_sudoku.py 30 hard`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate uniquely-solvable Sudoku puzzles."""
from __future__ import annotations
import random, sys
from copy import deepcopy

N = 9; B = 3

def solve_count(grid, limit=2, count=0):
    for r in range(N):
        for c in range(N):
            if grid[r][c] == 0:
                for v in range(1, N + 1):
                    if valid(grid, r, c, v):
                        grid[r][c] = v
                        count = solve_count(grid, limit, count)
                        grid[r][c] = 0
                        if count >= limit:
                            return count
                return count
    return count + 1

def valid(g, r, c, v):
    if any(g[r][x] == v for x in range(N)): return False
    if any(g[x][c] == v for x in range(N)): return False
    br, bc = (r // B) * B, (c // B) * B
    return not any(g[br + i][bc + j] == v for i in range(B) for j in range(B))

def fill(grid):
    for r in range(N):
        for c in range(N):
            if grid[r][c] == 0:
                nums = list(range(1, N + 1))
                random.shuffle(nums)
                for v in nums:
                    if valid(grid, r, c, v):
                        grid[r][c] = v
                        if fill(grid): return True
                        grid[r][c] = 0
                return False
    return True

def dig(grid, target_clues):
    cells = [(r, c) for r in range(N) for c in range(N)]
    random.shuffle(cells)
    clues = N * N
    for r, c in cells:
        if clues <= target_clues: break
        saved = grid[r][c]
        grid[r][c] = 0
        if solve_count(deepcopy(grid)) != 1:
            grid[r][c] = saved
        else:
            clues -= 1
    return grid, clues

DIFFICULTIES = {"easy": 40, "medium": 32, "hard": 26, "expert": 22}

def render(grid):
    out = []
    for r, row in enumerate(grid):
        if r and r % 3 == 0: out.append("------+-------+------")
        out.append(" ".join(
            (str(v) if v else ".") + (" |" if c % 3 == 2 and c < 8 else "")
            for c, v in enumerate(row)
        ))
    return "\n".join(out)

def main(target_clues: int, label: str):
    random.seed()
    solution = [[0]*N for _ in range(N)]
    fill(solution)
    puzzle = deepcopy(solution)
    puzzle, clues = dig(puzzle, target_clues)
    print(f"# Sudoku — {label}  ({clues} clues)\n")
    print("## Puzzle\n")
    print(render(puzzle))
    print("\n## Solution\n")
    print(render(solution))

if __name__ == "__main__":
    lvl = sys.argv[1] if len(sys.argv) > 1 else "medium"
    tgt = DIFFICULTIES.get(lvl, int(sys.argv[1]) if sys.argv[1].isdigit() else 32)
    main(tgt, lvl)
```

## Reference template — cryptarithm (uses Z3)

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["z3-solver"]
# ///
"""Find words/digit-mapping satisfying word1 + word2 = result."""
from __future__ import annotations
from z3 import Distinct, Int, Solver, sat, And
import sys, string

def solve(a: str, b: str, c: str) -> dict | None:
    letters = sorted(set(a + b + c))
    assert len(letters) <= 10, "too many distinct letters"
    vs = {L: Int(L) for L in letters}
    s = Solver()
    for v in vs.values(): s.add(v >= 0, v <= 9)
    s.add(Distinct(*vs.values()))
    for w in (a, b, c):
        s.add(vs[w[0]] != 0)  # no leading zero

    def to_int(w):
        n = 0
        for ch in w: n = n * 10 + vs[ch]
        return n

    s.add(to_int(a) + to_int(b) == to_int(c))
    if s.check() != sat: return None
    m = s.model()
    return {L: m[v].as_long() for L, v in vs.items()}

if __name__ == "__main__":
    a, b, c = sys.argv[1:4]
    mapping = solve(a.upper(), b.upper(), c.upper())
    if not mapping:
        sys.exit(f"No solution: {a} + {b} = {c}")
    print(f"{a} + {b} = {c}")
    for L, d in sorted(mapping.items()): print(f"  {L} = {d}")
```

Run: `./gen_crypta.py send more money` → maps `SEND + MORE = MONEY`.

## When to reach for CP-SAT / Z3

Write a bespoke backtracker for: Sudoku, nonogram, Kakuro, simple Latin
squares. Reach for **OR-Tools CP-SAT** or **Z3** for: Slitherlink, Masyu,
Heyawake, anything with global constraints (connectivity, closed loops,
parity). See `constraint-solver` for the encoding patterns.

## Pitfalls

- **Forgetting the uniqueness check.** A puzzle with 2+ solutions is just
  a guess. Always run the solver to `count=2` and abort if reached.
- **Digging too aggressively.** Fewer clues ≠ harder; can become unsolvable
  by pure logic. Stop digging as soon as another hole breaks uniqueness.
- **Timing as difficulty.** Use technique-complexity, not human timing.
  Solvers don't feel tired; use the minimum solver required.
- **Deterministic seeds in "random" puzzles.** `random.seed()` with no arg
  uses OS entropy — prefer that for freshness. Accept a `--seed` flag for
  reproducibility.
- **ASCII only.** Produce both ASCII and (where useful) PNG / SVG via
  trivial `matplotlib` or `cairosvg` scripts. Ask the user which.

## Handoff

- Print a puzzle book → `note-taker` (wrap in markdown + page breaks).
- Need the solution checked independently → run the solver script again
  on the output — a good puzzle passes.
- Batch generation → wrap the generator in a loop; write JSONL one puzzle
  per line.
