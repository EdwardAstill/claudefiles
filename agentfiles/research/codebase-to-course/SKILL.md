---
name: codebase-to-course
description: >
  Turn any codebase into a self-contained interactive HTML course that
  teaches how the code works to non-engineers. Use when the user says
  "turn this repo into a course", "make a tutorial from this codebase",
  "explain this project interactively", "teach me this code", "build a
  walkthrough from this repo", or "codebase as a course". Produces a
  directory with styled HTML/CSS/JS that opens in a browser with zero
  setup — scroll-based modules, embedded mermaid diagrams, quizzes, and
  plain-English side-by-side code translations. Complements
  codebase-explainer (which produces a markdown architecture summary for
  engineers); this skill produces a teaching artefact for vibe coders.
---

# codebase-to-course

Transform a codebase into an interactive single-page HTML course.
Adapted from the approach in
`zarazhangrui/codebase-to-course`. Target audience: **vibe coders** —
people who build with AI coding tools and need enough mental model to
steer the AI, detect hallucinations, and debug, without becoming full
engineers.

## When to use

- User already runs / uses the app but doesn't know how it works inside.
- User wants to learn from an open-source project before forking it.
- User wants onboarding material for collaborators who aren't devs.
- User wants a "how this thing works" artefact for a portfolio / blog.

**Don't use** when the user wants an architecture summary for a fellow
engineer — that's `codebase-explainer`. Use this when the reader is
deliberately *not* a software engineer.

## Output

A directory next to the project (default `./course/`) containing:

```
course/
  index.html           # assembled entry point
  styles.css           # design system, fixed across projects
  main.js              # scroll + quiz + diagram interactions
  module-01.html       # "what does this do & what happens on click"
  module-02.html       # "meet the actors"
  module-03.html       # "how the pieces talk"
  module-04.html       # "the outside world (APIs, DBs)"
  [module-05+.html]    # optional — one per genuine additional concept
```

Open `index.html` directly in any modern browser. No build step. Only
external dep: Google Fonts CDN.

## Method

### Phase 1 — Analyse the codebase

Read enough to have a mental model before you write a line of HTML.

- README + repo topology (use `codebase-explainer` as the warm-up).
- Main entry points — trace one full user action end-to-end.
- Identify the **cast of characters**: major components / services /
  modules. Name them like people.
- Map **data flow**: who calls whom, where state lives, what's cached.
- Note the **tech stack** and why each piece is there.
- Pull **notable patterns**: clever caching, error handling, lazy load,
  rate limiting, retries. These make great teaching moments.
- Skim **git log** + **TODO/FIXME** comments for real bugs that teach.

### Phase 2 — Curriculum design

**4–6 modules.** Only exceed 6 if the codebase genuinely has that many
distinct teachable concepts. Fewer, meatier modules beat more, thinner ones.

The arc always zooms from **experience → implementation**:

| # | Topic | Why a vibe coder cares |
|---|-------|------------------------|
| 1 | "Here's what this does — and what happens when you use it" | Grounds in concrete behaviour they've already seen |
| 2 | Meet the actors | So they can say "put this in X, not Y" when steering AI |
| 3 | How the pieces talk | Data flow knowledge = debugging "why isn't it showing up" |
| 4 | The outside world | External APIs / DBs / files — cost, rate limits, failure modes |
| 5 | (optional) Clever patterns used here | Pattern vocabulary to request / recognise elsewhere |
| 6 | (optional) Where this breaks | Gotchas, edge cases, known limits |

Every module answers **"why should I care?"** *before* "how does it
work?" — and the "why" is always practical: better AI steering, faster
debugging, smarter architectural decisions.

### Phase 3 — Write each module

Each module gets its own `module-NN.html` with four parts:

1. **Hook** — one paragraph, concrete and grounded in user experience.
   *"You paste a YouTube URL and click Analyze. Here's what happens."*
2. **Plain-English explanation** — never assume prior CS knowledge.
   Every term defined inline the first time it appears.
3. **Code with side-by-side translation** — the real code on the left,
   a plain-English narration on the right. Not pseudocode — real excerpts
   with link-back to files.
4. **Check-yourself quiz** — 2–4 questions. Not trivia; scenarios that
   test the mental model. "If X broke, where would you look?"

Also embed one **mermaid diagram per module** (sequence / flowchart /
component). Mermaid renders client-side with `<pre class="mermaid">`.

### Phase 4 — Assemble

`index.html` stitches the module fragments with scroll-linked navigation,
a progress bar, and a module index sidebar. `styles.css` and `main.js`
are copy-pasted templates (users iterating on content shouldn't wait
for AI to regenerate boilerplate).

## Tone

- Smart friend, not professor. Conversational, not dry.
- No "as you probably know" — always define, never assume.
- Precise vocabulary: teach the exact word ("namespace package") so they
  can reuse it when talking to AI later.
- Concrete examples from this codebase only. No fabricated analogies.
- Light humour OK. Academic tone not OK.

## Don'ts

- Don't write a CS textbook. Teach just enough to understand *this* code.
- Don't cover every file. Cover the 20% that drives 80% of the behaviour.
- Don't regenerate `styles.css` / `main.js` per run — they're templated.
- Don't hallucinate patterns that aren't in the code. If there's no
  caching layer, don't pretend there is to teach caching.
- Don't dump 50 lines of code per example. 5–15 is the sweet spot.

## Handoff

- Wants a markdown architecture doc for engineers instead → `codebase-explainer`.
- Wants a quiz *only*, not a course → `make-quiz`.
- Wants formal lecture notes → `note-taker` (LLM / human modes).
- Wants to host the output → the directory is already static; any static
  host works (GitHub Pages, Netlify drop).

## Attribution

This skill's curriculum structure, audience framing, and module
progression are adapted from `zarazhangrui/codebase-to-course`. The HTML
template idiom (pre-built CSS/JS, per-module HTML) is deliberately the
same so the output looks polished without regenerating boilerplate.
