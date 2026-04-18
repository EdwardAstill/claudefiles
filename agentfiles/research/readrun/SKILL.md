---
name: readrun
description: >
  Use when creating or editing readrun documentation — folders of Markdown rendered as
  interactive websites with runnable Python (Pyodide) and live JSX/React visualisations.
  Trigger on: "make readrun docs for X", "add a readrun page", "write an interactive
  tutorial", "document this with JSX widgets", "build a lesson with runnable code",
  "turn these notes into a readrun site", "scaffold a .readrun folder", "add a live
  visualisation to this page". This skill replaces note-taker: any markdown-with-runnable-
  code request lands here. For pure reference / LLM-optimised notes without runnable code,
  still use this skill and skip the executable fences.
---

# readrun

readrun is a Bun-powered CLI (`rr`) that renders a folder of `.md` files as a navigable
website with runnable Python (via Pyodide/WASM) and auto-mounting JSX/React components
(via Babel + Tailwind). Everything executes client-side, so static builds work on any host.

This skill's job is to:

1. Scaffold the right folder layout (`.readrun/scripts`, `.readrun/images`, `.readrun/files`).
2. Write Markdown that uses readrun's fence syntax correctly (`:::python`, `:::jsx`,
   `:::upload`, `:::filename.ext`).
3. Build **JSX visualisations** that explain how a system works — the core deliverable
   when the user says "outline exactly how this works".
4. Verify the site runs (`rr validate`, preview with `rr <folder>`).

---

## Step 0: Decide the shape before writing

| Input | Action |
|-------|--------|
| "Document X" + target directory | Scaffold there, propose page outline, confirm |
| Just a topic | Ask where to put it |
| Existing `.readrun/` folder present | Extend it, do not reinitialise |
| No runnable code wanted | Still use this skill — plain Markdown is a first-class readrun site |

Confirm the page outline (titles, sections, which blocks become JSX visualisations vs
Python vs static diagrams) **before** writing files. readrun has no hot reload, so
getting structure right up front saves page-refresh churn.

---

## Step 1: Scaffold the folder

Point `rr init` at the content folder, or create the layout manually:

```
my-docs/
  welcome.md              # first page — readrun sorts pages alphabetically by default
  concepts/
    overview.md
    internals.md
  reference/
    api.md
  .readrun/
    scripts/              # .py, .jsx, .html, .ts, .js, etc. — referenced via :::filename
    images/               # .svg .png .jpg .gif .webp — referenced via :::filename
    files/                # data files preloaded into Pyodide (open("data.csv") works)
    .ignore               # newline-separated exclude patterns (optional)
```

Rules:

- **No frontmatter required.** readrun reads plain Markdown — leave YAML out unless
  you're also feeding files to an LLM pipeline that needs it.
- **Sidebar is folder-derived.** Nest folders to group pages; the sidebar mirrors the tree.
- **First page** of a folder is what readers land on. Name it `welcome.md`, `overview.md`,
  or `README.md` and lead with a one-paragraph "what is this" and a table of contents.
- **`.readrun/.ignore`** excludes drafts / scratch files from the nav: one glob-ish pattern
  per line, `#` for comments. Common dirs (`node_modules`, `dist`, `.git`, `venv`,
  `__pycache__`) are auto-ignored.

---

## Step 2: Fence syntax catalogue

readrun extends Markdown with a single fence family: `:::`. Everything else is standard
CommonMark, so files stay readable in any Markdown viewer.

### Runnable Python — inline

```
:::python
x = 42
print(f"answer = {x}")
:::
```

- Runs in browser via Pyodide. All Python blocks on a page **share one session** (like
  Jupyter cells) — variables and imports persist.
- Must `print()` or the cell looks broken. Silent `return`s don't render.
- Packages auto-install from `import` statements. Name mismatches (e.g. `PIL` →
  `pillow`, `cv2` → `opencv-python`, `sklearn` → `scikit-learn`) are built in.
- matplotlib works with the Agg backend — call `plt.show()` to render inline.

### Runnable Python — file reference (preferred for ≥5 lines)

```
:::demo.py
```

Loads `.readrun/scripts/demo.py`, displays the source, runs on click. Use a file when
code is long, reused across pages, or contains complex logic.

### Hidden by default

```
:::python hidden
secret_helper()
:::
```

Starts collapsed. Run button still visible. Good for setup / boilerplate readers don't
need to see. Works on any executable fence.

### JSX / React — inline (auto-renders on page load, no Run button)

```
:::jsx
function App() {
  return <h1 className="text-2xl font-bold">hello</h1>;
}
render(<App />);
:::
```

