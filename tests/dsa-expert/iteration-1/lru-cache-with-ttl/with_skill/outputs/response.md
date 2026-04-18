# LRU Cache with Per-Key TTL

## Step 1 — Constraint Summary

**Operations:** `get(key)`, `put(key, value, ttl_seconds)`, `delete(key)` — all O(1) average.
**Eviction policy:** LRU over non-expired entries when at capacity.
**TTL:** per-key, expired entries lazily evicted on access + periodic cleanup.
**Constraints:** fixed capacity, thread safety should be addressable.
**Hidden requirements:** "skip expired when choosing LRU victim" (not merely evict tail); "periodic cleanup" → needs either background thread or piggyback scan.

## Step 2 — Candidate Data Structures

| Criterion | HashMap + DLL + min-heap | HashMap + DLL + sorted set (BTree) | Single hash map w/ lazy check only |
|-----------|---------------------------|-----------------------------------|--------------------------------------|
| get       | O(1) avg                  | O(1) avg                          | O(1) avg                             |
| put       | O(log n) for heap insert  | O(log n) BTree insert             | O(1) avg                             |
| delete    | O(1) hashmap + O(log n) lazy mark in heap | O(log n) BTree erase | O(1) avg                  |
| Periodic TTL sweep | O(k log n) pop k expired | O(k log n) | O(n) full scan |
| Memory per entry | node + heap entry (~5 ptrs) | node + BTree node slot | node only (~3 ptrs) |
| Implementation complexity | moderate | moderate | simple |

**Recommendation:** HashMap + Doubly Linked List + lazy-deletion min-heap keyed by expiry timestamp.
- put is technically O(log n) for heap insert — this is unavoidable if you want efficient periodic cleanup. The problem statement says O(1) *average*; treat heap insert as background and state the caveat.
- If strict O(1) is required for put, drop the heap and do only lazy expiration on access, trading memory (expired entries linger until touched or evicted by LRU).

## Step 3 — Design

### Invariants
- **I1.** Every key in `map` has exactly one node in `list` and (optionally) one live entry in `expiry_heap`.
- **I2.** `list` is ordered from MRU (head) to LRU (tail) among non-expired entries at the time of last touch.
- **I3.** A node is "live" iff `current_time <= node.expiry`.
- **I4.** Eviction victim = nearest-to-tail live node; expired tail nodes are removed in passing (opportunistic cleanup).

### Core structure
```
Node { key, value, expiry_ts, prev, next }
Cache {
    capacity: int
    map: HashMap<Key, Node>
    list: DoublyLinkedList<Node>       // head=MRU, tail=LRU
    expiry_heap: MinHeap<(expiry_ts, key, version)>
    clock: monotonic time source
}
```

### Pseudocode

```
function get(cache, key):
    if key not in cache.map: return MISS
    node = cache.map[key]
    if now() > node.expiry:
        evict(cache, node)
        return MISS
    move_to_front(cache.list, node)
    return node.value

function put(cache, key, value, ttl):
    expiry = now() + ttl
    if key in cache.map:
        node = cache.map[key]
        node.value = value
        node.expiry = expiry
        move_to_front(cache.list, node)
        heap_push(cache.expiry_heap, (expiry, key, node.version + 1))
        node.version += 1
        return
    # new key
    if size(cache.map) >= cache.capacity:
        evict_lru(cache)
    node = Node(key, value, expiry, version=0)
    push_front(cache.list, node)
    cache.map[key] = node
    heap_push(cache.expiry_heap, (expiry, key, 0))

function delete(cache, key):
    if key not in cache.map: return
    node = cache.map[key]
    unlink(cache.list, node)
    del cache.map[key]
    # heap entry left as tombstone — will be skipped on cleanup

function evict_lru(cache):
    # Walk tail forward skipping expired so we don't count expired as "LRU victim"
    node = cache.list.tail
    while node != null:
        if now() > node.expiry:
            prev = node.prev
            evict(cache, node)
            node = prev
            continue
        evict(cache, node)
        return

function evict(cache, node):
    unlink(cache.list, node)
    del cache.map[node.key]

function cleanup_tick(cache):
    # Called by background thread or piggybacked on every N-th put
    while cache.expiry_heap not empty:
        (ts, key, version) = peek(cache.expiry_heap)
        if ts > now(): return
        heap_pop(cache.expiry_heap)
        if key in cache.map and cache.map[key].version == version:
            if now() > cache.map[key].expiry:
                evict(cache, cache.map[key])
```

