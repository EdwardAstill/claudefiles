# Coaches

The `coaches/` region contains skills that apply domain reasoning to produce plans,
protocols, and critical evaluations grounded in the personal knowledge base.

## Why coaches exist

The `knowledge-base` skill retrieves and summarises. That is useful, but it is not the
same as coaching. A coach:

- Synthesises across domains (diet + training + biochemistry together)
- Produces actionable output — a protocol you can follow, not a summary
- Applies adversarial reasoning — stress-testing beliefs, finding contradictions

These are different cognitive modes. A separate region makes the distinction explicit
and ensures the right mode is triggered.

## Skill overview

| Skill | Mode | Use when |
|-------|------|----------|
| `knowledge-base` | Retrieval | "What do I know about X?" |
| `health-advisor` | Coaching | "What should I do about X?" |
| `kb-critic` | Critique | "Is what I believe about X actually right?" |

## health-advisor

Integrated health coach covering nutrition, training, supplementation, hormones, sleep,
recovery, and drug/supplement interactions.

**Trigger phrases:**
- "Build me a protocol for..."
- "How should I structure my diet / training for..."
- "I'm taking X — what should I know?"
- "Optimise my recovery / sleep / training given..."

**What it does:**

1. Searches the KB across all relevant domains (3–5 targeted queries)
2. Identifies what the KB covers vs where it is sparse
3. Synthesises across nutrition, training, biochemistry, supplementation, lifestyle
4. Outputs a numbered protocol with mechanism, watch points, and confidence rating

**Output structure:**

```
Protocol: [Goal]
Context Assumed
Recommendation (numbered steps, specific doses/timings)
Mechanism (why this works)
Key Interactions / Watch Points
KB Sources Used
Confidence
```

**Key constraint:** KB notes override general knowledge. If a KB note conflicts with
general biochemistry, the conflict is flagged — not silently resolved.

---

## kb-critic

Adversarial evidence auditor for the personal knowledge base. Reads KB content with
critical intent — looking for contradictions, weak evidence, unsupported conclusions,
outdated claims, and accumulated bias.

**Trigger phrases:**
- "Audit my notes on..."
- "Is my understanding of X actually well-supported?"
- "Do I have contradictory notes about...?"
- "What's the weakest part of my belief about...?"
- "I've been acting on X — is it actually backed by evidence?"

**What it does:**

1. Retrieves all relevant notes broadly (graph traversal + search)
2. Reconstructs the belief map — what the notes collectively claim
3. Classifies each core proposition by evidence tier
4. Detects contradictions between notes
5. Flags staleness and accumulated bias
6. Outputs recommendations for which notes to update

**Evidence tiers:**

| Tier | Evidence Type |
|------|--------------|
| Strong | Replicated RCTs, meta-analyses, mechanistic consensus |
| Moderate | Single RCTs, observational studies, strong mechanistic reasoning |
| Weak | Case reports, n=1, practitioner opinion, extrapolation |
| Speculative | Mechanistic extrapolation without human data |
| Unsupported | Assertion without cited evidence in notes |

**Output structure:**

```
Belief Map (what the notes collectively claim)
Evidence Tiers (table: proposition, tier, notes)
Contradictions Found
Weak Points
Outdated / Needs Update
Bias Flags
Recommended Actions
```

**Ends with an overall confidence rating:** Solid / Mixed / Shaky / Unreliable

---

## Typical workflows

### Goal-first: build a protocol

```
health-advisor → produces protocol
     ↓ (optional)
kb-critic → audit the beliefs the protocol rests on
     ↓
readrun → update any notes flagged as weak or outdated
```

### Belief-first: audit then act

```
kb-critic → audit a topic area
     ↓
knowledge-base → retrieve corrected understanding
     ↓
health-advisor → re-build protocol on stronger foundations
```

### Routine: periodic KB audit

```
kb-critic on a domain (e.g. "audit my nutrition notes")
     ↓
readrun → update flagged notes
     ↓
mks graph build → rebuild graph with updated content
```

---

## Relationship to knowledge-base

`knowledge-base` is a retrieval skill in the `research/` region. It is the data layer.
`health-advisor` and `kb-critic` are reasoning layers that build on top of it.

You can use `knowledge-base` directly for factual questions. Use the coaches when
you need synthesis, action, or critique.
