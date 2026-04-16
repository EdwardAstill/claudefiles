---
name: make-quiz
description: >
  Generate a ReadRun `.quiz.md` file from a `.quizspec` recipe, inline arguments, or interactively.
  ALWAYS use this skill when the user asks to: make a quiz, generate quiz questions, create a .quiz file,
  build a quiz from code, quiz me on this repo, or test my knowledge.
  Trigger even on casual phrasings like "quiz me on X", "make a quiz about Y", "test me on this codebase",
  or "generate questions from this repo".
  This skill governs the full quiz generation workflow — source ingestion, question design, formatting, and output.
  A `.quizspec` YAML is accepted as optional input but is NOT required — the skill can work interactively
  or from inline arguments without one. When no spec is provided, the skill generates its own spec as a guide.
---

# Make Quiz

Generate a `.quiz.md` file for the ReadRun app (`rr`). A `.quizspec` can optionally be provided as a recipe, but the skill works fine without one — it will ask the user or infer what's needed and generate a spec internally as a guide.

**All output goes to `.readrun/quizzes/` in the current working directory.** This is where `rr` looks for local quizzes. The user runs `rr <dir>` and accesses the Quizzes tab in the browser.

**Always output `.quiz.md` (markdown format)** unless the user explicitly asks for JSON. Markdown is the recommended format — no escaping, no index arithmetic, and LaTeX works naturally.

---

## Output directory

All generated files go into `.readrun/quizzes/` in the current working directory:
- `.readrun/quizzes/<name>.quiz.md` — the generated quiz
- `.readrun/quizzes/<name>.quizspec` — the spec used to generate it (saved for reuse)

Create the `.readrun/quizzes/` directory if it doesn't exist. Tell the user they can run `rr <dir>` and open the Quizzes tab to access their quizzes.

---

## Step 0: Route the request

Check what the user provided:

