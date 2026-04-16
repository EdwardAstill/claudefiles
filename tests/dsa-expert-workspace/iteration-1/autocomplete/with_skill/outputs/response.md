# Autocomplete Over ~100k Strings in <50ms

## Step 1: Constraint Summary

**Operations needed:**
- **Prefix lookup** -- given a partial string typed by the user, return all (or top-N) strings that start with that prefix
- **Read-heavy** -- the dictionary of ~100k strings is relatively static; lookups happen on every keystroke
- **Insert/delete** -- rare (only when the dictionary updates), not on the hot path

**Frequency and size characteristics:**
- ~100k candidate strings (modest size -- fits comfortably in memory)
- Lookups triggered on every keystroke -- must complete in <50ms (ideally <10ms to feel truly instant)
- Read-to-write ratio is extremely high (thousands of reads per write at most)

**Hard constraints:**
- Latency: <50ms per query, hard requirement
- Results should be prefix-ordered or ranked (e.g., by popularity/frequency)
- Memory budget: not critical at 100k strings -- a few tens of MB is fine
- No thread-safety requirement stated (single-user typing)

**What's already in place:**
- Not specified. Assuming a greenfield autocomplete component.

---

## Step 2: Trade-off Analysis

Three viable candidates for this workload:

| Criterion | Trie | Sorted Array + Binary Search | Hash Map (prefix buckets) |
|---|---|---|---|
| Prefix lookup | O(m + k) where m = prefix length, k = results | O(m log n) to find start, O(k) to scan results | O(m) average for exact bucket, but must pre-compute all prefix buckets |
| Insert | O(m) | O(n) (shift elements) | O(m * L) for all prefixes of a word of length L |
| Delete | O(m) | O(n) (shift elements) | O(m * L) |
| Memory | Higher -- pointer overhead per node (can be 5-20x the raw string data) | Low -- just the sorted strings | High -- stores every prefix as a key with its result list |
| Cache behavior | Poor -- pointer chasing across heap | Excellent -- contiguous memory, binary search is cache-friendly | Moderate -- hash table itself is cache-friendly, but value lists are scattered |
| Ordered iteration | Natural (DFS gives lexicographic order) | Natural (already sorted) | Not inherently ordered; must sort each bucket |
| Implementation complexity | Moderate | Simple | Simple to build, but wasteful and awkward to maintain |
| Supports fuzzy/typo-tolerant matching | Extensible (Levenshtein automata over trie) | Difficult | Difficult |

### Recommendation

**Use a Trie** for this problem. Here is why:

1. **Prefix matching is the trie's defining strength.** You descend to the node representing the user's input and collect descendants -- no wasted comparisons, no binary search overhead.
2. **At 100k strings, the trie fits in memory easily.** The pointer overhead that makes tries expensive at billions of entries is negligible here.
3. **Future extensibility.** If you later need fuzzy matching (tolerating typos), a trie extends naturally to Levenshtein automata or BK-tree hybrids. A sorted array does not.
4. **Practical latency.** Traversing a trie for a 10-character prefix is 10 pointer hops. Collecting the top-k results from there is bounded by k. This will be well under 1ms on modern hardware for 100k strings, let alone 50ms.

**When would sorted array + binary search win instead?** If your dictionary is truly static, memory is very tight, and you never need fuzzy matching, a sorted array is simpler and more cache-friendly. For 100k strings, binary search finds the prefix start in ~17 comparisons, then you scan forward. This is also well under 50ms. Choose this if you want minimal implementation effort and have no plans for fuzzy/ranked autocomplete.

**Avoid the hash map approach.** Pre-computing all prefix buckets wastes memory (every prefix of every string becomes a key) and is painful to maintain on updates. It offers O(1) lookup per bucket but the trade-off is not worth it.

---

## Step 3: Solution Design

### High-Level Approach

**Trie with bounded DFS collection.** Build a trie from the dictionary. On each keystroke, walk the trie to the node matching the current prefix, then collect up to K results via DFS from that node. Optionally, store a popularity/frequency score at each leaf and use a bounded priority queue during collection to return the top-K most relevant results.

### Invariants

1. **Every leaf node corresponds to exactly one complete string in the dictionary.** Internal nodes may or may not be end-of-word markers.
2. **Children of a node are keyed by character.** If children are stored in a sorted structure (array of 26 for lowercase English, or a small sorted map), DFS yields results in lexicographic order for free.
3. **The max results parameter K bounds the DFS.** Once K results are collected, traversal stops. This guarantees the query time is O(m + K) regardless of how many strings share the prefix.

### Pseudocode

```
structure TrieNode:
    children: map<char, TrieNode>
    is_end_of_word: bool
    word: string or null       // store the full word at leaf for easy retrieval
    frequency: int             // optional: for ranking results

function build_trie(words):
    root = new TrieNode()
    for word in words:
        node = root
        for char in word:
            if char not in node.children:
                node.children[char] = new TrieNode()
            node = node.children[char]
        node.is_end_of_word = true
        node.word = word
        node.frequency = get_frequency(word)  // optional
    return root

function autocomplete(root, prefix, max_results):
    // Phase 1: Walk to the prefix node
    node = root
    for char in prefix:
        if char not in node.children:
            return []          // no matches
        node = node.children[char]

    // Phase 2: Collect up to max_results completions via DFS
    results = []
    collect(node, results, max_results)
    return results

function collect(node, results, max_results):
    if len(results) >= max_results:
        return

    if node.is_end_of_word:
        results.append(node.word)

    for char in sorted(node.children.keys()):   // sorted gives lexicographic order
        collect(node.children[char], results, max_results)
        if len(results) >= max_results:
            return
```

