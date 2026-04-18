# LRU Cache with TTL

For an LRU cache with per-key TTL, you combine a hash map with a doubly linked list (the standard LRU pattern), and add some mechanism to track expiration times.

## Core Data Structures

You need three pieces:

1. **Hash map** (`key -> node`) for O(1) lookup.
2. **Doubly linked list** for O(1) LRU ordering — move to head on access, evict from tail.
3. **Something to handle TTL.** Options:
   - Store `expiry_time` on each node and check it lazily on get/put.
   - A min-heap keyed by expiry time, so a background task can periodically pop expired entries.
   - A sorted set / tree keyed by expiry time.

The typical design is: hashmap + DLL + min-heap.

## Operations

**get(key):**
- Look up in the hashmap.
- If the entry's expiry has passed, remove it and return miss.
- Otherwise move to front of the list and return the value.

**put(key, value, ttl_seconds):**
- Compute `expiry = now + ttl_seconds`.
- If key exists: update value and expiry, move node to front, push new entry into the expiry heap.
- If key doesn't exist: if at capacity, evict the LRU (tail) entry. Create node, insert at head, add to hashmap, push to expiry heap.

**delete(key):**
- Remove from hashmap, unlink from DLL. You can mark the heap entry as deleted or just skip it on cleanup.

## Eager vs Lazy Expiration

- **Lazy:** Check expiry only when the key is accessed. Simple, no extra thread, but expired entries stay in the cache until they're touched or pushed out by LRU, using memory.
- **Eager:** Background thread pops from the min-heap whenever `top.expiry <= now` and evicts. Keeps memory tight but adds CPU and thread-safety complexity.

A common approach is a hybrid — lazy on access plus a periodic cleanup.

## Memory Overhead

Per entry you're paying for:
- The node (key, value, expiry, prev pointer, next pointer).
- The hashmap entry.
- The heap entry (expiry, key).

Roughly 3 extra pointers per entry beyond the raw key/value.

## Thread Safety

Options:
- Global mutex — simple but contended.
- Shard the cache into N independent LRUs keyed by hash — scales nicely.
- Lock-free approaches exist but are complex (Caffeine in Java uses access-recording buffers with async drain).

## Edge Cases

- TTL = 0 — immediate expiry.
- Repeated puts of same key with different TTLs — need to invalidate old heap entries (version number or tombstone).
- Capacity = 1.
- All entries expire at once — eviction pass walks the list.
- Clock issues in distributed settings.

## Complexity

- get: O(1) average.
- put: O(1) amortized if you batch heap operations, otherwise O(log n) for the heap push.
- delete: O(1) from hashmap, heap entry lazily cleaned.