| Input | Action |
|-------|--------|
| A `.quizspec` file path | Read it → go to [Phase 2: Ingest Sources](#phase-2-ingest-sources) |
| A `.quizspec` YAML string (pasted inline) | Parse it → go to Phase 2 |
| Inline flags (`--source`, `--count`, etc.) | Build a spec from flags → write to `.readrun/quizzes/` → go to Phase 2 |
| A topic (e.g. "quiz me on React hooks") | Ask clarifying questions → write spec to `.readrun/quizzes/` → go to Phase 2 |
| Just `/make-quiz` with no args | Ask what to quiz on → write spec to `.readrun/quizzes/` → go to Phase 2 |

### Inline flag mapping

| Flag | Spec field |
|------|-----------|
| `--source <path>` | `sources: [{type: folder/file/pdf, path}]` (infer type from path) |
| `--url <url>` | `sources: [{type: url, url}]` |
| `--pdf <path>` | `sources: [{type: pdf, path}]` |
| `--count <n>` | `parameters.count` |
| `--difficulty <level>` | `parameters.difficulty` |
| `--types <list>` | `parameters.types` (comma-separated) |
| `--teach` | `parameters.teach: true` |
| `--focus <topics>` | `focus` (comma-separated) |
| `-o <path>` | `output` |

---

## Phase 1: Generate the `.quizspec` (if none provided)

A spec is NOT required — the user might just say "quiz me on React hooks" and that's enough. But you always produce a `.quizspec` file as a reusable recipe, even if you build it yourself from the conversation.

Ask the user enough to fill in the spec. At minimum you need:

1. **Source material** — ask:
   > What material should I build the quiz from?
   > - **This codebase** — I'll analyze the code in the current project
   > - **Files/folders** — give me a path (e.g. `~/notes/physics/`)
   > - **A URL** — give me a link to fetch
   > - **A PDF** — give me a path to a PDF file
   > - **A topic** — just tell me what to quiz you on (I'll use my own knowledge)
   >
   > You can combine multiple sources.

2. **Parameters** — ask about difficulty, count, teach mode, or accept defaults

3. **Focus/exclude** — if the source material is broad, ask what to focus on

4. **Notes** — ask if there are any special instructions (e.g. "explain things step by step", "focus on common exam pitfalls", "I'm weak on X")

Then **write the `.quizspec` file** to `.readrun/quizzes/` in the current directory.

---

## Phase 2: Ingest sources

Read the spec and process each source:

**Folder:** Glob for matching files → Read each (prioritize by `focus` if too many)
**File:** Read directly
**URL:** WebFetch the page → extract main content
**PDF:** Read with `pages` parameter if specified → chunk large PDFs (20 pages at a time)
**Codebase:** Read heuristically (README, entry points, core modules, types, config) or use glob if specified
**Topic only (no sources):** Use your own knowledge — no ingestion needed

**Important:** For large sources, summarize and focus on material matching `focus` topics rather than trying to read everything.

---

## Phase 3: Analyze and plan

1. **Identify key concepts** from the combined material
2. **Apply focus/exclude filters** from the spec
3. **Categorize by difficulty:**
   - Beginner: definitions, recall, basic facts
   - Intermediate: relationships, cause-and-effect, comparisons
   - Advanced: synthesis, application, debugging, edge cases
4. **Read the `notes` field** — apply any special instructions to the plan
5. **Present the plan to the user** — show what topics/sections you'll cover and get confirmation

---

## Phase 4: Generate questions

Follow the [Question Design Rules](#question-design-rules) and respect all spec parameters:

- Generate approximately `count` questions (±20%)
- Only use question types listed in `types`
- Match the `difficulty` level
- If `teach: true`, add substantial info pages before each section (mini-lessons, not just headers)
- If `sections: true`, organize into section groups
- If `hints: true`, include hints
- Honor `notes` for tone, approach, and special instructions

---

## Phase 5: Output

Check the spec's `generate` field to determine single vs. batch mode:

### Combined mode (default)

1. Determine output path: spec's `output` field, or `.readrun/quizzes/<spec-name>.quiz.md`
2. Validate the quiz (see [Validation Checklist](#validation-checklist))
3. Write the `.quiz.md` file
4. Tell the user: "Run `rr <dir>` and open the Quizzes tab to take the quiz."

### Batch mode (`per_file` or `per_source`)

When `generate.mode` is `per_file` or `per_source`, produce multiple quizzes:

1. **Split sources** — in `per_file` mode, expand folder sources into individual files. In `per_source` mode, treat each source entry as its own unit
2. **Loop:** For each unit, run Phase 2 (ingest), Phase 3 (analyze), and Phase 4 (generate) independently, scoped to that unit's material only
3. **Name each quiz** — derive file names from sources (see naming rules). Use `generate.title_from` to set each quiz's title (`filename`, `heading`, or `content`)
4. **Write to `generate.output_dir`** — create the directory if needed. Validate each quiz before writing
5. **Report results** — tell the user how many quizzes were generated and where they are

**Important for batch mode:**
- Each quiz is independent — don't reference material from other files
- Apply the same `parameters`, `focus`, `exclude`, and `notes` to each quiz
- If a source file is too small to generate `count` questions, generate as many as the material supports and note this

---

## Question Design Rules

- **Mix question types** — never make the entire quiz single-choice. Use all allowed types where appropriate
- **Progression** — start easier, build to harder concepts within each section
- **Structure with sections** — use section items to organize by topic, with info pages introducing each section
- **Good distractors** — wrong options must be plausible. Use common misconceptions, off-by-one errors, similar-looking alternatives
- **Explanations are mandatory** — every question must have an explanation. Explain *why* the answer is correct and *why* common wrong answers are wrong
- **Code in questions** — use fenced code blocks for multi-line code snippets, inline backticks for identifiers
- **Free text answers must be short** — 1-3 words, unambiguous. If the answer could be phrased multiple ways, use single/multi choice instead
- **Groups for related concepts** — when testing multiple aspects of one topic, use a question group with a shared prompt
- **No trick questions** — challenging but fair. The goal is learning, not gotchas
- **Teach mode info pages** — when `teach` is true, info pages should be substantial: explain the concept clearly with examples, formulas, and context *before* testing

### Difficulty calibration

| Level | Question style | Example |
|-------|---------------|---------|
| Beginner | "What is X?" / "Which of these is Y?" | "What does HTTP stand for?" |
| Intermediate | "Why does X happen?" / "What's the difference between X and Y?" | "Why does TCP use a three-way handshake?" |
| Advanced | "Given this scenario..." / "What would happen if..." / Debug-style | "A server returns 200 but the client sees a CORS error. What's the most likely cause?" |

---

## Markdown Quiz Format (`.quiz.md`)

**Always use this format.** Only use JSON if the user explicitly requests it.

```
---                              ← YAML frontmatter (required)
title: Quiz Title
description: Optional subtitle
---

## [info] Heading                ← info page
:::                              ← extended body block (optional)
Markdown content...
:::

# Section Title                  ← section (groups items in sidebar)

## [single] Question text        ← single-choice question
- Wrong option
- Correct option *               ← trailing * marks the correct answer
- Another wrong option
?> Hint text                     ← hint (shown before answering)
> Explanation text               ← explanation (shown after answering)

## [multi] Question text         ← multiple-choice question
- Wrong
- Correct *                      ← multiple * for multiple correct
- Also correct *
- Wrong

## [truefalse] Statement text    ← true/false question
true *                           ← * marks which value is correct

## [freetext] Question text      ← free-text question
= Expected answer                ← exact-match answer

## [group] Shared prompt         ← question group
### [truefalse] Sub-question 1   ← sub-questions use ###
true *
### [freetext] Sub-question 2
= Answer
```

### Element reference

| Element | Syntax |
|---------|--------|
| Frontmatter | `---` / `title:` / `description:` / `---` |
| Section | `# Section Title` |
| Item | `## [type] Text` — type is `single`, `multi`, `truefalse`, `freetext`, `info`, or `group` |
| Group sub-question | `### [type] Text` |
| Extended body | `:::` block after heading (supports code fences inside) |
| Options | `- Option text` (append ` *` for correct) |
| True/false answer | `true *` or `false *` on its own line |
| Free text answer | `= answer text` |
| Hint | `?> hint text` |
| Explanation | `> text` (multiline: each line starts with `> `) |

### Extended body blocks (`:::`)

For question text longer than the heading — code snippets, multi-paragraph prompts, etc.:

```markdown
## [single] Consider the following code:
:::
```python
def foo(x):
    return x * 2
```

What does `foo(3)` return?
:::
- 3
- 6 *
- 9
```

### Markdown and math

All text fields support Markdown and LaTeX math:
- **Inline math:** `$E = mc^2$`
- **Display math:** `$$\int_0^\infty e^{-x}\,dx = 1$$`

**Warning: `$` as currency.** Write `500 USD` or `US$500` — never bare `$500` (triggers math mode). Inside math blocks, use `\text{\textdollar}` not `\$`.

---

## Validation Checklist

Before writing the file:

- [ ] Correct answers are marked — trailing ` *` on correct options, `true *`/`false *`, `= answer` for freetext
- [ ] Free text answers are short (1-3 words, no ambiguity)
- [ ] Every question has an explanation
- [ ] Distractors are plausible (real misconceptions, not absurd fillers)
- [ ] At least 3 different question types used
- [ ] Info pages before new sections
- [ ] No bare `$` for currency
- [ ] Difficulty progression within each section
- [ ] No trick questions
- [ ] Output is `.quiz.md` (not JSON)

---

## Anti-patterns

| Don't | Do instead |
|-------|-----------|
| All single-choice questions | Mix in multi, truefalse, freetext, and groups |
| Obvious wrong answers | Plausible distractors based on real misconceptions |
| Free text with long/ambiguous answers | Use single choice for anything > 3 words |
| 20 questions with no structure | Use sections and info pages |
| Missing explanations | Always explain — this is where learning happens |
| `$500` for currency | Write `500 USD` or `US$500` |
| Generating `.quiz` JSON | Use `.quiz.md` unless explicitly asked |

---

## Example Output

```markdown
---
title: AWS Solutions Architect
description: Practice exam for SAA-C03
---

## [info] AWS Solutions Architect
:::
This quiz covers key topics for the **SAA-C03** exam.
:::

# S3 Storage

## [single] Which S3 storage class is cheapest for infrequent access?
- S3 Standard
- S3 Glacier
- S3 Standard-IA
- S3 One Zone-IA *
?> Think about which class trades redundancy for lower cost.
> One Zone-IA is cheapest but lacks multi-AZ redundancy.

## [group] Answer the following questions about S3:

### [truefalse] S3 bucket names must be globally unique.
true *
> Bucket names share a global namespace across all AWS accounts.

### [freetext] What does S3 stand for?
= Simple Storage Service

# Serverless & IAM

## [multi] Which services are serverless? (select all that apply)
- EC2
- Lambda *
- DynamoDB *
- RDS
> Lambda and DynamoDB require no server management.

## [freetext] What does IAM stand for?
= Identity and Access Management
?> Three words: **I**___ **A**___ **M**___
> IAM controls who can do what in your AWS account.
```

---

## Example Interactions

### Interactive (no spec)

```
User: /make-quiz
Assistant: What material should I build the quiz from?
  ...

User: This codebase, focus on API routes and DB layer, advanced, ~20 questions, teach mode.
Assistant: [Writes .readrun/quizzes/codebase-review.quizspec, reads codebase, generates quiz]
Assistant: Saved to .readrun/quizzes/codebase-review.quiz.md (20 questions, 4 sections, teach mode).
  Run `rr <dir>` and open the Quizzes tab to take it.
```

### With an existing spec

```
User: /make-quiz physics-midterm.quizspec
Assistant: [Reads spec, ingests sources, generates quiz]
Assistant: Written to .readrun/quizzes/physics-midterm.quiz.md (25 questions, 5 sections).
  Run `rr <dir>` and open the Quizzes tab.
```
