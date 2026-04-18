# research/knowledge/

Distilled agent knowledge. The only directory `af ak` reads.

Every file here answers a load-bearing question about how this system
*should* work. Raw sources live in sibling dirs (`../papers/`,
`../projects/`, `../documentation/`, `../lessons/`) and are consulted
only when a knowledge page points at them.

## Stable citation IDs

Every page has an `id: K-NNN` frontmatter field. IDs are stable — once
assigned, never change — even if the file is renamed or moved.

When referencing a knowledge page from a skill, a retrospective, a lesson,
or a code comment, cite it by id:

```
See [K-003] for the memory taxonomy.
...per the three retrieval strategies in [K-003]...
```

The id is the contract. Filenames can drift (rename for clarity, move to a
subfolder); the id keeps citations valid.

**Assigning a new id:** next integer, zero-padded to 3. If `af ak list` shows
up to `K-012`, the next page is `K-013`. Ids are global across the flat dir
and any future subfolders — they don't reset per folder.

**Resolving citations from the CLI:**

```bash
af ak show K-003           # resolves by id
af ak show memory-and-learning   # resolves by slug (same page)
```

## Filename convention

Flat at the top level. Name files for the concept they cover:

```
knowledge/
  context-engineering.md
  harness-foundations.md
  memory-and-learning.md
  multi-agent-coordination.md
  self-improving-agents.md
```

Use a **prefix convention** when related files start to accumulate.
Example: future eval research would land as `eval-bench-setup.md`,
`eval-rubric-design.md`, `eval-scoring.md`. Alphabetical sort groups
them automatically under `af ak list`.

## Promotion rule

A prefix becomes a subfolder when **both** hold:

1. ≥5 files share the prefix.
2. The files split into sub-areas that need navigation beyond the filename.

Until both are true, keep flat. Premature subfolders add drilling cost
without navigation value.

When you do promote, it's a rename:

```bash
mv eval-*.md eval/
# then strip the prefix:
cd eval/ && for f in eval-*.md; do mv "$f" "${f#eval-}"; done
```

## Page structure

Each page is a document that a reader (human or agent) can pick up cold
and act on. Structure:

1. **First H1** — the topic name. Appears in `af ak list`.
2. **Opening paragraph** — one paragraph stating what the page covers
   and why it matters. No preamble.
3. **Core claims with citations.** Every non-trivial claim cites a
   paper in `../papers/`, a repo in `../projects/`, or a lesson in
   `../lessons/`.
4. **Implications for agentfiles** — a section that translates the
   general findings into concrete recommendations for this system.
5. **Sources** — at the bottom, list every referenced paper/repo/lesson.

Keep pages grep-friendly: headings are nouns, not questions. Bullets for
discrete facts, numbered lists only for ordered steps.

## What does NOT go here

- Raw notes, scratch thinking, partial drafts → `.agentfiles/notes.md`.
- Session-specific retrospectives → `../lessons/`.
- Summaries of external repos → `../projects/`.
- Academic PDFs → `../papers/`.
- Current design specs → `docs/reference/` (outside `research/`).

## CLI

```bash
af ak list                  # every page here + first heading
af ak show <slug>           # print one page (slug = filename without .md)
af ak grep <pattern>        # ripgrep over this dir only
```
