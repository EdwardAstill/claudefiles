# Reasoning Region

Skills for formal problem-solving, rule design, and constraint reasoning. Distinct from `research/` (lookup) and `planning/` (execute).

---

### game-designer
- **Purpose:** Take a game concept → produce a concrete design doc: core loop, MDA breakdown, progression, economy/balance math, prototype spec
- **Use when:** "Help me design a game", "make mechanics for X", "balance this combat system", "pitch a roguelike about Y"
- **NOT for:** Implementing a game engine (that's coding) or writing narrative prose (that's creative writing)
- **Produces:** `design.md` with pillars, core loop diagram, MDA table, progression curve, resource math, MVP feature list
- **Chains into:** writing-plans (turn design into implementation plan), dsa-expert (for algorithmic AI/pathfinding bits)

### logic-puzzle-designer
- **Purpose:** Generate valid logic puzzles with guaranteed uniqueness and a given difficulty — Sudoku, nonograms, Kakuro, Nurikabe, ASCII kenken, cryptarithmetic
- **Use when:** "Make me a hard Sudoku", "generate 20 nonograms", "build a puzzle with these constraints"
- **NOT for:** Solving an external puzzle the user already has (that's dsa-expert + specific solver)
- **Produces:** Puzzle grid + solution + difficulty grade. Runnable `uv run` script per puzzle family.
- **Chains into:** note-taker (print puzzle book), test-taker (verify solution)

### constraint-solver
- **Purpose:** Take a natural-language problem (scheduling, packing, assignment, cryptarithm, timetable) → encode to OR-Tools CP-SAT or Z3 → solve → explain
- **Use when:** "Assign 8 workers to 5 shifts with constraints", "pack these boxes", "solve SEND+MORE=MONEY", "I have these dependencies, what's the order?"
- **NOT for:** Pure arithmetic (calculator), general search (dsa-expert), or ML optimisation (out of scope)
- **Produces:** Runnable `uv run` Python script + printed solution + constraint-by-constraint explanation
- **Chains into:** (terminal — outputs a concrete assignment)
