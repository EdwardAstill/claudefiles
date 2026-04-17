---
name: dsa-expert
description: >
  Data structures and algorithms expert. Use for choosing between data structures
  (hash map vs trie, BTree vs skip list), analyzing complexity, designing efficient
  solutions, or implementing classic algorithms. Triggers on complexity questions,
  algorithm selection, search/sort/graph problems, or any situation where the right
  choice materially affects correctness or performance.
---

# Data Structures & Algorithms Expert

Helps you pick the right data structure or algorithm for the job, understand
the trade-offs, and arrive at a correct implementation. Works in pseudocode
by default — hand off to a language-specific skill (python-expert,
rust-expert, typescript-expert) for production implementation.

## When to Use

- Choosing between data structures for a specific access pattern
- Analyzing or improving time/space complexity of existing code
- Designing solutions to computational problems (production or interview-style)
- Implementing classic algorithms (sorting, graph, DP, string matching, etc.)
- Understanding trade-offs: cache-friendliness, amortized cost, worst-case guarantees

## When NOT to Use

- **Database query optimization** — use `database-expert`
- **Profiling existing slow code** — use `performance-profiling` to find the bottleneck first, then come back here if the fix is algorithmic
- **Language-specific idioms** — use the relevant language expert
- **System design / architecture** — this skill is about the low-level building blocks, not service topology

## Process

### Step 1: Understand the Problem

Before recommending anything, nail down the constraints:

1. **What operations are needed?** — insert, delete, lookup, range query, iteration, min/max, rank, predecessor/successor
2. **What are the frequency and size characteristics?** — read-heavy vs write-heavy, expected N, growth pattern
3. **What are the hard constraints?** — worst-case latency requirements, memory budget, ordered output needed, thread safety
4. **What's already in place?** — existing data structures, invariants the code relies on

Present this as a brief constraint summary before moving to recommendations.

### Step 2: Recommend with Trade-off Analysis

Never recommend a single option in isolation. Present at minimum two candidates with a comparison:

| Criterion | Option A | Option B |
|-----------|----------|----------|
| Insert | O(?) | O(?) |
| Lookup | O(?) | O(?) |
| Delete | O(?) | O(?) |
| Memory | ... | ... |
| Cache behavior | ... | ... |
| Ordered iteration | yes/no | yes/no |
| Implementation complexity | simple/moderate/complex | ... |

Then give a clear recommendation with reasoning: "Use X because your workload is read-heavy and you need ordered iteration. Y would win on insert throughput but you'd lose ordering."

### Step 3: Design the Solution

Work through the solution in layers:

1. **High-level approach** — name the technique (sliding window, two pointers, union-find, topological sort, etc.) and explain why it fits
2. **Invariants** — state the key invariants that must hold. These are the backbone of correctness
3. **Pseudocode** — clean, language-agnostic pseudocode that captures the logic without language ceremony. Use simple, readable notation:

```
function lru_get(cache, key):
    if key not in cache.map:
        return MISS

    node = cache.map[key]
    move_to_front(cache.list, node)
    return node.value

function lru_put(cache, key, value):
    if key in cache.map:
        update node value
        move_to_front(cache.list, node)
        return

    if cache.size == cache.capacity:
        evict = remove_back(cache.list)
        delete cache.map[evict.key]

    node = new Node(key, value)
    push_front(cache.list, node)
    cache.map[key] = node
```

4. **Complexity proof** — state time and space complexity with brief justification, not just the O() notation. "Each element enters and leaves the deque at most once across the entire loop, so total work is O(n) despite the inner while loop."

### Step 4: Edge Cases and Correctness

Identify edge cases that break naive implementations:

- Empty input
- Single element
- All duplicates
- Already sorted / reverse sorted
- Integer overflow in index calculations (especially for binary search: `mid = lo + (hi - lo) / 2` not `(lo + hi) / 2`)
- Off-by-one in bounds (inclusive vs exclusive)
- Disconnected components in graph problems
- Negative weights / cycles in shortest-path problems

### Step 5: Hand Off to Language Expert

Once the pseudocode and design are solid, the user can take it to a language-specific skill for idiomatic implementation. Point out language-specific considerations:

