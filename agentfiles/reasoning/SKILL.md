---
name: reasoning
description: >
  Use when the user asks a formal problem-solving question that dispatches to
  a specialist: designing a game, generating a logic puzzle, or solving a
  declarative constraint problem. Trigger phrases: "design a game", "generate
  a puzzle", "make me a sudoku", "solve this scheduling problem", "encode this
  to a solver", "help me pick between game / puzzle / constraint approaches",
  "I have a reasoning problem but I don't know the family", "route me to the
  right solver skill". Routes to game-designer, logic-puzzle-designer, or
  constraint-solver. Do NOT use when the sub-skill is already known — invoke
  that skill directly. Do NOT use for open-ended research or tradeoff analysis
  (use research-agent) or codebase mental-model building (use codebase-explainer).
---

# Reasoning

Routes to the right reasoning skill based on the task.

## Sub-skills

| Skill | Use when |
|-------|----------|
| `game-designer` | "Design a game about X" — core loop, MDA, progression, balance math, prototype spec |
| `logic-puzzle-designer` | "Generate me a puzzle" — Sudoku, nonogram, Kakuro, Nurikabe, cryptarithm, with uniqueness proof |
| `constraint-solver` | "Solve this optimisation / scheduling / assignment / logic problem" — CP-SAT (OR-Tools) or SMT (Z3) encoding |
