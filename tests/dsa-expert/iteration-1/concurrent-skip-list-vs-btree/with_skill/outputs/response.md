# Concurrent Skip List vs B+ Tree

## Step 1 — Constraint Summary

**Operations:** `insert`, `delete`, `get`, `range_scan(start, end)`.
**Concurrency:** multiple threads, reads + writes.
**Scale:** 10M–100M entries, in-memory.
**Must decide:** skip list or B+ tree, then give concrete insert pseudocode with concurrency control.

**Implied workload dimensions I need to ask about but must still address:**
- Read/write ratio — skews recommendation.
- Range scan length — long scans favor B+ tree.
- Hot-key contention — punishes B+ tree at internal splits.
- Durability/persistence — not requested, in-memory only.

## Step 2 — Trade-off Comparison

| Criterion | Concurrent skip list | Concurrent B+ tree |
|-----------|----------------------|--------------------|
| Insert | O(log n) expected, lock-free feasible | O(log_B n), locks at node/page |
| Delete | O(log n), fine-grained | O(log_B n), may trigger merges |
| Point get | O(log n) expected, lock-free readers | O(log_B n), optimistic locking possible |
| Range scan | O(log n + k), forward links at level 0 are a clean linked list | O(log_B n + k), sibling pointers at leaves |
| Memory per entry | ~4 pointers avg (level geometric dist, p=0.5) | amortized across B+ node (high fanout → low per-key overhead) |
| Cache performance | **poor** — pointer chasing across heap | **good** — cache-line–sized nodes, high fanout, fewer cache misses |
| Lock granularity | node-level, often lock-free | node/page-level; splits/merges require coordinated locks up the tree |
| Write contention | **low** — no structural propagation | **higher** — splits cascade, top-level root splits are global chokepoints |
| Read contention | very low (lock-free traversal) | low with optimistic version-counter scheme (RCU-style) |
| Implementation complexity | medium (randomized, concurrent handshake for insert) | high (concurrent splits/merges done correctly is famously subtle — see B-link trees) |
| Battle-tested libraries | `ConcurrentSkipListMap` (Java), Folly `ConcurrentSkipList` | absent from most stdlibs; databases roll their own |

## Recommendation

**Choose a concurrent (preferably lock-free) skip list** for a mixed read/write workload at 10M–100M. Reasoning:

1. Writes don't cascade up the structure — insert only modifies local nodes and their immediate predecessors at each level. No equivalent of root-splits.
2. Lock-free read traversals are easy to get right (atomic pointer reads) and extensively implemented — you can adopt Java's `ConcurrentSkipListMap` design directly.
3. Fine-grained locking during insert/delete is bounded to `O(log n)` nodes and scales nearly linearly with cores.
4. B+ trees win on cache behavior and point-read throughput (roughly 2–5× in single-threaded benchmarks), so if the workload becomes heavily read-dominant with large range scans, switch to a B-link-tree (B+ tree with right-sibling pointers and optimistic version counters).

If the user signals read-heavy + range-heavy, say >90% reads, recommend the B-link tree despite higher implementation cost — the cache advantage compounds over billions of lookups.

## Step 3 — Design: Lock-Free/Fine-Grained Skip List Insert

### Invariants
- **I1.** Every node at level `k > 0` also exists at level `k-1` (bottom level has all entries).
- **I2.** Forward pointers at each level are in key order.
- **I3.** A node is "visible at level k" iff its predecessor at level k has a `next` pointer pointing to it and is itself visible at level k.
- **I4.** Insert is atomic at level 0; higher-level links become visible after the node is already linked at level 0.
- **I5.** A node's `fully_linked` flag is set after *all* levels have been linked; searches use this as the commit marker.
- **I6.** To modify a node's predecessor set, we lock the predecessors (not the node being inserted — it's newly created and private until linked).

### Pseudocode (Herlihy–Shavit–style, fine-grained lock-based with lock-free reads)

