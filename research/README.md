# research/

The system's long-term memory. Everything here exists to improve
`research/knowledge/` — the distilled, queryable summary that agents
consult before making architectural decisions.

```
research/
  papers/          raw: academic PDFs
  projects/        raw: external repo take-aways
  documentation/   raw: third-party platform docs (Claude Code, Anthropic API, …)
  lessons/         raw: session retrospectives
  knowledge/       ★ distilled output — the only dir `af ak` reads
  README.md        this file
```

## The one rule

**`knowledge/` is the destination; everything else is input.**

Papers, external projects, documentation, and session lessons feed into
it. Agents don't search the raw inputs during a task; they query
`knowledge/` via `af ak` and only open the raw sources when a knowledge
page says "see source X in `research/papers/`".

## Subdirs

| Dir | Purpose | Who writes | When to read |
|---|---|---|---|
| `knowledge/` | Distilled write-ups on harness design, memory, context engineering, multi-agent coordination, self-improvement, etc. | `research-agent`, manual synthesis | Before any architectural decision. Primary interface: `af ak list / show / grep`. |
| `papers/` | Academic PDFs (arxiv, conference proceedings) | `sci-hub` skill, manual download | Only when a knowledge page cites a specific paper and you need the primary source. |
| `projects/` | One-file summaries of external GitHub repos (`<owner>-<repo>.md`) with take-aways | `github-repo-researcher` | When evaluating whether another project has solved a problem you're about to solve, or to crib patterns. |
| `documentation/` | Local copies of third-party platform docs (Claude Code, Anthropic API) | Manual or `docs-agent` | When you need current reference material and don't trust ambient built-in knowledge. |
| `lessons/` | Dated session retrospectives — what went wrong, what to repeat | `retrospective` skill | When planning a task that resembles past work. Grep by keyword, read newest first. |

## CLI

```bash
af ak list               # index of knowledge/ pages, flat or nested
af ak show <slug>        # print one page
af ak grep <pattern>     # ripgrep over knowledge/
rg <pattern> research/   # full-tree search (raw inputs too)
```

## How things land here

From inside a session:

- **`af note "finding"`** — captures short observations into
  `.agentfiles/notes.md`. Not in `research/`; gets promoted only if
  the finding survives the session.
- **`lessons/<YYYY-MM-DD-slug>.md`** — written by the `retrospective`
  skill or manually. Short: context, what happened, what to do
  differently, a citation or two.

For a new research topic:

- **`af research <topic>`** scaffolds a deep-research prompt. Run it,
  feed the output back in, then write the synthesis into
  `knowledge/<topic>.md`.
- **Papers go to `papers/`** (use `sci-hub` for academic PDFs). Link
  them from the knowledge page that cites them.
- **External repos go to `projects/`** via the `github-repo-researcher`
  skill.

## Promoting a lesson

A lesson becomes `knowledge/` material when it's no longer a single
observation but a reusable principle. When promoting, cite both the
lesson(s) and any papers that support it. Leave the original lesson
file in `lessons/` — promotion doesn't delete history.

## Relationship to `docs/reference/`

These are not the same thing.

- **`research/`** = long-term memory. Living, accumulating, consulted
  before work.
- **`docs/reference/`** = current design spec. How the system works
  right now, authoritative, read at runtime via skills.

A `knowledge/` page may cite `docs/reference/*.md`. It never duplicates
it. When a knowledge page's evidence contradicts a spec, the spec
change goes through explicit review — note the contradiction in the
knowledge page's "Implications" section first.

## Related

- [../README.md](../README.md) — project overview and mission.
- [../AGENTS.md](../AGENTS.md) — runtime guidance for agents working in
  this repo.
- [../docs/reference/orchestration.md](../docs/reference/orchestration.md)
  — current executor + manager design spec.
