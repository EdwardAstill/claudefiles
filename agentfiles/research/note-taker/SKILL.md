---
name: note-taker
description: >
  Use when creating markdown notes, lessons, study material, or interactive tutorials.
  Trigger on: "make notes on X", "create a lesson about Y", "new readrun page for Z",
  "write up notes with runnable code", "make an interactive tutorial". Handles both
  plain markdown and readrun-compatible notes with runnable code blocks.
---

# Note Taker

Create markdown notes with optional runnable code blocks. Supports plain markdown and
readrun sites — where code runs interactively in the browser.

---

## Step 0: Gather context

| Input | Action |
|-------|--------|
| Topic + target directory | Create notes there |
| Just a topic | Ask where to put them (or use cwd) |
| No args | Ask what to write about |

Ask if the notes should be **readrun-compatible** (runnable code blocks in the browser)
or plain markdown. If readrun: check for `.readrun/scripts/` in the target, create it
if missing. Run `rr help` or `rr guide` for syntax details if needed.

---

## Step 1: Plan the note structure

Outline before writing:

1. **Title and sections** — what `##` headings will the note have?
2. **Code blocks** — for each:
   - Plain markdown: use standard triple-backtick fences
   - Readrun: script file (`.readrun/scripts/name.py`) or inline (`:::python ... :::`)?
     - Rule: 5+ lines or reused across notes → script file. Short one-offs → inline.
     - **Prefer JSX** for interactive UI. **HTML** for canvas/WebGL or non-React JS libs.
3. **Links** — relative links to other notes in the same folder

Present the outline for confirmation before writing files.

---

## Step 2: Write scripts (readrun mode only)

For each script identified in Step 1, write to `.readrun/scripts/<descriptive-name>.<ext>`.
Name descriptively (`variables.py`, `counter.jsx`) — not `script1.py`.

**Python:**
- Always `print()` results — silent scripts look broken
- For third-party packages, add a PEP 723 block:
  ```python
  # /// script
  # dependencies = ["pandas", "matplotlib"]
  # ///
  ```
- stdlib only for static/Pyodide mode; third-party works in live mode

**JSX (`.jsx`) — preferred for interactive UI:**
- React 18, Tailwind auto-loaded. Call `render(<App />)` to mount.
- Auto-renders as a seamless visualization — no code display by default.
- Self-contained: define and render in the same file.

**HTML — for canvas/WebGL or non-React JS libraries:**
- JS libraries auto-detected (Plotly, D3, Chart.js, Observable Plot, Three.js, p5.js,
  Leaflet, Mermaid) — just call them, no `<script src>` tags needed.
- Renders in a sandboxed iframe that auto-resizes to content.

---

## Step 3: Write the markdown

### Plain markdown — standard fences

````
```python
print("display only — not runnable")
```
````

### Readrun — runnable blocks

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

### Writing rules

- Lead with explanation, then code — never drop a block without context
- Every runnable block must produce visible output
- One concept per section — multiple scripts → subsections
- Link between notes with relative links: `[Next](./next-topic.md)`

---

## Step 4: Verify structure

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

## Style

Direct, no filler. One concept per `##` section. Bullets for discrete facts, numbered
for sequences. `$...$` for inline math, `$$...$$` for block math. Bold for emphasis,
backticks for code identifiers. Apply `style-guide-notes` if available.