- React 18, ReactDOM, Babel and Tailwind are preloaded.
- Call `render(<Component />)` once — this is the mount call, not standard React.
- Auto-renders on page load (Python blocks only run on click; JSX does not).
- Use Tailwind utility classes — there is no custom CSS pipeline.

### JSX — file reference

```
:::counter.jsx
```

Loads `.readrun/scripts/counter.jsx`. Same auto-render behaviour. Prefer files for
anything > ~15 lines or reused across pages.

### File upload → Pyodide filesystem

```
:::upload "Upload CSV" accept=.csv rename=data.csv
```

Renders a button. Dropped file is written into Pyodide's virtual filesystem; later
Python blocks read it with `open("data.csv")`. Flags: `accept=.ext`, `multiple`,
`rename=fixed-name.ext`.

### Image / SVG embed

```
:::diagram.svg
```

Loads from `.readrun/images/`, inlines as base64, click-to-enlarge in lightbox. Use for
static diagrams that don't need interactivity — interactive ones should be JSX.

### HTML / canvas / D3 / Plotly etc.

```
:::widget.html
```

Loads `.readrun/scripts/widget.html`. readrun auto-loads common libraries when it
detects their globals (Plotly, D3, Chart.js, Observable Plot, Three.js, p5.js, Leaflet,
Mermaid) — no `<script src>` tags needed. Use HTML when React is the wrong shape
(canvas-heavy, a D3 chart, a Three.js scene).

### Standard triple-backtick fences

```python
print("display only")
```

Plain fences render with syntax highlighting but **no Run button**. Use for shell
commands, config snippets, or pseudo-code that must not execute.

### Links between pages

Standard Markdown links with `.md` targets. readrun rewrites them for site nav:

```markdown
See [internals](./internals.md) or go back to the [overview](../welcome.md).
```

Absolute URLs (`https://…`) are left alone.

### Math

`$inline$` and `$$block$$` render via KaTeX when `@vscode/markdown-it-katex` is
installed in the project. Don't assume it is — if the user wants math, confirm the
package is present or add it.

---

## Step 3: Build JSX visualisations that "outline exactly how this works"

This is the core deliverable when the user wants visual documentation. A good readrun
JSX visualisation has these properties:

1. **Explains one concept per widget.** Flow of data through a pipeline, state
   transitions in a protocol, the anatomy of a request — one idea, one widget.
2. **Has interactive state.** A static SVG is fine, but if it could be a JSX widget
   with hover / click / step-through controls, make it one.
3. **Is self-contained.** One file, one `render()` call. No external imports beyond
   `React`, `ReactDOM` (already global). No build step.
4. **Tailwind-only styling.** Utility classes, no CSS-in-JS libraries.
5. **Legible in light and dark themes.** readrun ships 8 themes; prefer Tailwind
   colours that work across them (`text-zinc-700`, `bg-slate-100 dark:bg-slate-800`),
   and avoid baking in a single background colour.

### JSX visualisation patterns

| Pattern | When to use | Core mechanic |
|---------|-------------|---------------|
| **Stepper / timeline** | Protocol, pipeline, request/response flow | `useState(step)` + prev/next buttons, arrow through numbered stages |
| **Toggle diagram** | "With X vs without X" | Boolean `useState`, swap the rendered structure |
| **Animated flow** | Data moving through a system | `useEffect` + `setInterval`, draw dots along an SVG path |
| **Interactive parameter** | Show how a function responds to inputs | Slider `<input type="range">` → `useState` → recomputed derived value → rendered bars / line |
| **Tabbed deep-dive** | Multiple perspectives on the same system | `useState(tab)` + button row + conditional render |
| **Tree / graph explorer** | Hierarchies, dependency graphs, ASTs | Recursive component over a static tree literal, click-to-expand |

Save the component in `.readrun/scripts/<topic>-<pattern>.jsx` and reference with
`:::<topic>-<pattern>.jsx`. Name files so a reader browsing the `scripts/` sidebar tab
can guess their purpose.

### JSX skeleton — copy this

