# K Most Frequent Elements in a High-Throughput Event Stream

## Step 1: Constraint Summary

**Operations needed:**
- **Insert/Update:** Increment the frequency count of an event type as events arrive (~10k/sec)
- **Top-k query:** At any point, retrieve the k event types with the highest frequency
- **No deletion required** (stream is append-only from the problem description)

**Frequency and size characteristics:**
- Write-heavy: 10,000 inserts per second
- Read pattern: top-k queries at arbitrary times (assumed less frequent than writes)
- N = number of distinct event types (unknown but likely far smaller than total event count)
- Growth: frequency counts grow monotonically; the set of distinct event types grows over time but stabilizes

**Hard constraints:**
- Insert must be fast enough to keep up with 10k events/sec (must be sub-100us per insert to leave headroom)
- Top-k query should be responsive (sub-millisecond to low milliseconds)
- Memory budget proportional to distinct event types, not total events

**What's already in place:**
- Not specified; designing from scratch

---

## Step 2: Trade-off Analysis

There are three viable approaches here. The core challenge is maintaining frequency counts (easy) while also being able to efficiently extract the top-k (harder).

### Option A: Hash Map + Min-Heap of Size k

Maintain a hash map from event_type to count. For top-k queries, maintain a separate min-heap of size k that tracks the k most frequent elements.

### Option B: Hash Map + Full Sort on Query

Maintain a hash map from event_type to count. When top-k is requested, extract all entries and partial-sort (quickselect).

### Option C: Hash Map + "Bucket Sort" Frequency Map (Double Hash Map)

Maintain a hash map from event_type to count AND a reverse mapping from count to a set of event_types at that count. Track the current maximum frequency.

| Criterion | A: HashMap + Min-Heap | B: HashMap + Quickselect | C: HashMap + Frequency Buckets |
|---|---|---|---|
| Insert (update count) | O(1) avg hash + O(log k) heap update | O(1) avg hash only | O(1) avg hash + O(1) bucket move |
| Top-k query | O(k) (heap already maintained) | O(N + N) partial sort = O(N) | O(k) walk from max bucket down |
| Delete | O(log k) if in heap | O(1) hash delete | O(1) hash + O(1) bucket move |
| Memory | O(N + k) | O(N) | O(N) (two hash maps, same key set) |
| Cache behavior | Heap is array-backed, decent locality | Sort touches all N entries | Pointer-heavy bucket sets, poor locality |
| Ordered iteration | Top-k only (heap order, not sorted) | Returns sorted if desired | Naturally ordered by frequency |
| Implementation complexity | Moderate | Simple | Moderate |
| Insert latency consistency | Log k per update (small) | O(1) constant | O(1) constant |

### Recommendation

**Use Option C: Hash Map + Frequency Buckets** (sometimes called the "O(1) frequency counter" or the pattern used in LFU caches).

Reasoning:
- Your workload is heavily write-dominated (10k inserts/sec) with occasional reads. Option C gives true O(1) inserts because moving an event from bucket `f` to bucket `f+1` is constant-time hash map operations. Option A's O(log k) heap maintenance on every insert is unnecessary overhead when queries are infrequent.
- Top-k queries are O(k) by walking down from the maximum frequency bucket -- which is optimal since you must read k items.
- Option B's O(N) query cost is unacceptable if N (distinct event types) grows large and queries need to be responsive.
- If k is very small and fixed (say k=10), Option A is also excellent. But Option C is strictly better on insert throughput and equally good on query time.

**If simplicity is paramount and k is small and fixed**, Option A (HashMap + Min-Heap) is the pragmatic second choice. It is simpler to implement correctly and the O(log k) overhead per insert is negligible for small k (log 10 ~ 3 comparisons).

---

## Step 3: Solution Design

### High-level Approach

This uses the **frequency bucket** technique (the same core idea behind O(1) LFU cache eviction). We maintain two coordinated data structures:

1. A hash map `count_map: event_type -> current_count` for O(1) frequency lookup
2. A hash map `bucket_map: count -> Set<event_type>` grouping events by their current frequency
3. A single integer `max_freq` tracking the highest frequency seen

When an event arrives, we move it from its old frequency bucket to the new one. When top-k is queried, we walk from `max_freq` downward collecting items.

### Invariants

1. **Count consistency:** For every event_type `e`, `count_map[e] == f` if and only if `e` is in `bucket_map[f]`.
2. **Max-freq correctness:** `max_freq` is always equal to the maximum key in `bucket_map` that has a non-empty set. Since frequencies only increase (stream is append-only), `max_freq` is monotonically non-decreasing and never needs to be decremented.
3. **Completeness:** Every event type that has been seen at least once exists in exactly one bucket and in `count_map`.

### Pseudocode

```
structure FreqTracker:
    count_map  : HashMap<EventType, Integer>    // event -> its current count
    bucket_map : HashMap<Integer, Set<EventType>> // count -> set of events with that count
    max_freq   : Integer = 0

function record_event(tracker, event):
    old_count = tracker.count_map.get(event, 0)
    new_count = old_count + 1

    // Update count map
    tracker.count_map[event] = new_count

    // Move event between frequency buckets
    if old_count > 0:
        tracker.bucket_map[old_count].remove(event)
        if tracker.bucket_map[old_count] is empty:
            delete tracker.bucket_map[old_count]   // optional cleanup

    if new_count not in tracker.bucket_map:
        tracker.bucket_map[new_count] = new empty Set

    tracker.bucket_map[new_count].add(event)

    // Update max (only increases in append-only stream)
    if new_count > tracker.max_freq:
        tracker.max_freq = new_count

function top_k(tracker, k):
    result = []
    freq = tracker.max_freq

    while freq > 0 and len(result) < k:
        if freq in tracker.bucket_map:
            for event in tracker.bucket_map[freq]:
                result.append((event, freq))
                if len(result) == k:
                    break
        freq = freq - 1

    return result
```

