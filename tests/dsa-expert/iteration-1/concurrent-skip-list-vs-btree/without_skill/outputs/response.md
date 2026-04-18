# Concurrent Skip List vs B+ Tree for In-Memory KV Store

## Comparison

### Lock Granularity
- Skip list: fine-grained, each node can be locked independently. Readers can traverse without locks using atomic pointer reads.
- B+ tree: locks are at node/page level. Structural changes (splits, merges) can cascade and require locking multiple nodes up the tree.

### Cache Performance
- B+ tree wins. Cache-line-sized nodes with high fanout mean fewer cache misses per lookup.
- Skip list has poor spatial locality — lots of pointer chasing across unrelated memory.
- B+ trees are typically 2-5x faster on single-threaded reads.

### Memory Overhead
- Skip list: ~2 pointers per level, expected 2 levels per node, ~4 pointers per entry on average.
- B+ tree: per-node fill factor means overhead is amortized across many keys. Usually lower memory per entry.

### Scalability Under Contention
- Skip list: scales better under write-heavy loads because structural changes are local. No root-level contention.
- B+ tree: contention at internal nodes during splits; root can become a bottleneck. Optimistic locking (B-link trees with version counters) helps for reads.

## Recommendation

For 10M-100M entries with concurrent reads and writes:
- Skip list for write-heavy or mixed workloads.
- B+ tree with optimistic concurrency for read-heavy workloads with range scans.

Java's ConcurrentSkipListMap is a proven example of the skip list approach and is a reasonable default.

## Concurrent Skip List Insert Pseudocode

```
function insert(key, value):
    top_level = random_level()
    preds, succs = arrays of size top_level+1

    retry:
        found_level = find(key, preds, succs)
        if found_level >= 0:
            node = succs[found_level]
            if not node.marked:
                wait_until(node.fully_linked)
                node.value = value
                return
            goto retry

        # lock predecessors bottom-up
        locks_held = []
        valid = true
        for level in 0..top_level:
            pred = preds[level]; succ = succs[level]
            if level == 0 or pred != preds[level-1]:
                pred.lock()
                locks_held.push(pred)
            if pred.marked or succ.marked or pred.next[level] != succ:
                valid = false
                break
        if not valid:
            unlock all in locks_held
            goto retry

        new_node = Node(key, value, top_level)
        for level in 0..top_level:
            new_node.next[level] = succs[level]
            preds[level].next[level] = new_node
        new_node.fully_linked = true
        unlock all in locks_held
```

- Readers traverse without locks.
- Writers lock only the affected predecessors.
- `find` walks top-down, descending when `curr.key >= target`.

## Range Scan

Start with `find(start_key)`, then walk level-0 forward pointers until key > end_key. Skip marked nodes. Weak iteration semantics unless you implement snapshot isolation.

## Edge Cases

- Duplicate keys: update semantics handled in the `found_level >= 0` branch.
- Concurrent insert and delete: marked flag + retry loop.
- Memory reclamation for lock-free: hazard pointers or epoch-based reclamation.

## Summary

Skip list is the pragmatic choice here. Use ConcurrentSkipListMap or crossbeam-skiplist rather than rolling your own.
