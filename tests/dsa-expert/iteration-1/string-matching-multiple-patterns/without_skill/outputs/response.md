# Multi-Pattern Content Moderation

This is a classic multi-pattern string matching problem. There are three main approaches.

## 1. Aho-Corasick Automaton

Build a trie of all 50K patterns, then add failure links (like KMP generalized to multiple patterns). Scan the input text once in O(n + m + z) where n = text length, m = total pattern length, z = number of matches.

- Preprocessing: O(m · |alphabet|), typically tens of ms for 50K patterns.
- Query: O(n + z) per message — one pass through the text.
- Memory: 2–5 MB for a dictionary of this size (depends on alphabet and trie implementation).

This is the gold standard for this kind of problem.

## 2. Rabin-Karp with Multiple Lengths

Compute rolling hashes. For each distinct pattern length L (here 1-5 words, so maybe 5-20 distinct lengths), slide a window of size L, compute the hash, check against a HashSet of pattern hashes for that length.

- Query: O(n · k) where k is the number of distinct lengths.
- Preprocessing: O(m).
- Memory: O(m) for hash sets.

Simpler to implement than AC but slower.

## 3. Bloom Filter Prefilter

For each distinct length, maintain a Bloom filter of all L-length patterns. Slide a window, check Bloom first (fast reject), on a possible hit verify with the exact HashSet.

- Query: average close to O(n), worst O(n · k).
- Preprocessing: O(m).
- Memory: O(m) + bloom filter bits.

Useful when most substrings are not matches; otherwise no better than Rabin-Karp.

## Recommendation

Use Aho-Corasick. For 10K messages/sec with 500-char average, you're processing about 5M chars/sec, which is trivial for AC on a single core. Preprocessing 50K patterns once takes around 100ms.

## Case-insensitive Matching

Lowercase both patterns and text. For non-ASCII, use locale-aware lowercasing.

## Unicode Normalization

Apply NFC normalization to both the patterns (at build time) and the text (at scan time) before building or scanning. Consider NFKC or casefold for more aggressive canonicalization.

Homoglyphs (Cyrillic 'a' vs Latin 'a') may need a confusables folder.

## Dynamic Updates

- Rebuild the automaton on dictionary change. At 50K patterns rebuilding in ~100ms, this is fine for infrequent updates.
- Or maintain a small delta trie for recent additions and merge periodically.
- Incremental Aho-Corasick exists but is complex.

## Edge Cases

- Overlapping patterns — AC handles naturally via the output chain.
- Patterns that are prefixes of others — both terminals in the trie, both reported.
- Empty pattern — reject.
- Pattern longer than text — no problem.
- UTF-8 sliding windows (for Rabin-Karp) — must respect codepoint boundaries.
- Homoglyph attacks.

## Libraries

- Python: pyahocorasick.
- Rust: aho-corasick (BurntSushi).
- Java: org.ahocorasick:ahocorasick.
- Go: cloudflare/ahocorasick.
- For very large dictionaries consider Intel Hyperscan.
