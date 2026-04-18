# Multi-Pattern Content Moderation Matcher

## Step 1 — Constraint Summary

**Operations:** scan incoming text for any occurrence of ~50,000 banned phrases.
**Message:** avg 500 chars, worst 10 KB.
**Dictionary:** 50,000 phrases, 1 to 5 words each (≈ 5–50 chars).
**Throughput:** 10,000 msg/sec; sub-ms per message latency.
**Cross-cutting:** case-insensitive matching, Unicode normalization, dynamic dictionary updates.

**Implications:**
- Per-message budget: < 1 ms for ≤ 10 KB ⇒ need algorithm near ~10 MB/s per core at worst case (easily achievable).
- Aggregate: 10^4 × 500 = 5 × 10^6 chars/sec average; well within single-core reach of any streaming matcher.
- "Dynamic updates" is the real architectural lever — rebuild frequency vs hot-swap.

## Step 2 — Candidate Algorithms

| Criterion | Aho–Corasick automaton | Rabin–Karp, multi-length | Bloom filter prefilter + hashset | Commentz-Walter / WM |
|-----------|-------------------------|---------------------------|------------------------------------|-----------------------|
| Preprocessing time | O(Σ‖p‖ · |alphabet|) — ≈ tens of ms for 50K patterns | O(Σ‖p‖) | O(Σ‖p‖) | O(Σ‖p‖) |
| Query time | **O(n + z)** single pass | O(n · k) where k = #distinct lengths | average near O(n), worst O(n · k) | O(n / min_pattern_len) average, O(n · k) worst |
| Memory | 2–5 MB for 50K patterns (trie + goto/failure) | O(Σ‖p‖) hash sets | Bloom ≈ 10 bits/pattern per length + hash set | similar to AC |
| Match semantics | finds **all** occurrences, including overlaps | reports each occurrence per length | exact on hit | all |
| Incremental update | costly without a dynamic AC variant | easy: add to hashset | easy: add to Bloom + set | costly |
| Implementation complexity | moderate (textbook, libraries exist) | simple | moderate | moderate |

**Recommendation: Aho–Corasick.** Single-pass linear-time scan makes per-message latency essentially `length / memory_bandwidth` (tens of microseconds for 500 chars). The other approaches only win when the query budget exceeds preprocessing cost *and* dictionary churn is extreme.

Use **two-tier Aho–Corasick**: main automaton rebuilt every minute or on N additions, plus a small "hot" automaton holding recent additions; scan both in the same pass (cost: 2×, still sub-ms). Merge during quiet periods.

## Step 3 — Design (Aho–Corasick)

### Data Structures
```
TrieNode {
    children:    map<char, TrieNode>     # or array[σ] if fixed alphabet
    failure:     *TrieNode                # LPS-style fallback
    output:      list<PatternId>          # patterns ending here + via failure chain
    depth:       int                      # pattern length if terminal
}
```

### Invariants
- **I1.** `failure[root] = root`. For every non-root node `v` with parent `u` and edge `c`, `failure[v]` is the longest proper suffix of the path from root to `v` that exists in the trie (BFS order ensures this is computable from parent-level failure).
- **I2.** `output[v]` contains all pattern IDs whose end is a suffix of the path to `v` — computed once during BFS as `output[v] = terminal_patterns(v) ∪ output[failure[v]]`.
- **I3.** During scan, the automaton is in some node `state`; on input char `c`, we follow `children[c]` if present, else `state = failure[state]` repeatedly, else `state = root`. This gives amortized O(1) per char.

### Pseudocode

```
function build(patterns: list<string>):
    root = new TrieNode()
    # 1. Insert all patterns into the trie
    for pid, p in enumerate(patterns):
        node = root
        for c in normalize(p):
            node = node.children.setdefault(c, new TrieNode())
        node.output.append(pid)
        node.depth = len(p)

    # 2. BFS to set failure links
    queue = deque()
    for c, child in root.children:
        child.failure = root
        queue.push(child)
    while queue not empty:
        u = queue.popleft()
        for c, v in u.children:
            # find failure target for v
            f = u.failure
            while f != root and c not in f.children:
                f = f.failure
            v.failure = f.children.get(c, root) if f.children.get(c) != v else root
            v.output.extend(v.failure.output)   # I2
            queue.push(v)
    return root

function scan(root, text) -> list<(position, pattern_id)>:
    matches = []
    state = root
    for i, c in enumerate(normalize(text)):
        while state != root and c not in state.children:
            state = state.failure
        state = state.children.get(c, root)
        for pid in state.output:
            matches.append((i - pattern_len(pid) + 1, pid))
    return matches

function normalize(s):
    s = unicode_normalize(s, "NFC")
    s = s.lower()            # locale-aware lowercase if multilingual
    return s
```

