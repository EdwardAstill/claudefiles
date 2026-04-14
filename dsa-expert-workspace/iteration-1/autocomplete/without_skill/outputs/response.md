# Autocomplete Over 100k Strings in Under 50ms

## Recommended Approach: Trie (Prefix Tree)

A **trie** is the textbook-correct data structure for prefix-based autocomplete and will comfortably hit your <50ms target even on 100k strings. Here is why, along with alternatives and practical guidance.

---

## Why a Trie?

A trie stores strings character-by-character along shared prefixes. For autocomplete the key operations are:

| Operation | Time Complexity | Notes |
|---|---|---|
| Insert a string | O(L) | L = length of the string |
| Lookup / prefix search | O(P + K) | P = prefix length, K = number of results returned |
| Build the entire trie | O(N * L_avg) | One-time cost at startup |

For a prefix of length 5 against 100k strings, a lookup walks 5 nodes then collects the top-K matches. This is typically **sub-millisecond** -- well within your 50ms budget.

### Basic Trie Node (Python)

```python
class TrieNode:
    __slots__ = ('children', 'is_end', 'word')

    def __init__(self):
        self.children = {}   # char -> TrieNode
        self.is_end = False
        self.word = None     # store full word at terminal nodes

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.word = word

    def autocomplete(self, prefix: str, limit: int = 10) -> list[str]:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        # DFS/BFS to collect completions
        results = []
        stack = [node]
        while stack and len(results) < limit:
            current = stack.pop()
            if current.is_end:
                results.append(current.word)
            for child in current.children.values():
                stack.append(child)
        return results
```

### Memory Estimate

For 100k English strings averaging 10 characters, a trie uses roughly **5-20 MB** depending on alphabet density and implementation language. This fits comfortably in memory.

---

## Ranking Results: Weighted / Scored Trie

Raw prefix matching returns results in arbitrary order. In practice you want to rank by popularity, frequency, or relevance. Two approaches:

### 1. Store a score at each terminal node and maintain a heap during collection

```python
import heapq

def autocomplete_ranked(self, prefix: str, limit: int = 10):
    node = self._walk(prefix)
    if not node:
        return []
    heap = []  # min-heap of (score, word)
    stack = [node]
    while stack:
        current = stack.pop()
        if current.is_end:
            if len(heap) < limit:
                heapq.heappush(heap, (current.score, current.word))
            elif current.score > heap[0][0]:
                heapq.heapreplace(heap, (current.score, current.word))
        for child in current.children.values():
            stack.append(child)
    return [word for _, word in sorted(heap, reverse=True)]
```

### 2. Pre-compute top-K at each node (faster queries, more memory)

Store the top-K completions at every internal node during build time. Queries become O(P) -- just walk the prefix and return the cached list. This trades ~2-5x more memory for near-instant lookups.

---

## Alternatives and When to Use Them

### Sorted Array + Binary Search

- **How:** Sort all 100k strings lexicographically. Use binary search to find the range matching the prefix.
- **Time:** O(P * log N) per query.
- **Pros:** Dead simple, cache-friendly, minimal memory overhead.
- **Cons:** Slightly slower than a trie for very short prefixes; harder to extend with ranking.
- **When to use:** You want maximum simplicity and the dataset is static.

```python
import bisect

words.sort()

def autocomplete_bisect(prefix, words, limit=10):
    lo = bisect.bisect_left(words, prefix)
    results = []
    for i in range(lo, min(lo + limit, len(words))):
        if words[i].startswith(prefix):
            results.append(words[i])
        else:
            break
    return results
```

### Ternary Search Tree (TST)

- More memory-efficient than a standard trie (one node per character vs. one per alphabet slot).
- Similar O(P + K) lookup.
- **When to use:** Memory is tight and you need trie-like behavior.

### Finite State Transducer (FST) -- e.g., Lucene / `fst` crate in Rust

- Compresses the trie into a minimal automaton. Extremely memory efficient.
- Used by Elasticsearch/Lucene internally for suggest/completion.
- **When to use:** Millions of strings, or you need the data structure to be serializable to disk.

### Inverted Index with n-grams (for fuzzy / substring matching)

- If you need to match **anywhere** in the string (not just prefix), build an inverted index of character n-grams (trigrams are typical).
- **When to use:** Substring search, typo tolerance, or "contains" matching.

---

## Practical Architecture Recommendations

### Frontend (browser-based autocomplete)

1. **Debounce input** to 100-150ms so you are not firing on every keystroke.
2. **Ship a pre-built trie or sorted array** as a static JSON/binary asset if the dataset is stable and small enough (100k short strings is roughly 1-3 MB gzipped).
3. **Web Worker:** Run the search in a Web Worker to avoid blocking the main thread.
4. In JavaScript, a simple sorted array with binary search is often the fastest option because V8 optimizes flat arrays aggressively and the trie's pointer-chasing is cache-unfriendly.

### Backend (API-based autocomplete)

1. **In-memory trie or sorted array** in your application server. At 100k strings this is trivially small.
2. **Redis** with `ZRANGEBYLEX` gives you sorted-set prefix queries with zero custom code.
3. **Elasticsearch completion suggester** if you already run ES -- it uses an FST internally and handles ranking, fuzzy matching, and sharding.

### Hybrid

For the best UX, prefetch the most common completions to the client and fall back to the server for the long tail:

```
keystroke -> check local cache/trie -> if miss, fetch from server
```

---

## Performance Budget Breakdown (for 100k strings)

| Phase | Estimated Time |
|---|---|
| Trie build (one-time) | 50-200ms |
| Prefix lookup (per keystroke) | 0.01-1ms |
| Collecting top-10 results | 0.1-5ms |
| JSON serialization + network (if server) | 5-30ms |
| **Total per keystroke** | **< 35ms typical** |

You are well within your 50ms budget.

---

## Summary

| Approach | Best For | Query Time | Complexity |
|---|---|---|---|
| **Trie** | Prefix search with ranking | O(P + K) | Moderate |
| **Sorted array + bisect** | Simple static prefix search | O(P log N) | Low |
| **Pre-computed top-K trie** | Fastest possible queries | O(P) | Higher build cost |
| **Redis ZRANGEBYLEX** | Server-side, no custom DS | O(log N + K) | Low (ops cost) |
| **Elasticsearch completion** | Full-featured suggest | O(P) (FST) | Highest ops cost |

**Start with a trie or sorted array in memory.** Either will be well under 50ms for 100k strings. Add pre-computed top-K or move to Redis/ES only if your requirements grow (fuzzy matching, millions of entries, distributed serving).