```
function insert(list, key, value):
    top_level = random_level()      # geometric, p = 0.5, capped at MAX_LEVEL
    preds : Node[MAX_LEVEL]
    succs : Node[MAX_LEVEL]

    while true:
        lfound = find(list, key, preds, succs)
        if lfound != -1:
            # key exists — update semantics
            node = succs[lfound]
            if not node.marked:         # deletion flag
                while not node.fully_linked: wait_nanos()
                node.value = value      # CAS or locked field update
                return UPDATED
            continue                    # concurrent delete, retry

        # key not present — lock predecessors bottom-up to prevent structural change
        highest_locked = -1
        try:
            valid = true
            for level in 0..top_level:
                pred = preds[level]; succ = succs[level]
                if level == 0 or pred != preds[level-1]:
                    pred.lock()
                    highest_locked = level
                # validate: pred still points to succ and neither is marked
                if pred.marked or succ.marked or pred.next[level] != succ:
                    valid = false; break
            if not valid:
                continue                 # retry outer loop
            new_node = Node(key, value, top_level)
            for level in 0..top_level:
                new_node.next[level] = succs[level]
            for level in 0..top_level:
                preds[level].next[level] = new_node    # linked bottom-up
            new_node.fully_linked = true
            return INSERTED
        finally:
            unlock_range(preds, highest_locked)

function find(list, key, preds[], succs[]) -> int:
    # lock-free traversal from top-level head
    lfound = -1
    pred = list.head
    for level in MAX_LEVEL-1 .. 0:
        curr = pred.next[level]
        while curr.key < key:
            pred = curr; curr = curr.next[level]
        if lfound == -1 and curr.key == key:
            lfound = level
        preds[level] = pred
        succs[level] = curr
    return lfound
```

`get(key)` is the same `find` without locking, returning the value only if `!marked && fully_linked`. `delete(key)` uses logical marking (`marked = true`) then physical unlink, with the same predecessor-locking protocol.

### Complexity Proof
- Expected path length at each level is O(1) (geometric distribution), with `log_{1/p} n` levels expected, so `find` is O(log n) expected.
- Lock acquisition is bounded by `top_level + 1 ≤ MAX_LEVEL`; MAX_LEVEL chosen so that `(1/p)^MAX_LEVEL >= expected n`, e.g., MAX_LEVEL = 32 for n ≤ 4 × 10^9.
- Locks are held only during the linking of one new node — no global locks, no structural propagation.
- Readers never wait; writers only block writers touching an overlapping predecessor set.
- Space: expected `1 / (1 - p) ≈ 2` forward pointers per node for `p = 0.5`; lower variance and memory with `p = 0.25` at the cost of slightly deeper searches.

## Step 4 — Edge Cases, Contention, Correctness

### Edge cases
- **Duplicate keys:** with update semantics, handle in the `lfound != -1` branch. For multi-value semantics, use a secondary linked list or value-vectors per node.
- **Concurrent insert and delete of same key:** the `marked` flag and retry loop ensure linearizability. Must reacquire the path after a failed validation.
- **Empty range scan:** start > end, or `start_key` not present — begin from the successor of `start_key` at level 0 and walk until key > `end_key` or null.
- **Iterator invalidation during range scan:** scanning at level 0 over a live list requires skipping `marked` nodes and tolerating concurrent inserts — this gives weak (snapshot-isolated) semantics but not repeatable reads. If stronger semantics needed, snapshot the head via RCU epoch counters.
- **Level generation randomness:** use a per-thread PRNG seeded uniquely; a single global RNG becomes a contention point. Java's implementation uses ThreadLocalRandom.
- **MAX_LEVEL clipping bias:** at 10^8 entries with p = 0.5, expected max level ≈ 27; cap at 32 to avoid tail cost.

### Scalability notes
- For B+ trees, the dominant contention is at internal nodes during splits. B-link trees add right-sibling pointers and a "high key" to let searches proceed past in-flight splits without blocking — this is what InnoDB and PostgreSQL effectively do. Getting it right is non-trivial.
- Skip list writes have **bounded locality** — a single insert touches a constant-expected number of unique predecessors. B+ tree splits have **unbounded locality** in the worst case (cascading root splits).
- For range scans > ~100 entries, B+ tree leaves are strictly faster per entry (sequential cache lines). Skip list level-0 traversal has one pointer chase per step.

## Step 5 — Language Handoff

- **Java:** just use `java.util.concurrent.ConcurrentSkipListMap` — production-grade lock-free skip list with range views (`subMap`, `tailMap`, `headMap`). Don't roll your own.
- **C++:** Folly `ConcurrentSkipList`, or `cds::container::SkipListMap` from the Concurrent Data Structures library. Alternatively Facebook's `folly::AtomicHashMap` for non-ordered.
- **Rust:** `crossbeam-skiplist` (`SkipMap`) is a well-tested lock-free skip list with epoch-based memory reclamation. For a B-tree, `std::collections::BTreeMap` is *not* concurrent — wrap with `RwLock` or use `dashmap` (hash map, not ordered).
- **Go:** no stdlib ordered concurrent map; `github.com/huandu/skiplist` or build on `sync.RWMutex` over a skip list.
- **Python:** no C-level concurrent primitives matter under the GIL; `sortedcontainers.SortedDict` under a `threading.Lock` is usually fine.

Memory-reclamation note: lock-free skip lists need **hazard pointers** or **epoch-based reclamation (EBR)** to free nodes safely. EBR (used by crossbeam) is simpler and generally faster; hazard pointers give more predictable latency.
