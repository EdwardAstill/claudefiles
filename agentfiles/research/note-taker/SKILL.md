---
name: note-taker
description: >
  Use when creating markdown notes, lessons, study material, or interactive tutorials.
  Trigger on: "make notes on X", "create a lesson about Y", "new readrun page for Z",
  "write up notes with runnable code", "make an interactive tutorial", "write LLM notes
  on X", "create reference docs for Y", "add notes on Z to the knowledge base".
  Handles two modes: human-readable (with optional readrun interactive code) and
  LLM-optimized (dense, structured reference docs for AI consumption).
---

# Note Taker

Create markdown notes in one of two modes:

| Mode | Audience | Style | Features |
|------|----------|-------|----------|
| **Human** | People reading/studying | Pedagogical, explanatory | readrun interactive code, prose explanations |
| **LLM** | AI agents, RAG systems, knowledge graphs | Dense, structured, retrieval-optimized | YAML frontmatter, wikilinks, semantic headers |

---

## Step 0: Gather context and choose mode

| Input | Action |
|-------|--------|
| Topic + target directory | Create notes there |
| Just a topic | Ask where to put them |
| No args | Ask what to write about |

**Choose the mode** based on context:

| Signal | Mode |
|--------|------|
| "lesson", "tutorial", "explain", "study material", "readrun" | Human |
| "reference", "knowledge base", "for agents", "LLM notes", "cheatsheet" | LLM |
| Technical topic with no audience signal | Ask: "Are these notes for a human to read, or for LLM/agent consumption?" |

---

## Step 1: Plan the note structure

Outline before writing:

1. **Title and sections** — what `##` headings will the note have?
2. **Mode-specific planning:**
   - Human: identify code blocks (readrun script files vs inline, plain vs interactive)
   - LLM: identify entities, category, and wikilink targets
3. **Links** — relative links to other notes in the same folder

Present the outline for confirmation before writing files.

---

## Human Mode

### Writing rules

- Lead with explanation, then code — never drop a block without context
- One concept per `##` section
- Every runnable block must produce visible output
- Link between notes with relative links: `[Next](./next-topic.md)`
- Bullets for discrete facts, numbered for sequences
- `$...$` for inline math, `$$...$$` for block math
- Bold for emphasis, backticks for code identifiers

### Plain markdown — standard fences

````
```python
print("display only — not runnable")
```
````

### Readrun — runnable blocks

Ask if the notes should be **readrun-compatible** (runnable code blocks in the browser)
or plain markdown. If readrun: check for `.readrun/scripts/` in the target, create it
if missing. Run `rr help` or `rr guide` for syntax details if needed.

**Script file vs inline rule:** 5+ lines or reused across notes → script file in
`.readrun/scripts/<descriptive-name>.<ext>`. Short one-offs → inline.

**File reference** (preferred for non-trivial scripts):
```
:::variables.py
```

**Inline block:**
```
:::python
x = 42
print(f"The answer is {x}")
:::
```

**Hidden block** (code collapsed by default, Run button always visible):
```
:::python hidden
answer = 42
print(answer)
:::
```

**File upload** (lets readers upload files into Pyodide's filesystem):
```
:::upload "Upload CSV" accept=.csv rename=data.csv
```

**Image reference:**
```
:::diagram.svg
```

### Script conventions

**Python:**
- Always `print()` results — silent scripts look broken
- For third-party packages, add a PEP 723 block:
  ```python
  # /// script
  # dependencies = ["pandas", "matplotlib"]
  # ///
  ```

**JSX (`.jsx`) — preferred for interactive UI:**
- React 18, Tailwind auto-loaded. Call `render(<App />)` to mount.
- Self-contained: define and render in the same file.

**HTML — for canvas/WebGL or non-React JS libraries:**
- JS libraries auto-detected (Plotly, D3, Chart.js, Observable Plot, Three.js, p5.js,
  Leaflet, Mermaid) — just call them, no `<script src>` tags needed.

### Readrun verification

- [ ] Every `:::filename.ext` reference has a matching file in `.readrun/scripts/`
- [ ] Every script produces visible output when run
- [ ] No orphaned scripts or broken references

```
notes-folder/
  topic.md
  .readrun/
    scripts/
      concept-demo.py
      counter.jsx
    images/
      diagram.svg
```

---

## LLM Mode

Notes optimized for AI retrieval, RAG chunking, and knowledge graph extraction.

### Frontmatter (required)

Every file starts with YAML frontmatter:

```yaml
---
title: "Specific Descriptive Title"
category: "domain/subdomain"
summary: "A 1-2 sentence high-level overview of the note's content."
entities: [Entity1, Entity2]
---
```

### Writing rules

1. **Lead paragraph** — the first paragraph after `#` title is a dense, factual summary.
   AI retrieval prioritizes document beginnings. Put the most important information first.

2. **Semantic headers** — headers must be context-rich and keyword-dense so that when a
   section is chunked for RAG, the chunk remains self-descriptive.
   - Bad: `## Mechanism`
   - Good: `## Mechanism of Action of Sodium Channel Blockers`

3. **Explicit references** — no ambiguous pronouns (`it`, `they`, `this`) at the start
   of paragraphs or sentences. Repeat the noun.
   - Bad: "It blocks the receptor and prevents signaling."
   - Good: "`Lidocaine` blocks the voltage-gated sodium channel and prevents action potential propagation."

4. **Lists over prose** — use bullet points for facts, features, steps. LLMs parse
   structured lists more reliably than dense paragraphs.

5. **Wikilinks** — use `[[Wikilinks]]` for internal references instead of standard
   markdown links. They are token-efficient, resilient to folder reorganization, and
   map cleanly to knowledge graph nodes.

6. **Technical terms in backticks** — wrap all technical identifiers, commands, and
   domain-specific terms in backticks.

7. **LaTeX for math** — `$inline$` and `$$display$$` for all mathematical notation.

8. **Specify code block languages** — always tag fenced code blocks with the language.

### LLM verification

- [ ] YAML frontmatter present with title, category, summary
- [ ] Headers are specific and keyword-rich (not generic)
- [ ] No ambiguous pronouns opening sentences
- [ ] Technical terms wrapped in backticks
- [ ] Internal links use `[[Wikilinks]]`
- [ ] First paragraph is a dense factual summary

---

## Style (both modes)

Direct, no filler. One concept per `##` section. Apply `style-guide-notes` if available.
