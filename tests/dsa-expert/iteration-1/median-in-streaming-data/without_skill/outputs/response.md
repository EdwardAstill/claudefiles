# Streaming Median

The classic solution to streaming median uses two heaps: a max-heap for the lower half of values and a min-heap for the upper half, kept balanced so their sizes differ by at most one.

## Two-Heap Approach

```
addNum(x):
    if max_heap is empty or x <= max_heap.top():
        max_heap.push(x)
    else:
        min_heap.push(x)
    # rebalance
    if max_heap.size > min_heap.size + 1:
        min_heap.push(max_heap.pop())
    elif min_heap.size > max_heap.size:
        max_heap.push(min_heap.pop())

findMedian():
    if max_heap.size > min_heap.size:
        return max_heap.top()
    else:
        return (max_heap.top() + min_heap.top()) / 2.0
```

- addNum: O(log n).
- findMedian: O(1).
- Space: O(n).

## Alternative: Order-Statistic Tree

A balanced BST (AVL or red-black) with subtree size augmentation supports select(k) in O(log n). Both add and findMedian are O(log n). This also supports delete and range queries if you need them.

## Alternative: Frequency Array

Since values are in [-10^5, 10^5], you can use a 200,001-slot counting array. addNum increments count[x - MIN] in O(1). For findMedian, you can walk the array to find the middle, which would be O(range) = O(200001) = O(1) effectively (bounded). With a maintained median pointer and running counts, you can make findMedian O(1) amortized too.

This is actually the best choice for this specific input constraint.

## Approximation

For very large streams or when merging is needed, approximation sketches like t-digest give O(1) add and O(1) quantile queries with bounded error. P² algorithm is another option with even smaller memory.

## Trade-offs

- Two heaps is the general-purpose answer: simple, fast, works for any range.
- Frequency array exploits the bounded value range and wins for this specific problem. Memory is O(R) not O(n).
- BST adds flexibility (delete, range) at the cost of higher constants.
- Approximate algorithms trade accuracy for memory and speed.

## Skewed Distributions

Two heaps are insensitive to skew. The frequency array pointer clusters where the density is high, which is fine. t-digest handles skew especially well because it allocates more resolution near the median.

## Edge Cases

- Single element — odd branch.
- Two elements — careful with integer overflow in the average.
- All duplicates — both medians fall in the same bucket.
- Very large n — for n = 10^8, frequency array uses ~800KB regardless of n; two heaps use O(n) which is large.
