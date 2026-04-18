# Streaming Median

## Step 1 — Constraint Summary

**Operations:** `addNum(int)`, `findMedian() -> double`.
**Scale:** up to 10^8 numbers — memory matters.
**Value range:** `[-10^5, 10^5]` — bounded! This is a huge lever.
**Performance:** "as efficient as possible" — interpret as "best asymptotic + good constants."
**Variants:** heavy skew, approximate OK.

The bounded range is the key observation: naive answers (two heaps) ignore it.

## Step 2 — Candidate Approaches

| Criterion | Two heaps | Order-stat BST (AVL/RB) | Frequency array (bucket) | Approximate (t-digest / P²) |
|-----------|-----------|-------------------------|---------------------------|------------------------------|
| addNum    | O(log n)  | O(log n)                | **O(1)**                  | O(1)                         |
| findMedian| O(1)      | O(log n)                | **O(R) once, O(1) incremental** | O(1)                  |
| Space     | O(n)      | O(n)                    | **O(R) = O(2·10^5) bounded** | O(compression_param) ≈ O(100–1000) |
| Supports delete | no  | yes                     | yes (decrement)           | no                           |
| Range queries | no   | yes                     | yes                       | approximate                  |
| Exact answer | yes    | yes                     | yes                       | no (bounded error)           |
| Implementation | easy | hard                    | easy                      | moderate (library)           |

**Recommendation:** Because the range is bounded at `|R| = 2·10^5 + 1 ≈ 200K`, a **frequency array with an incrementally-maintained median pointer** beats two heaps on both operations. Two-heaps is the canonical general answer; frequency-array is the right answer for this specific problem.

Fall back to two heaps if the range weren't bounded. Use t-digest if approximate answers suffice and you want O(1) add with low memory regardless of n.

## Step 3 — Design (Frequency Array)

### Invariants
- **I1.** `count[v - MIN]` = number of times `v` has appeared in the stream, for `v ∈ [-10^5, 10^5]`.
- **I2.** `total_n` = sum of `count[]`.
- **I3.** `median_ptr` = index in `count[]` such that `below_count` = number of elements strictly below `MIN + median_ptr`, and `below_count + count[median_ptr]` >= ⌈total_n / 2⌉.
- **I4.** After every `addNum`, `median_ptr` and `below_count` are updated by at most one increment/decrement.

### Pseudocode

```
MIN = -100000
R   = 200001    # values in [-100000, 100000]
count: int[R]   # zero-initialized
total_n = 0
median_ptr = 0            # index into count[]
below_count = 0           # number of values strictly below (MIN + median_ptr)

function addNum(x):
    idx = x - MIN
    count[idx] += 1
    total_n += 1

    if idx < median_ptr:
        below_count += 1

    # Walk the pointer to restore invariant I3:
    # we want below_count < ceil(total_n / 2) <= below_count + count[median_ptr]
    while below_count >= (total_n + 1) / 2:       # integer ceil
        median_ptr -= 1
        below_count -= count[median_ptr]
    while below_count + count[median_ptr] < (total_n + 1) / 2:
        below_count += count[median_ptr]
        median_ptr += 1

function findMedian():
    if total_n is odd:
        return (MIN + median_ptr)     # integer cast but return double
    # even: median_ptr is the lower-median bucket; find upper median
    if 2 * (below_count + count[median_ptr]) > total_n:
        # both medians fall in the same bucket
        return (MIN + median_ptr)
    # upper median is the next non-empty bucket
    upper = median_ptr + 1
    while count[upper] == 0: upper += 1
    return ((MIN + median_ptr) + (MIN + upper)) / 2.0
```

### Complexity Proof
- **addNum:** the while-loops move `median_ptr` by at most one per call in steady state (since each add changes `below_count` by at most 1 and `total_n` by 1; the true median changes by at most one bucket). **Amortized O(1)** and effectively O(1) per call after warm-up. Single operations may walk further on cold starts but that cost is amortized across the stream.
- **findMedian:** O(1) in the odd case, O(1) amortized in the even case (the "walk to next non-empty bucket" is bounded by sparse regions; worst case O(R) but extremely rare — can be eliminated by maintaining a `next_nonempty` helper).
- **Space:** O(R) = O(200001) ≈ 800 KB with 4-byte ints. Independent of n. For n = 10^8 this is a 100000× memory win over two-heaps.

### Two-Heap (fallback reference)

```
max_heap = MaxHeap()   # lower half
min_heap = MinHeap()   # upper half
invariant: |size(max_heap) - size(min_heap)| <= 1,
           max_heap.top() <= min_heap.top()

function addNum(x):
    if max_heap empty or x <= max_heap.top(): max_heap.push(x)
    else: min_heap.push(x)
    if size(max_heap) > size(min_heap) + 1:
        min_heap.push(max_heap.pop())
    elif size(min_heap) > size(max_heap):
        max_heap.push(min_heap.pop())

function findMedian():
    if size(max_heap) > size(min_heap): return max_heap.top()
    return (max_heap.top() + min_heap.top()) / 2.0
```
Complexity: O(log n) add, O(1) find. Space O(n).

## Step 4 — Edge Cases, Skew, Approximation

### Edge Cases
- `n = 0` — `findMedian` undefined; document behavior.
- `n = 1` — trivial; odd branch returns the lone element.
- `n = 2` — even branch; watch integer overflow in `(a + b) / 2` — use `a + (b - a) / 2.0` or cast to double.
- All identical values — `median_ptr` sits on that bucket; both odd and even branches work.
- Alternating max/min — `median_ptr` oscillates by exactly ±1; O(1) maintained.
- Integer overflow in sum for averaging — irrelevant at |value| ≤ 10^5; but if range grew, use double or long.

### Heavily Skewed Distributions
- **Two heaps:** completely insensitive to skew. Work proportional to log n regardless.
- **Frequency array:** skew concentrates `median_ptr` in a narrow region of `count[]`; pointer walks become *shorter*, speeding things up. Cache-friendly.
- **BST:** depth stays balanced (that's the point of AVL/RB); unaffected by skew.

### Approximate Answers
- **t-digest** (Dunning): adaptive centroids, O(1) add, O(1) find for any quantile (not just median), bounded relative error, ~1 KB per digest. Ideal for very large streams and merging across shards.
- **P² algorithm** (Jain & Chlamtac): five-marker approximation, O(1) add, no memory growth, but less accurate and doesn't merge cleanly.
- **Count-min sketch + binary search** for quantiles — more general but heavier.

For n = 10^8 with bounded values, exact with frequency array is strictly better than approximate.

## Step 5 — Language Handoff

- **Python:** `heapq` is min-heap; for max-heap negate values. `heappush` + `heappop` O(log n). For the frequency-array approach, use `array.array('i', [0]*200001)` or a `numpy.int32` array.
- **Rust:** `std::collections::BinaryHeap` is a max-heap; wrap with `Reverse` for min. Frequency array is a `Vec<u32>` of fixed size — perfect fit.
- **Java:** `PriorityQueue` + `Collections.reverseOrder()` for max. Frequency array is `int[R]`.
- **C++:** `std::priority_queue` defaults to max-heap. Frequency array is `std::array<int, R>`.

If the user needs merging across distributed shards, point them at **t-digest** libraries (`tdigest` in Python, `com.tdunning.math:t-digest` in Java).
