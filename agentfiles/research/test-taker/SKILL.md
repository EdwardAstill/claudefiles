---
name: test-taker
description: >
  Use when given a set of questions to answer using provided reference material.
  Takes a questions path, an information path, a strictness level (rough-guide,
  strong-guide, or only-information), and an output path. Produces a single
  answers.md with all questions answered. For calculation questions (math, physics,
  etc.) creates and runs Python scripts, including computed output in the answers.
---

# Test Taker

Answer a set of questions using provided reference material. All answers go into a
single markdown file. Calculation questions get Python scripts that run and feed
results into the answers.

## Inputs

Collect these before starting. Ask for any that are missing:

| Input | What it is |
|-------|-----------|
| **Questions path** | File or directory containing the questions |
| **Information path** | File(s) or directory of reference material to draw from |
| **Strictness** | How closely to follow the information (see below) |
| **Output path** | Directory where `answers.md` and scripts will be written |
| **Readrun mode** | Optional — see below |

### Readrun mode (optional)

After collecting the inputs above, ask:

> "Do you want readrun mode? This makes calculation scripts runnable in the browser —
> `answers.md` uses `:::script.py` references and scripts go into `.readrun/scripts/`."

**If yes:**
- Run `rr init <output-path>` if `.readrun/` doesn't exist yet
- Scripts go to `<output-path>/.readrun/scripts/q<N>_<slug>.py`
- `answers.md` references scripts with `:::q<N>_<slug>.py` instead of code blocks
- Run `rr help` or `rr guide` if you need syntax details

**If no (default):** scripts go to `<output-path>/scripts/`, answers embed output
in triple-backtick code blocks as normal.

## Strictness Modes

**`rough-guide`**
The information is useful context but not a constraint. Draw freely on general
knowledge. No labelling required.

**`strong-guide`**
The information is the primary source. Prefer answers derivable from it. When
supplementing with general knowledge, label it clearly: `[general knowledge]`.

**`only-information`**
Answer exclusively from the provided information. Do not add outside knowledge.
When a question cannot be answered from the information alone, flag it:

```
⚠️ Outside information required: this question requires knowledge of [topic],
which is not covered in the provided material.
```

## Process

### Step 1: Read everything

```
Read all questions — note total count
Read all information — build a working understanding of the material
```

If questions are in a directory, read all files and treat them as one ordered set.
If information is a directory, read all files.

### Step 2: Classify each question

For each question, decide:
- **Factual/conceptual** — answer directly in markdown
- **Calculation** — requires math, physics, or computation → write a Python script

Calculation questions include: anything with numbers to compute, equations to solve,
unit conversions, statistical calculations, simulations, or geometric/physical problems.

### Step 3: Write scripts for calculation questions

For each calculation question, create:
- Default: `<output-path>/scripts/q<N>_<slug>.py`
- Readrun mode: `<output-path>/.readrun/scripts/q<N>_<slug>.py`

```python
#!/usr/bin/env python3
"""
Q<N>: <question text, truncated to ~80 chars>
"""

# Constants and given values
# ...

# Calculation
# ...

# Output
print(f"Result: ...")
```

Rules:
- Use only the standard library unless numpy/scipy are clearly needed
- Comment each step with the physical/mathematical reasoning
- `print()` the final answer in plain language with units
- One script per calculation question — don't combine unrelated questions

### Step 4: Run all scripts

```bash
python3 <output-path>/scripts/q<N>_<slug>.py
```

Capture stdout. If a script errors, note the error in the answer and provide a
manual calculation as fallback.

### Step 5: Write answers.md

Write `<output-path>/answers.md`.

**Default format:**
```markdown
# Answers

*Questions: <source path>*
*Information: <info path>*
*Strictness: <mode>*

---

## Q1: <question text>

<answer>

---

## Q2: <question text>

<answer>

**Computed result:**
```
<script output>
```
*Script: `scripts/q2_<slug>.py`*

---
```

**Readrun mode format** — use `:::` file references instead of embedding output:
```markdown
## Q2: <question text>

<answer>

:::q2_<slug>.py
```

**Formatting rules:**
- Number questions sequentially (Q1, Q2, ...)
- Include the full question text as the heading
- Default: embed script output in a code block, reference the script file
- Readrun mode: use `:::q<N>_<slug>.py` so readers can run calculations interactively
- For `only-information` flags: place the ⚠️ warning directly under the question heading
- Keep answers concise but complete — don't pad

### Step 6: Confirm

Report when done:

```
answers.md written to <output-path>/
<N> questions answered
<N> scripts created and run in <output-path>/scripts/
<N> questions flagged (only-information mode) [if applicable]
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Answering before reading all information | Read everything first, then answer |
| Skipping script for a borderline calculation | When in doubt, write the script — it shows the work |
| Scripts that don't print a clear final answer | Always end with a plain-language print statement |
| Combining multiple questions in one script | One script per question, named by question number |
| Forgetting to run scripts before writing answers.md | Run first, embed output second |
