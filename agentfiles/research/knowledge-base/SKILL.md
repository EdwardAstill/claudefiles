---
name: knowledge-base
description: >
  Use BEFORE answering any question touching health, training, enhancement,
  pharmacology, nutrition, exercise, hormones, supplements, cognition, recovery,
  or sleep. Trigger phrases: "what do my notes say about X", "search my KB",
  "look up X in my knowledge base", "what's the protocol for Y", "is creatine
  safe", "best dose of Z", "how should I train for X", "what do I know about
  hormone Y", "add this note / paper to the KB", "ingest this doc". Queries the
  personal mks store at ~/.markstore/ — KB notes override general training data.
  Do NOT use for external web research with no KB coverage (use research-agent)
  or for library API docs (use docs-agent).
---

Personal KB at `~/projects/knowledge/`. 2028 docs in `~/.markstore/store.db`.
Search before answering any health, training, or enhancement question.

## Collections

| Collection | Docs | Use |
|------------|------|-----|
| `notes` | 1957 | Primary — all current notes |
| `literature` | 62 | Books/papers with frontmatter (title, authors, doi, type) |

---

## Search

### Basic

```bash
mks search "creatine performance" --limit 5 --snippets
mks search "creatine" --limit 5 --snippets --collection notes
```

### FTS5 query syntax

| Query | Meaning |
|-------|---------|
| `creatine` | Stemmed match (also matches "creatines") |
| `"creatine monohydrate"` | Exact phrase |
| `creatine -placebo` | Must contain creatine, must NOT contain placebo |
| `creat*` | Prefix — matches creatine, creatinine, etc. |
| `lex: query` | Explicit BM25 (same as default) |

```bash
mks search '"testosterone dose" -study' --limit 5 --snippets
mks search "sleep* recovery" --limit 5 --snippets --collection notes
```

### Filter by frontmatter

```bash
# Note: flag is --where-clause (not --where)
mks search "recovery" --where-clause "category=health" --limit 5 --snippets
mks search "RCT" --where-clause "type=RCT" --collection literature --limit 5 --snippets
mks search "paper" --where-clause "date>2024-01" --limit 5 --snippets
```

Supported fields: `collection`, `path`, `title`, or any YAML frontmatter key.
Operators: `=` `!=` `>` `<` `>=` `<=`

### Semantic search (requires Ollama)

```bash
# Only if Ollama is running — falls back to BM25 if not
mks embed                              # generate embeddings first (one-time)
mks search "vec: how does creatine increase strength" --limit 5
mks search "vec: recovery protocols after heavy training" --collection notes
```

Ollama not currently installed. To enable: `ollama pull nomic-embed-text` then `mks embed`.

### Intent prefix (disambiguation)

```bash
mks search 'intent: looking for notes on testosterone therapy, not general biology' \
  --limit 5 --snippets
```

---

## Retrieve

```bash
mks get <id>              # full document content (id from search results)
mks list --limit 20
mks list --collection notes --limit 50
mks stats
```

---

## Graph

```bash
# Build/rebuild graph (run after adding new docs)
mks graph build
mks graph build --force    # re-extract all

# Traverse from a concept
mks graph query "creatine"                    # BFS depth 2, 2000-token budget
mks graph query "testosterone" --depth 3 --budget 4000

# Find connections
mks graph path "creatine" "mTOR"              # shortest path between two nodes
mks graph neighbors "testosterone" --depth 2
mks graph backlinks "mTOR"                    # what links TO this node
mks graph god-nodes --limit 20               # most connected nodes in KB

# Overview
mks graph report
```

---

## Workflow for answering a question

```
1. search (2-3 queries)  →  2. get full docs  →  3. synthesize
```

```bash
# Multiple angles on same topic
mks search "sleep quality protocols" --limit 3 --snippets --collection notes
mks search "circadian rhythm optimization" --limit 3 --snippets --collection notes
mks search '"sleep debt" recovery' --limit 3 --snippets --collection notes

# Get the most relevant doc in full
mks get <id>
```

---

## Adding new content

```bash
# Single file
mks add ~/projects/knowledge/notes/health/enhancers/perform/new-compound.md --collection notes

# Directory
mks add ~/projects/knowledge/notes/pharmacology/ --collection notes

# Re-ingest changed files
mks add ~/projects/knowledge/notes/ --force --collection notes

# Web page
mks add https://examine.com/supplements/creatine/ --collection notes

# Watch for live updates
mks watch ~/projects/knowledge/notes/ --collection notes

# After adding — rebuild graph
mks graph build
```

### PDF → KB pipeline (with cnv)

```bash
cnv paper.pdf -f raw -o /tmp/out/
mks add /tmp/out/paper.md --collection literature
mks embed                    # if Ollama running
mks graph build
```

---

## Domain map

```
health/
  enhancers/perform/    # creatine, caffeine, beta-alanine, nitrates
  enhancers/recover/    # sleep aids, anti-inflammatories
  enhancers/think/      # nootropics, cognitive enhancers
  enhancers/feel/       # mood, wellbeing
  hormonal-management/  # TRT, SARMs, aromatase
  exercise/             # training protocols, hypertrophy, periodization
  nutrition/            # macros, timing, metabolic health
  lifestyle/            # sleep, stress, circadian
  specialised/          # specific performance protocols

pharmacology/           # drug mechanisms, PK/PD, dosing, toxicology
human-biology/          # anatomy, physiology, endocrinology, pathology
```

---

## When to search

Always search when the question involves:
- Supplements, ergogenics, nootropics, or drugs
- Training, exercise protocols, hypertrophy, strength
- Nutrition, recovery, sleep, circadian biology
- Hormones, endocrinology, TRT
- Dosing, timing, or protocols
- Any mechanism question in biology or physiology
