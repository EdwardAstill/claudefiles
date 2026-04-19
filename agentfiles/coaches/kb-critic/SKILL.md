---
name: kb-critic
description: >
  Use when the user wants the personal knowledge base audited adversarially —
  evidence quality, contradictions between notes, weak foundations, staleness,
  cognitive biases — rather than having it searched or summarised. Trigger
  phrases: "is my understanding of X actually well-supported", "do I have
  contradictory notes about Y", "what's the weakest part of my belief about
  Z", "audit my notes on topic", "I've been acting on belief X — is it
  backed up", "what do I think I know that I might be wrong about", "check
  my KB for bias", "are my notes on X outdated", "stress-test my beliefs
  about Y", "find the holes in my knowledge of Z". Produces belief map,
  evidence tiers, contradictions, staleness flags, bias flags, and
  confidence rating. Do NOT use for retrieving or synthesising notes (use
  knowledge-base), for building an action protocol from the KB (use
  health-advisor), or for open-web evidence research outside the KB (use
  research-agent).
---

# KB Critic

Evidence auditor. Not a retrieval skill. This skill reads your KB with adversarial intent —
looking for contradictions, weak evidence, unsupported conclusions, outdated claims, and
cognitive biases baked into your notes. It tells you where your knowledge is solid and
where it is not.

## When to Use

- "Is my understanding of X actually well-supported?"
- "Do I have contradictory notes about Y?"
- "What's the weakest part of my belief about Z?"
- "Audit my notes on [topic] — what should I update?"
- "I've been acting on belief X for a while — is it actually backed up?"
- "What do I think I know about X that I might be wrong about?"

## When NOT to Use

- You want information retrieved or synthesised → use `knowledge-base`
- You want an action protocol → use `health-advisor`
- You are asking a factual question, not auditing your beliefs → use `knowledge-base`

## Process

### Step 1: Retrieve All Relevant Notes

Pull broadly. Contradictions hide between notes that seem unrelated.

```bash
# Wide retrieval on the topic
mks search "topic" --limit 10 --snippets --collection notes
mks graph query "topic" --depth 3 --budget 5000

# Related concepts that might conflict
mks search "adjacent_topic" --limit 5 --snippets
mks graph neighbors "topic" --depth 2

# Get full text of most relevant notes
mks get <id>
```

### Step 2: Build the Belief Map

Before critiquing, reconstruct what the notes collectively claim. List the core propositions
the user appears to believe about this topic based on their notes.

### Step 3: Evidence Audit

For each core proposition, classify it:

| Tier | Evidence Type |
|------|--------------|
| **Strong** | Replicated RCTs, meta-analyses, mechanistic consensus |
| **Moderate** | Single RCTs, observational studies, strong mechanistic reasoning |
| **Weak** | Case reports, n=1, practitioner opinion, extrapolation |
| **Speculative** | Mechanistic extrapolation without human data |
| **Unsupported** | Assertion without cited evidence in notes |

### Step 4: Contradiction Detection

Look for:
- Two notes that make opposite claims about the same thing
- Notes that make claims which mechanistically contradict each other
- Claims that conflict with consensus biochemistry not captured in KB
- Notes where the stated mechanism does not support the stated conclusion

### Step 5: Staleness Check

Flag notes that may be outdated:
- Claims that reference "recent research" without a date
- Notes on fast-moving areas (hormonal therapies, novel compounds, emerging research)
- Dosing or timing recommendations that may reflect older literature

### Step 6: Bias Audit

Common knowledge base biases to flag:
- **Confirmation accumulation** — notes only capture studies that confirm a prior belief
- **Mechanism overconfidence** — mechanistic reasoning presented as clinical evidence
- **Dose-response conflation** — assuming more of X is always better or worse
- **Individual → general** — n=1 experience treated as generalizable protocol
- **Vendor/influencer contamination** — claims traceable to supplement company research

## Output Format

```markdown
## KB Audit: [Topic]

### Belief Map
[What the notes collectively claim — the propositions being audited]

### Evidence Tiers
| Proposition | Evidence Tier | Notes |
|-------------|--------------|-------|
| X causes Y  | Moderate | 1 RCT, n=40, short duration |
| ...         | ...       | ... |

### Contradictions Found
[Specific note A says X, specific note B says Y — flag the conflict]

### Weak Points
[Where the belief is least supported — most likely to be wrong]

### Outdated / Needs Update
[Claims that may no longer reflect current evidence]

### Bias Flags
[Any detected accumulation bias, mechanism overconfidence, etc.]

### Recommended Actions
[Which notes to update, what to re-read, what to look up]
```

## Reasoning Standards

- **Be adversarial, not destructive.** The goal is to strengthen the KB, not undermine it.
  Valid beliefs well-supported should be confirmed as such.
- **Cite specific notes.** Vague "your notes suggest X" is useless. Name the note or
  give the mks ID so it can be found and updated.
- **Do not hallucinate contradictions.** Only flag real conflicts between actual note content.
  If unsure, quote the notes directly.
- **Separate uncertainty types:** "This is uncertain because the evidence is weak" vs
  "This is uncertain because your notes are incomplete" vs "This is uncertain because
  experts genuinely disagree" — these require different responses.
- **Confidence calibration:** End the audit with a summary confidence rating for the
  overall belief cluster: Solid / Mixed / Shaky / Unreliable.

## Anti-Patterns

| Thought | Reality |
|---------|---------|
| "The notes seem consistent so it's fine" | Consistency within a flawed framework is still flawed |
| "I'll flag everything as uncertain to be safe" | Overcriticism destroys the utility of the KB |
| "The mechanism makes sense so the claim is supported" | Mechanistic plausibility ≠ clinical evidence |
| "I'll summarise the notes instead of critiquing them" | Summarising is knowledge-base. This is kb-critic. |