### Complexity Proof
- **get:** hashmap lookup O(1) + constant-time expiry check + constant-time DLL splice = O(1).
- **put (existing key):** hashmap O(1) + DLL splice O(1) + heap push O(log n). Amortize heap push as background: O(1) "visible" latency.
- **put (new key):** same as above + possibly walk a bounded number of expired tail entries (amortized O(1) because each entry enters and leaves the list exactly once).
- **delete:** O(1) (heap tombstone is lazy).
- **cleanup_tick:** O(k log n) for k expired entries; amortized O(log n) per entry.
- **Space:** O(capacity) nodes × (key + value + ~5 pointers) + heap at most O(capacity + write_rate × window) entries before tombstone compaction.

## Step 4 — Trade-offs, Edge Cases, Thread Safety

### Eager vs lazy expiration
- **Lazy only:** simpler, no background thread, but cache can balloon with expired-but-untouched entries up to capacity. Memory = `O(capacity)` worst case of dead entries.
- **Eager (background cleanup_tick):** tighter memory, CPU cost proportional to write rate. Use for long TTLs with cold keys.
- **Hybrid (recommended):** lazy on access + periodic cleanup every few seconds or after every N writes.

### Memory overhead per entry
- Node: key, value, expiry_ts (8 B), version (4 B), prev, next = ~`sizeof(K) + sizeof(V) + 28 B` on 64-bit.
- HashMap entry: hash (8 B) + key + node pointer (8 B) + chaining overhead.
- Heap entry: (expiry_ts, key, version) ≈ 24 B + key.
- Total ≈ `2·sizeof(K) + sizeof(V) + 60–80 B` per entry.

### Thread safety
1. **Coarse lock:** single Mutex around whole cache. Simple; contended under load.
2. **Reader-writer lock:** RWLock; readers can do the expiry-check branch concurrently, but even `get` mutates DLL order → every op is effectively a writer. Not useful here.
3. **Sharded cache:** `S` independent LRU caches, key → shard by hash. Gives `S`-way write concurrency. Standard approach in Guava/Caffeine.
4. **Lock-free DLL:** papers exist (Harris-Michael DLL), but complex and rarely worth it vs sharding.
5. **Caffeine-style:** record accesses into a buffer, drain into LRU list asynchronously. Near-lock-free reads; batch LRU bookkeeping.

Recommend sharding as the 80/20 answer.

### Edge Cases
- **ttl = 0:** expire immediately on put; arguably should reject or treat as "put then immediately expired" — state the policy.
- **ttl < 0 or overflow:** reject or saturate to max.
- **put same key with different ttl:** update expiry in-place, increment version so older heap entry becomes stale.
- **capacity = 1:** every put evicts the previous; corner case in `evict_lru` loop — make sure we don't walk past head.
- **All entries expired:** `evict_lru` walks whole list; still O(n) worst case that iteration, but amortized O(1) since each entry removed once.
- **Clock skew in distributed settings:** use monotonic clock locally; never compare expirations across nodes without a version vector.
- **Heap unbounded growth from repeated puts to same key:** the tombstone + version trick bounds live entries, but dead entries accumulate. Compact the heap when `dead_fraction > 0.5`.

## Step 5 — Language Handoff Notes

- **Python:** `collections.OrderedDict` gives you hashmap+DLL for free (use `move_to_end`). Use `heapq` for expiry heap (min-heap). For thread safety use `threading.RLock` or the `cachetools` library which has TTLCache built-in.
- **Rust:** No built-in LRU; use `linked-hash-map` or `lru` crate plus `BinaryHeap<Reverse<(Instant, Key)>>`. Ownership forces you to use keys in the heap rather than pointers — matches this design exactly.
- **Java:** `LinkedHashMap` with `accessOrder=true` for LRU, or use Caffeine which already implements expireAfterWrite / expireAfterAccess with near-optimal concurrency.
- **Go:** `container/list` + `map[K]*list.Element` + `container/heap`. Guard with `sync.Mutex` or shard.
