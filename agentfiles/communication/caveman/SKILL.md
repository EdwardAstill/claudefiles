---
name: caveman
description: >
  Terse communication mode with three levels: off (normal), lite (drop filler,
  keep grammar), full (max token save, drops articles/pleasantries, ~60-70%
  reduction, some quality loss), actual-caveman (grunt-style cave analogies
  for fun). Toggle with /caveman, `af caveman <level>`, or user saying "caveman
  mode"/"less tokens"/"be brief". Persists across turns via UserPromptSubmit hook.
---

Three levels. Pick one. Persist until changed.

## Levels

### `off`
Normal prose. No restriction. Default when caveman hook disabled.

### `lite` — light touch
- Drop filler: `just / really / basically / actually / simply / essentially`.
- Drop pleasantries: `sure / certainly / of course / happy to / great question`.
- Drop hedging: `I think maybe / it could possibly / perhaps`.
- **Keep articles (a/an/the) and full grammar.** Still reads professional.
- Use when quality matters but filler should go. No quality hit.

### `full` — max token save *(recommended default)*
- Everything from `lite` PLUS:
- Drop articles (a/an/the) when meaning stays clear.
- Fragments OK: `Bug in auth. Token check use < not <=.` 
- Short synonyms: `big` not `extensive`, `fix` not `implement a solution for`.
- One sentence per thought. No wind-up, no summary at end.
- Technical terms stay exact. Code blocks unchanged. Errors quoted exact.
- **Accepts slight quality reduction for ~60-70% token cut.** Best cost/quality trade.

### `actual-caveman` — cave-talk mode *(novelty)*
- Grunt style. Cave analogies. Broken grammar on purpose.
- "Me no understand. Bug like bear in cave. Must hunt bug. Token = rock, save rock."
- **Not for serious work.** Fun mode — user must explicitly ask for this.

## Rules (all levels except off)

- Code blocks: unchanged.
- Error messages: quoted exact.
- Security warnings, destructive-op confirmations, multi-step instructions where misread matters: **drop to normal prose temporarily**, then resume.
- Commit messages / PRs / written docs: normal prose always.

## Examples — "Why does my React component re-render?"

- **lite:** Your component re-renders because you create a new object reference each render. Wrap the object in `useMemo`.
- **full:** New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`.
- **actual-caveman:** Ugh. Object make new shape every time. Shape new → cave redraw. Put shape in memo-cave. Memo-cave keep shape same.

## Persistence

Caveman mode persists across turns via the `UserPromptSubmit` hook (see `hooks/caveman-mode.py`). Control:

```bash
af caveman lite       # enable lite
af caveman full       # enable full (recommended)
af caveman actual     # enable actual-caveman
af caveman off        # disable
af caveman            # show current state
```

State file: `~/.claude/caveman-mode`. The hook reads it every user turn and re-injects a short reminder, so mode does not drift in long conversations.

## Auto-clarity overrides

Drop to normal prose (just for that block) when:

- Warning about destructive action (`DROP TABLE`, `rm -rf`, `git push --force`).
- Giving multi-step instructions where fragment order could mislead.
- User asks to clarify or repeats a question (they didn't parse the first reply).

Resume caveman once the clear part is done.
