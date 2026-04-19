# anthropics/courses

**URL:** https://github.com/anthropics/courses
**Stars:** ~20,700 | **Type:** Official teaching resource (Jupyter notebooks)

## What It Is

Anthropic's official educational repo — a sequence of five interactive courses delivered almost entirely as Jupyter notebooks. Designed to be worked through in order:

- **Anthropic API Fundamentals** — SDK basics, model parameters, multimodal prompts, streaming
- **Prompt Engineering Interactive Tutorial** — step-by-step technique drills (also republished as an AWS workshop)
- **Real World Prompting** — assembling production-grade prompts from technique primitives
- **Prompt Evaluations** — writing evals to measure prompt quality before shipping
- **Tool Use** — implementing function/tool calling in agent workflows

Notebooks default to Claude 3 Haiku to keep API costs negligible while learners iterate.

---

## What It Does Well

- **Pedagogical sequencing** — fundamentals → techniques → real-world assembly → evals → tool use is a deliberate ramp, not a grab-bag of demos
- **Notebook-native** — every concept is paired with a runnable cell and an editable prompt; learners can fork and mutate in place
- **Evaluations as a first-class topic** — most community tutorials skip evals entirely; making it course #4 signals it's not optional
- **Cheap to run** — Haiku-by-default means a learner can complete the full sequence for cents, lowering the barrier to actually finishing

---

## Weaknesses

- **API-shaped, not agent-shaped** — focused on raw API calls, not Claude Code / agent harness patterns; tool use is the one bridge
- **Notebook-only** — no CLI, no scripts, no install path; cannot be lifted into a project as reusable code
- **Claude 3-era examples** — some prompt patterns predate Sonnet 4 / Opus 4.x reasoning improvements and may be over-engineered for current models

---

## Take

The single best public reference for *how Anthropic itself teaches prompting and evals*. Pull the **evals course** in particular — most agent platforms (agentfiles included) ship without an evals story, and this repo lays out the conceptual scaffolding (test sets, grading rubrics, eval-driven iteration) that should inform any future skill-quality measurement system. Skip if you're looking for Claude Code / hooks / skills patterns specifically.