**Variant -- top-K by frequency:** Replace the simple list with a min-heap of size K. During DFS, push every leaf's (frequency, word) pair onto the heap; if the heap exceeds K, pop the minimum. At the end, the heap contains the K highest-frequency completions.

```
function autocomplete_ranked(root, prefix, K):
    node = root
    for char in prefix:
        if char not in node.children:
            return []
        node = node.children[char]

    min_heap = new MinHeap()    // keyed by frequency
    collect_ranked(node, min_heap, K)
    return min_heap.drain_sorted_descending()

function collect_ranked(node, heap, K):
    if node.is_end_of_word:
        if heap.size() < K:
            heap.push((node.frequency, node.word))
        else if node.frequency > heap.peek().frequency:
            heap.pop()
            heap.push((node.frequency, node.word))

    for char in node.children.keys():
        collect_ranked(node.children[char], heap, K)
```

### Complexity Analysis

**Build time:** O(N * L) where N = number of strings, L = average string length. Each string requires L node traversals/creations. For 100k strings of average length 15, this is ~1.5M operations -- takes a few milliseconds.

**Query time:** O(m + K) where m = prefix length, K = max results returned.
- Phase 1 (prefix walk): exactly m pointer hops.
- Phase 2 (DFS collection): visits at most K leaf nodes. In the worst case, it visits some internal nodes too, but the early termination at K results bounds the work. For a ranked variant with a full DFS subtree scan, worst case is O(S) where S is the subtree size, but this only matters if the prefix is very short (e.g., a single character). Mitigate by requiring a minimum prefix length of 2-3 characters.

**Space:** O(N * L) for the trie nodes in the worst case (no shared prefixes). In practice, shared prefixes compress this significantly. For 100k English strings, expect 300k-1M nodes, each consuming ~50-100 bytes (depending on child map implementation), so roughly 15-100 MB.

---

## Step 4: Edge Cases and Correctness

| Edge case | Risk | Mitigation |
|---|---|---|
| **Empty prefix** | Returns entire dictionary -- DFS traverses all 100k entries | Require minimum prefix length (2-3 chars) or return nothing for empty input |
| **Single character prefix** | Large subtree, potentially thousands of matches | Enforce max_results (K) and terminate DFS early |
| **No matches** | Prefix walk fails at some character | Return empty list (handled by the `char not in node.children` check) |
| **Exact match only, no extensions** | Prefix is itself a complete word with no children | Works correctly -- the prefix node is a leaf with `is_end_of_word = true`, returned as sole result |
| **Case sensitivity** | "App" vs "app" treated as different prefixes | Normalize input to lowercase before insertion and query |
| **Unicode / special characters** | Characters outside ASCII break fixed-array child storage | Use a hash map or sorted map for children instead of a fixed-size array |
| **Very long strings** | Excessive trie depth | Not a practical concern at typical string lengths (<100 chars); trie depth = string length |
| **Duplicate strings in dictionary** | Inserted twice, but trie naturally deduplicates (same path) | No issue -- `is_end_of_word` is idempotent. If frequency tracking, add to the count |
| **Concurrent updates** | User typing while dictionary is being rebuilt | Use double-buffering: build new trie in background, swap atomically |

---

## Step 5: Language-Specific Handoff Notes

### Python
- Use a `dict` for children (hash map per node). For lower memory, consider the `marisa-trie` or `pygtrie` library instead of hand-rolling.
- `heapq` is a min-heap: works directly for the top-K-by-frequency variant (push negated frequencies for a max-heap, or use the min-heap approach described above).
- For the simple case, `bisect.bisect_left` on a sorted list of strings is a strong alternative -- the entire implementation is ~5 lines and will be fast enough at 100k strings.
- `sortedcontainers.SortedList` gives O(log n) insertion and O(log n + k) prefix range queries via `irange()`.

### Rust
- `BTreeMap<char, Box<TrieNode>>` for ordered children. Alternatively, use a `Vec<(char, TrieNode)>` sorted by char for better cache locality at small alphabet sizes.
- Consider the `trie-rs` or `fst` crate. The `fst` crate (finite state transducer) is extremely memory-efficient and fast for static dictionaries -- ideal for this use case if the dictionary is built once.
- Ownership: each `TrieNode` owns its children. Use `Box` or arena allocation (`typed-arena`) to avoid lifetime complexity.
- For the sorted array approach: `Vec<String>` with `.binary_search()` and `.partition_point()` is idiomatic and very fast.

### TypeScript
- No built-in trie or sorted set. Hand-roll a trie with `Map<string, TrieNode>` for children, or use a library like `trie-search` or `mnemonist/trie`.
- For the sorted array approach: `Array.prototype.sort()` on build, then a custom binary search function (no built-in `bisect`).
- If running in the browser, the 50ms budget includes rendering. Consider using `requestAnimationFrame` or debouncing keystrokes (100-150ms) to reduce query frequency, making even a slower approach viable.
- Web Workers can offload trie queries off the main thread to avoid blocking the UI.
