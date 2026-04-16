# Finding the K Most Frequent Elements in a High-Throughput Event Stream

## Problem Summary

You need to maintain frequency counts over a continuous stream of events arriving at ~10k/sec and answer "top-k" queries at any point in time. The two core operations are:

1. **Ingest** -- process each incoming event and update frequency information.
2. **Query** -- return the k most frequent event types seen so far.

Both operations must be fast; ingestion is on the hot path and must keep up with the stream.

---

## Recommended Approach: Hash Map + Min-Heap of Size k

### Data Structures

| Structure | Purpose |
|---|---|
| **Hash map** (`event_id -> count`) | O(1) amortized count updates on every incoming event |
| **Min-heap of size k** (keyed by count) | Maintains the current top-k elements; the root is the smallest count among the top-k |

### How It Works

#### Ingestion (per event)

1. Look up the event in the hash map and increment its count. **O(1) amortized.**
2. If the event is already in the heap, update its count and bubble it up/down as needed. **O(log k).**
3. If the event is not in the heap:
   - If the heap has fewer than k elements, insert the event. **O(log k).**
   - If the event's new count exceeds the heap's minimum (the root), extract the root and insert the event. **O(log k).**
   - Otherwise, do nothing to the heap.

#### Query (top-k)

Return the contents of the heap. **O(k)** to copy, or **O(k log k)** if you need them sorted.

### Complexity

| Operation | Time | Space |
|---|---|---|
| Ingest one event | O(1) average (hash) + O(log k) worst case (heap) | -- |
| Query top-k | O(k) unsorted, O(k log k) sorted | -- |
| Total space | O(n + k) where n = distinct event types | -- |

At 10k events/sec with, say, k = 100, the heap work per event is at most O(log 100) ~ 7 comparisons. This is easily fast enough.

### Why a Min-Heap (not a Max-Heap)?

A min-heap lets you efficiently guard the "entry threshold" into the top-k set. The root holds the smallest count among the current top-k. When a new event's count exceeds this minimum, you pop the root and push the newcomer. A max-heap would require scanning all k elements to find the one to evict.

---

## Implementation Sketch (Python-like Pseudocode)

```python
import heapq

class TopKTracker:
    def __init__(self, k: int):
        self.k = k
        self.counts = {}          # event_id -> count
        self.heap = []            # min-heap of (count, event_id)
        self.heap_set = set()     # event_ids currently in the heap

    def ingest(self, event_id):
        # Update count
        self.counts[event_id] = self.counts.get(event_id, 0) + 1
        count = self.counts[event_id]

        if event_id in self.heap_set:
            # Lazy update: push new entry; stale entries are cleaned on pop
            heapq.heappush(self.heap, (count, event_id))
        elif len(self.heap_set) < self.k:
            heapq.heappush(self.heap, (count, event_id))
            self.heap_set.add(event_id)
        elif count > self.heap[0][0]:
            # Evict the current minimum
            self._pop_min()
            heapq.heappush(self.heap, (count, event_id))
            self.heap_set.add(event_id)

    def query_top_k(self):
        # Clean stale entries and collect results
        result = {}
        for count, event_id in self.heap:
            if event_id in self.heap_set:
                # Keep the latest (highest) count for each event_id
                result[event_id] = max(result.get(event_id, 0), count)
        return sorted(result.items(), key=lambda x: -x[1])[:self.k]

    def _pop_min(self):
        while self.heap:
            count, event_id = heapq.heappop(self.heap)
            if event_id in self.heap_set and count == self.counts.get(event_id):
                self.heap_set.discard(event_id)
                return
            elif event_id in self.heap_set:
                # Stale entry; keep popping
                continue
            # Event already evicted; keep popping
```

> **Note on lazy deletion:** Because Python's `heapq` does not support decrease-key / increase-key, the standard technique is to push a new entry with the updated count and discard stale entries when they surface at the root. This keeps ingestion O(log n) worst case but amortized O(log k) for the heap operations that matter.

---

## Alternatives Considered

### 1. Count-Min Sketch + Heap (Approximate)

If you can tolerate approximate counts (e.g., for analytics dashboards), a **Count-Min Sketch** replaces the hash map:

- Uses sub-linear space: O(w * d) where w = width, d = depth (number of hash functions).
- Provides an over-estimate of counts (never under-counts).
- Pair it with a min-heap of size k the same way as above.
- Trade-off: approximate counts, possible over-counting of infrequent items.

**Best for:** very large cardinality streams where you cannot afford to store every distinct event.

### 2. Space-Saving Algorithm (Metwally et al., 2005)

A streaming algorithm specifically designed for finding frequent items in bounded memory:

- Maintains a fixed set of k monitored elements.
- When a new (unmonitored) element arrives, it replaces the element with the smallest count and inherits that count + 1.
- Provides guaranteed error bounds.
- **O(1)** per update using a doubly-linked list of count buckets.

**Best for:** when memory is strictly bounded and you want formal approximation guarantees.

### 3. Lossy Counting (Manku & Motwani, 2002)

Another streaming algorithm that provides frequency estimates with bounded error relative to the total stream length. More complex to implement; better suited when you need frequency thresholds rather than strict top-k.

### 4. Full Sort / Selection on Query

Keep only the hash map and run a selection algorithm (e.g., quickselect) at query time:

- Ingestion: O(1)
- Query: O(n) where n = distinct events

**Best for:** infrequent queries, very large k, or when k is close to n.

---

## Recommendation Summary

| Scenario | Recommended Approach |
|---|---|
| **Exact counts, moderate cardinality (< millions of distinct events)** | Hash map + min-heap of size k (the primary recommendation) |
| **Approximate counts OK, very high cardinality** | Count-Min Sketch + min-heap |
| **Strict memory bound, formal guarantees needed** | Space-Saving algorithm |
| **Queries are very rare compared to ingestion** | Hash map + quickselect on demand |

For your use case (10k events/sec, exact top-k queries at any time), the **hash map + min-heap** approach is the clear winner. It provides:

- Exact counts
- O(1) average ingestion cost with O(log k) heap maintenance
- O(k log k) query time
- Simple implementation with no approximation error

At 10k events/sec, even a straightforward Python implementation can keep up. In C++, Java, or Rust, this approach handles millions of events per second comfortably.