- **Python:** `collections.deque`, `heapq` (min-heap only — negate for max), `bisect`, `sortedcontainers.SortedList` for balanced BST equivalent
- **Rust:** `BTreeMap`/`BTreeSet` for ordered collections, `HashMap` entry API, ownership considerations for graph structures (arena allocation or index-based graphs)
- **TypeScript:** no built-in sorted set — suggest a library or manual implementation for balanced BST needs. `Map` preserves insertion order but isn't sorted

## Common Data Structure Selection Guide

This is a starting point, not a lookup table. Real problems have nuance.

| Need | First Reach | Consider When |
|------|-------------|---------------|
| Key-value lookup | Hash map | Unordered, O(1) average is fine |
| Ordered key-value | Balanced BST / BTree | Need range queries, ordered iteration, or worst-case O(log n) |
| Priority access (min/max) | Binary heap | Only need top element, not arbitrary lookup |
| Priority + arbitrary delete | Indexed priority queue or balanced BST | Need to update priorities of existing elements |
| Prefix matching | Trie | Autocomplete, common prefix queries |
| Set membership (approximate) | Bloom filter | Can tolerate false positives, need space efficiency |
| Disjoint sets / connectivity | Union-Find | Dynamic connectivity, Kruskal's MST |
| FIFO | Queue (ring buffer) | Fixed-capacity, cache-friendly |
| LIFO | Stack | DFS, expression evaluation, undo |
| Sliding window statistics | Monotonic deque | Min/max over sliding window in O(1) amortized |
| Interval overlap | Interval tree / sweep line | "Which intervals overlap with this query?" |
| 2D spatial queries | k-d tree / R-tree | Nearest neighbor, range search in geometric space |
| String search | KMP / Aho-Corasick / suffix array | Pattern matching in text |

## Common Algorithm Patterns

| Pattern | When to Recognize | Key Idea |
|---------|-------------------|----------|
| Two pointers | Sorted array, pair/subarray problems | Narrow from both ends or slow/fast |
| Sliding window | Contiguous subarray with constraint | Expand right, shrink left to maintain invariant |
| Binary search | Monotonic predicate over search space | Don't just search arrays — search answer spaces |
| BFS/DFS | Graph traversal, connected components | BFS for shortest unweighted path, DFS for exploration |
| Topological sort | Dependency ordering (DAG) | Process nodes with no remaining dependencies |
| Dynamic programming | Overlapping subproblems + optimal substructure | Define state, recurrence, base case. Top-down first, bottom-up if needed for space |
| Greedy | Local optimal choice leads to global optimal | Prove the greedy choice property before trusting it |
| Divide and conquer | Problem splits into independent subproblems | Merge sort, quickselect, closest pair |
| Union-Find | Dynamic connectivity, equivalence classes | Path compression + union by rank = near O(1) |
| Monotonic stack | Next greater/smaller element | Maintain invariant: stack always increasing or decreasing |
| Backtracking | Constraint satisfaction, combinatorial search | Prune early, restore state on backtrack |

## Anti-patterns

| Anti-pattern | Why It's Wrong | Instead |
|-------------|---------------|---------|
| Reaching for hash map by default | Hash maps have poor cache locality, O(n) worst case, and no ordering | Consider whether a sorted array, BTree, or simpler structure fits |
| Premature complexity | Skip list when a sorted array would do | Start simple, measure, then escalate |
| Ignoring constant factors | O(n log n) with huge constants can lose to O(n^2) for small n | Consider practical input sizes, not just asymptotic growth |
| Hand-rolling when stdlib has it | Error-prone, slower, harder to maintain | Use standard library data structures first |
| Optimizing the wrong layer | Fancy algorithm on top of O(n) database calls | Profile first — the bottleneck may not be where you think |
| Choosing based on average case only | Hash map O(1) average but O(n) worst case | If worst-case latency matters, consider balanced BST |

## Outputs

- Constraint summary for the problem
- Trade-off comparison table
- Recommended approach with reasoning
- Pseudocode with invariants documented
- Time/space complexity with justification
- Edge cases identified
- Language-specific notes for handoff to python-expert, rust-expert, or typescript-expert
