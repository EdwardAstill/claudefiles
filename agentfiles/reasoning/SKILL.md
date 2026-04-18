---
name: reasoning
description: >
  Category dispatcher for formal problem-solving skills. Routes to
  game-designer (turn a concept into a design doc), logic-puzzle-designer
  (generate Sudoku / nonograms / Kakuro with uniqueness guarantees), or
  constraint-solver (encode a problem to OR-Tools or Z3 and solve it).
---

# Reasoning

Routes to the right reasoning skill based on the task.

## Sub-skills

| Skill | Use when |
|-------|----------|
| `game-designer` | "Design a game about X" — core loop, MDA, progression, balance math, prototype spec |
| `logic-puzzle-designer` | "Generate me a puzzle" — Sudoku, nonogram, Kakuro, Nurikabe, cryptarithm, with uniqueness proof |
| `constraint-solver` | "Solve this optimisation / scheduling / assignment / logic problem" — CP-SAT (OR-Tools) or SMT (Z3) encoding |