### Complexity Proof
- **Build:** total children explored during failure-link BFS is O(Σ‖p‖); each failure hop is amortized O(1) because state depth strictly decreases on each hop and increases by 1 per character. So build is O(Σ‖p‖) with a small constant and a `|alphabet|` factor if arrays are used for children.
- **Scan:** the amortization argument: each character advances depth by at most 1; each failure hop decreases depth by ≥ 1. Total depth movements ≤ 2n. So `O(n + z)` where z = number of matches.
- **Memory:** ≈ Σ‖p‖ × (child-map overhead + failure pointer + output list). With a dictionary of 50K phrases averaging 20 chars = 1M total chars, and hashmap-based children, expect ~20–40 bytes/node → 20–40 MB. With array-based children on a small alphabet (lowercased ASCII + common punctuation) and pooled nodes, can be compressed to 2–5 MB. Double-array trie (DAT-AC) achieves ~2 MB and better cache behavior.

### Per-message latency back-of-envelope
10 KB max / ~1 GB/s scan speed ≈ 10 µs per worst-case message. Average 500-char message ≈ 0.5 µs. Well inside the sub-ms budget.

## Step 4 — Cross-cutting Concerns + Edge Cases

### Case-insensitive matching
- Canonical: lowercase both patterns *during build* and text *during scan*. ASCII fast path via a 256-byte LUT; Unicode requires `toLowerCase` with locale awareness (e.g., Turkish dotted/dotless I is a subtle bug source).
- Faster alternative: build the automaton with all-lowercase patterns and force the scan through a lowercasing iterator — zero copy if you scan char-by-char.

### Unicode normalization
- Apply **NFC** to both sides at build and scan time. NFKC if you want compatibility folding (⅔ → 2⁄3).
- Combining marks matter: "café" can be `c a f é` (NFC) or `c a f e + ◌́` (NFD). Without normalization, patterns won't match user-typed input.
- Consider **NFKC + casefold + strip combining marks** for moderation (catches homoglyph tricks): normalize to a canonical form before building and scanning. Trade off: you may over-match.
- Homoglyph attacks (Cyrillic 'а' U+0430 vs Latin 'a' U+0061): use a confusables folder (Unicode's `confusables.txt` or ICU `UConfusable`).

### Dynamic dictionary updates
Three options, in order of operational preference:
1. **Periodic rebuild + two-tier:** main AC (stable) + hot AC (recent additions, rebuilt every few seconds). Scan both. Merge hourly. 50K patterns rebuild in tens of ms; this is almost always fine.
2. **Hot-swap with versioning:** build new automaton in the background, atomically swap pointer under RCU or a read-write lock. Cheap for readers.
3. **Incremental AC (Meyer 1985 / dynamic AC):** supports single-pattern insert/delete on the fly, but implementation is complex and rarely worth it for 50K-scale dictionaries that rebuild in ms.

### Sharding / throughput
- 10K msg/s is trivial for one core; use a thread pool of size = cores, share the automaton read-only.
- Pin threads, use NUMA-aware allocation for very large dictionaries.

### Edge Cases
- **Overlapping patterns** ("abc" and "bcd" in "abcd"): Aho–Corasick naturally reports both via the `output` chain — that's what the failure-link output extension (I2) is for.
- **Pattern is prefix of another** ("car" and "carpet"): both terminals exist in the trie; the longer one's scan naturally hits the shorter's output set.
- **Empty pattern:** reject at build time; it would match everywhere.
- **Pattern longer than text:** harmless; the trie walk simply never reaches that depth.
- **UTF-8 multi-byte sliding window (for Rabin–Karp):** always scan at codepoint boundaries; byte-level windows can hit partial codepoints. AC avoids this since you scan codepoints directly.
- **Punctuation/whitespace normalization:** "f**k" vs "fuck" — decide if you want to canonicalize leet/obfuscation (a separate `canonicalize` step before scanning).
- **Very short patterns** (single common words): cause many trivial matches and inflate z; consider filtering or weighting by confidence.

## Step 5 — Language Handoff

- **Python:** `pyahocorasick` (C extension, very fast), or `ahocorasick-rs` via PyO3. Python's built-in `re` with 50K alternatives would be far slower (regex engine builds a worse NFA).
- **Rust:** `aho-corasick` crate by BurntSushi — SIMD-accelerated, battle-tested in ripgrep; supports case-insensitive out of the box (`AhoCorasickBuilder::ascii_case_insensitive`). Unicode-aware variant available.
- **Java:** `org.ahocorasick:ahocorasick` or Apache Commons Text; alternatively `DFA` via Brics.
- **Go:** `github.com/cloudflare/ahocorasick` or `github.com/anknown/ahocorasick`.
- **C++:** Yu's DATA (double-array AC), or write against `std::u32string` for Unicode safety. Consider `hyperscan` (Intel) which beats pure AC for very large dictionaries via regex compilation + SIMD, with a more complex API.

For Unicode normalization: Python `unicodedata.normalize`, Rust `unicode-normalization`, Java `java.text.Normalizer`, Go `golang.org/x/text/unicode/norm`, C++ ICU.

If the dictionary grows toward 500K+ and messages stay short, switch from AC to **Hyperscan** — it trades more preprocessing for SIMD-vectorized scanning that scales better with both dictionary and text size.