```jsx
function SystemFlow() {
  const [step, setStep] = React.useState(0);
  const stages = [
    { title: "Request arrives", body: "..." },
    { title: "Router matches", body: "..." },
    { title: "Handler runs", body: "..." },
  ];
  const s = stages[step];

  return (
    <div className="border rounded-lg p-4 space-y-3 bg-slate-50 dark:bg-slate-800">
      <div className="flex gap-2">
        {stages.map((_, i) => (
          <button
            key={i}
            onClick={() => setStep(i)}
            className={`px-3 py-1 rounded ${i === step ? "bg-blue-600 text-white" : "bg-slate-200 dark:bg-slate-700"}`}
          >
            {i + 1}
          </button>
        ))}
      </div>
      <h3 className="font-semibold">{s.title}</h3>
      <p className="text-sm text-slate-600 dark:text-slate-300">{s.body}</p>
      <div className="flex justify-between">
        <button disabled={step === 0} onClick={() => setStep(step - 1)} className="px-3 py-1 disabled:opacity-30">← prev</button>
        <button disabled={step === stages.length - 1} onClick={() => setStep(step + 1)} className="px-3 py-1 disabled:opacity-30">next →</button>
      </div>
    </div>
  );
}
render(<SystemFlow />);
```

For SVG-heavy diagrams, wrap an `<svg viewBox="...">` inside the same component and
drive positions / colours from state.

---

## Step 4: Authoring rules (both plain and runnable pages)

- **Prose-first.** readrun is a document renderer, not a notebook. Lead each `##`
  section with explanation, then the block.
- **One concept per `##` section.** Keeps TOC useful and page-refresh friction low.
- **Every runnable block must produce visible output.** Python → `print`; JSX → `render`.
- **No ambiguous pronouns at section starts.** After a chunk break, repeat the noun —
  helps both readers and RAG chunking if the site is re-indexed later.
- **Technical identifiers in backticks.** Commands, flags, function names, env vars.
- **Bullets for discrete facts, numbered lists for ordered steps.**
- **Bold sparingly** — for the load-bearing noun of a paragraph, not for emphasis.
- **Do not add `README`-style banners, badges, emoji headers.** readrun pages are
  documents, not landing pages.

---

## Step 5: Preview and verify

```bash
rr <folder>           # dev server on http://localhost:3001
rr validate <folder>  # check that every :::filename reference resolves
```

Verification checklist before handing the docs back:

- [ ] Every `:::filename.ext` has a matching file in `.readrun/scripts/` or `.readrun/images/`.
- [ ] Every Python block `print`s something; every JSX block calls `render()`.
- [ ] No orphaned scripts or images in `.readrun/` that nothing references.
- [ ] Internal `[text](./page.md)` links resolve to real files.
- [ ] `rr validate <folder>` exits clean.
- [ ] Start `rr <folder>`, click through the pages, confirm JSX widgets mount and
      Python blocks run without uncaught errors.

If validation surfaces a missing file, either add the file or remove the reference —
never leave broken `:::` lines in the Markdown.

---

## Step 6: Build (when the user asks to publish)

```bash
rr build <folder>            # plain static HTML to ./dist
rr build github <folder>     # + .nojekyll and Actions workflow
rr build vercel <folder>     # + vercel.json
rr build netlify <folder>    # + netlify.toml
```

Base paths for GitHub Pages auto-detect from the git remote. Everything runs
client-side, so any static host works — no server runtime.

---

## Limits to communicate up front

If the user proposes something that readrun cannot do, say so before writing code:

- **No native network from Python.** `requests`, `urllib`, sockets — all blocked. If the
  page needs to fetch data, fetch it in JSX with `fetch()` or preload it into
  `.readrun/files/`.
- **No C-extension packages** outside Pyodide's pre-built set. Pure Python + Pyodide's
  scientific stack (numpy, pandas, scipy, matplotlib, scikit-learn) work; most ML
  frameworks and DB drivers don't.
- **No filesystem persistence across reloads.** Pyodide's FS resets on refresh. Users
  must click download on generated files to keep them.
- **No live reload.** Markdown edits need a page refresh. For JSX edits, refresh too.
- **No client-side routing.** Page nav is a full reload, which resets Python state.
- **Mobile UX is not a goal.** Sidebars hide on narrow screens; widgets should still
  be readable but don't design mobile-first.

---

## Quick decision tree

```
Is there code the reader should run?
├── No  → plain Markdown + `:::filename.svg` for static diagrams
├── Python, short, one-off       → inline `:::python` fence
├── Python, reusable / long      → file in .readrun/scripts/*.py + `:::file.py`
├── Interactive UI / diagram     → JSX, file in .readrun/scripts/*.jsx + `:::file.jsx`
├── Canvas / D3 / Three.js       → HTML in .readrun/scripts/*.html + `:::file.html`
└── Reader supplies input data   → `:::upload` button + Python block that reads the file
```

When in doubt: **prefer a JSX visualisation** over a static diagram. That's what makes
readrun worth the infrastructure.
