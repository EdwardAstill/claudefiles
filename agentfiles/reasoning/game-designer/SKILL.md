---
name: game-designer
description: >
  Take a game concept and turn it into a concrete, implementable design doc.
  Use when the user says "design a game about X", "help me with game mechanics",
  "balance this combat/economy", "pitch me a roguelike / tower defence / puzzle
  / deckbuilder / …", or wants a prototype spec before any engine is chosen.
  Works at the systems-design level (MDA, core loop, progression, economy) —
  not engine code and not narrative prose. Pairs with writing-plans to go from
  design to implementation.
---

# game-designer

Turn a rough concept into a design doc with enough structure to prototype.
No engine choice, no narrative padding — just systems that hold up.

## When to use

- "Design a game where…"
- "What should the core loop be for X?"
- "Balance this resource economy."
- "What's a MVP prototype for this idea?"
- "This mechanic feels shallow — fix the depth."

**Don't use** for: engine-specific code (use language-experts), narrative/lore
writing (out of scope), art direction (use ui-expert patterns at best).

## Output: a design.md

```
# <Game Title>  —  <one-line hook>

## Pillars (3, no more)
1. …
2. …
3. …

## Core loop
<ASCII or numbered diagram of the second-to-second player activity>

## MDA
| Layer       | Notes |
|-------------|-------|
| Mechanics   | …     |
| Dynamics    | …     |
| Aesthetics  | …     |

## Progression
<What changes over 5 min / 30 min / full run>

## Economy / resources
| Resource | Source | Sink | Notes |
|----------|--------|------|-------|
| …        | …      | …    | …     |

## Failure state
<Lose conditions, punishment, recovery>

## MVP prototype scope
<Smallest slice that proves the core loop — rough feature list>

## Open questions
<3–5 things to playtest>
```

## Method

1. **Extract pillars.** Press the user for three pillars max — anything more is
   indecision. Pillars are fantasy + verb + constraint, e.g. *"Be a cunning
   thief"*, *"Every turn is a puzzle"*, *"You always have less than you need"*.
   If the user can't name three, ask "what's the one moment you want the
   player to remember?" and work backwards.

2. **Define the core loop.** Second-to-second activity: the verb the player
   performs ~20 times in a 10-minute session. If you can't describe it in
   one diagram, the design isn't ready. Name it.

3. **MDA pass.**
   - Mechanics = rules (what are the tokens, actions, win/lose).
   - Dynamics = behaviours that emerge from mechanics × players.
   - Aesthetics = felt experience (the 8 kinds: Sensation, Fantasy, Narrative,
     Challenge, Fellowship, Discovery, Expression, Submission — Hunicke et al.).
   Flag the pillars → aesthetics mapping.

4. **Progression curve.** Three time-scales:
   - Session (5–30 min): what changes between early and late?
   - Meta (across sessions): persistent unlocks, mastery, records?
   - Narrative beats (if any): act structure, reveal cadence.
   If the game is a single session (puzzle, arcade), say so — no meta layer.

5. **Economy math.** For any resource (gold, HP, fuel, XP, action points):
   - Source rate (per action / turn / second).
   - Sink rate (cost per meaningful decision).
   - Ratio should leave the player **slightly short** — scarcity drives
     decisions. If source ≥ sink by a wide margin, the resource isn't a
     decision-maker and should be removed.
   - Sketch formulae: `damage = weapon * (1 + level * 0.1) * randf(0.9, 1.1)`.

6. **Failure state.** Specify *how* players lose, *what* gets lost, and the
   *recovery loop*. Permadeath + full restart is one choice; run-based reset
   with meta-progression is another. Be explicit.

7. **MVP prototype scope.** Smallest slice that proves the core loop. If the
   game is about resource tension, one resource + one enemy type + one map
   is plenty. If it's about deck combos, 20 cards is usually enough.

8. **Open questions.** End with 3–5 *playtestable* questions — not
   preferences. "Does the 3-second attack wind-up feel deliberate or sluggish?"
   not "Should attacks be 3 seconds?".

## Design heuristics to apply

- **One primary verb per scene.** Mix scouting with combat with puzzles
  only if each has its own dedicated loop.
- **Juice comes later.** Design the unsweetened version first; add feedback,
  sound, particles after the mechanics land.
- **Failure must teach.** If dying is random or opaque, the game is broken.
  Players should rebuild a model of the system from each loss.
- **Meaningful choice ≠ many choices.** Three options with visible trade-offs
  beats twelve that feel interchangeable.
- **Loss aversion > gain seeking.** Threatening to take something away is
  usually stronger than promising a reward.
- **Second-to-second > session-to-session.** If minute one is boring, no
  amount of meta progression saves it.
- **Power fantasy ≠ infinite power.** Even god-mode games have constraints.
  Doom Eternal's constraint is ammo scarcity despite the power fantasy.

## Genre-specific red flags

| Genre | Common failure |
|-------|----------------|
| Roguelike | Too much meta-progression → trivialises the run; death loses its sting |
| Deckbuilder | Card counts bloat before archetypes are distinct |
| Metroidvania | Map is interesting but movement is dull — movement IS the verb |
| Tower defence | Strategies collapse to one dominant build — rebalance counters |
| Puzzle | Puzzles are mini-metric increments rather than insight moments |
| RPG | "Level up → numbers bigger" without new decision texture |

## Worked example (short form)

> User: "A card game where you play a detective assembling a case from clues."

1. Pillars: *deduction under uncertainty*, *discard something true to commit*,
   *every case is solvable, never by brute force*.
2. Core loop: draw clue → compare to suspects → discard one suspect OR one
   clue → check if a unique culprit remains → accuse or continue.
3. MDA: Mechanics — deck, suspect grid, discard cost. Dynamics — hand
   management under information-incomplete pressure. Aesthetics — Discovery,
   Challenge.
4. Progression: later cases introduce red herrings (clues that falsely
   implicate), partner characters with special discard rules.
5. Economy: *Certainty* points. Gained by eliminating suspects. Lost by
   wrong accusation. Not regenerated within a case.
6. Failure: wrong accusation → case marked unsolved → next case begins.
7. MVP: 1 case, 5 suspects, 15-clue deck, no partners.
8. Open: Does discarding a clue feel like a sacrifice or a relief?

---

Hand the design doc off to `writing-plans` to get implementation tasks.