### Complexity Proof

**`record_event`:** O(1) amortized.
- `count_map.get` and `count_map[event] = ...` are O(1) average for hash maps.
- `bucket_map[old_count].remove(event)` is O(1) average for a hash set.
- `bucket_map[new_count].add(event)` is O(1) average for a hash set.
- The `max_freq` comparison is O(1).
- Total: O(1) amortized per event. At 10k events/sec this is comfortably achievable.

**`top_k`:** O(k + F) where F is the number of empty frequency levels between max_freq and the k-th most frequent element's frequency.
- In the worst case, if frequencies are very sparse, we might skip many empty buckets. In practice, F is bounded by the gap between the highest and k-th highest frequency, which is typically small.
- Best case (dense frequencies, as expected in high-throughput streams): O(k).
- We can improve worst case to strict O(k) by maintaining a sorted structure of non-empty frequencies (e.g., a doubly-linked list of buckets ordered by frequency, exactly as in LFU cache implementations). This makes `top_k` always O(k) at no extra cost to insert.

**Space:** O(N) where N is the number of distinct event types. Each event type appears once in `count_map` and once in exactly one bucket in `bucket_map`. The bucket_map has at most N entries (one per distinct frequency value).

---

## Step 4: Edge Cases and Correctness

1. **First occurrence of an event:** `old_count` is 0, so we skip the bucket removal step and only add to bucket 1. The `get(event, 0)` default handles this.

2. **k larger than number of distinct events:** The `top_k` function naturally handles this -- the loop terminates when `freq` reaches 0, and the result will contain fewer than k items. The caller should be aware of this possibility.

3. **k = 0:** Returns an empty list. The while-loop condition `len(result) < k` is immediately false.

4. **Single event type (all events are the same):** Works correctly. One entry in `count_map`, one bucket that keeps moving up in frequency. `max_freq` tracks it.

5. **Tie-breaking among events with equal frequency:** The iteration order within a bucket (hash set) is arbitrary. If deterministic tie-breaking is needed (e.g., alphabetical, or by first-seen time), replace the `Set` in `bucket_map` with an ordered structure (sorted set or linked list maintaining insertion order).

6. **Integer overflow on count:** At 10k events/sec, a 64-bit integer overflows after ~29 million years. A 32-bit integer overflows after ~2.5 days if a single event type receives all traffic. **Use 64-bit integers for counts.**

7. **Sparse frequency gaps in `top_k`:** If one event has count 1,000,000 and the next has count 5, the naive loop walks through 999,995 empty buckets. **Mitigation:** Use the linked-list variant (as in LFU cache) where buckets are linked in order and empty buckets are removed, making traversal O(k) regardless of frequency gaps.

8. **Thread safety (concurrent access):** At 10k events/sec, concurrent writes are likely. The naive structure is NOT thread-safe. Options:
   - **Single-writer pattern:** Funnel all events through one writer thread; readers take a snapshot.
   - **Sharded counters:** Partition events by hash across N shards, each with its own lock. Merge results for top-k queries.
   - **Read-write lock:** Acceptable if write contention is low (unlikely at 10k/sec).
   - **Lock-free approximate:** Use Count-Min Sketch for approximate frequencies + a separate heap for top-k candidates (see "approximate alternative" below).

9. **Approximate alternative -- Count-Min Sketch + Heap:** If exact counts are not required and memory must be bounded regardless of distinct event count, a Count-Min Sketch provides approximate frequency estimates in O(1) time and O(1) space per event, with a min-heap of size k maintained alongside. This trades exactness for guaranteed bounded memory and excellent throughput. Consider this if distinct event types number in the millions.

---

## Step 5: Language-Specific Handoff Notes

### Python
- `collections.defaultdict(set)` for `bucket_map`, `collections.defaultdict(int)` for `count_map`
- For the linked-list variant, `collections.OrderedDict` or a manual doubly-linked list
- `heapq` is available if you go with Option A (min-heap approach) -- remember it is a min-heap, so use it directly (you want the min of the top-k to know what to evict)
- For thread safety, `threading.Lock` around the structure, or use `multiprocessing.Queue` to funnel events to a single writer
- For the approximate approach, the `pybloom_live` or `datasketches` library provides Count-Min Sketch

### Rust
- `HashMap<EventType, u64>` for `count_map`, `HashMap<u64, HashSet<EventType>>` for `bucket_map`
- `BTreeMap<u64, HashSet<EventType>>` is an excellent choice for `bucket_map` if you want to avoid the sparse-gap problem entirely -- `iter().rev()` gives you frequencies in descending order in O(log N) to start + O(k) to collect
- For thread safety, `dashmap` crate for concurrent hash maps, or `Arc<RwLock<FreqTracker>>`
- For the approximate approach, the `probabilistic-collections` crate has Count-Min Sketch
- Consider `SmallVec` or `ArrayVec` for the bucket sets if most frequencies have few event types

### TypeScript
- `Map<string, number>` for `count_map`, `Map<number, Set<string>>` for `bucket_map`
- No built-in sorted map; if you need the linked-list variant, implement a doubly-linked list or use a library like `bintrees`
- For the heap approach (Option A), no built-in heap -- use a library like `heap-js` or implement a simple binary heap
- For thread safety in Node.js, the single-threaded event loop means concurrent writes are not an issue unless using Worker threads
- For high throughput, consider buffering events and processing in batches to reduce per-event overhead
