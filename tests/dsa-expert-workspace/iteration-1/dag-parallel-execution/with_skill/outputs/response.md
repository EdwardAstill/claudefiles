# DAG Parallel Build Execution: Optimal Scheduling with Known Task Durations

## Step 1: Understand the Problem

### Constraint Summary

**What operations are needed?**
- Parse a DAG of build tasks with directed edges representing dependencies (A -> B means A must complete before B can start)
- Determine which tasks can run in parallel at any given point
- Compute a schedule that minimizes the total wall-clock build time (the makespan) given unlimited parallelism, or adapt to bounded parallelism (P processors)
- Each task has a known, fixed duration (weight)

**What are the frequency and size characteristics?**
- Typical build graphs range from tens to thousands of tasks
- The graph is constructed once and traversed once per build invocation (not a hot loop)
- Read-heavy in the sense that we build the graph, then query it; we do not mutate it during scheduling

**What are the hard constraints?**
- The graph must be a DAG (no cycles) -- if cycles exist, the build is invalid
- Dependency ordering must be respected: a task cannot start until all its predecessors have finished
- We want to minimize makespan (wall-clock time from first task start to last task finish)
- With unlimited parallelism, the makespan equals the length of the **critical path** (longest weighted path in the DAG)
- With bounded parallelism (P processors), scheduling is NP-hard in general, but good heuristics exist

**What's already in place?**
- Assumed: a DAG represented as an adjacency list with task durations. No existing scheduling infrastructure.

---

## Step 2: Recommend with Trade-off Analysis

The core question is: what algorithm and data structure combination best solves this?

There are two distinct sub-problems:
1. **Critical Path Analysis** (unlimited parallelism) -- determines the theoretical minimum makespan
2. **Bounded-Parallelism Scheduling** (P processors) -- a practical schedule that respects resource limits

### Option A: Topological Sort + Critical Path Method (CPM)

Use a topological sort to process tasks in dependency order, computing the **earliest start time (EST)** for each task. The makespan is `max(EST[t] + duration[t])` over all tasks. This gives the optimal schedule under unlimited parallelism and also identifies the critical path, which guides prioritization under bounded parallelism.

### Option B: Priority Queue (Heap) Based List Scheduling

Use a min-heap (keyed on earliest-available-time) to model P processors. Tasks are dispatched in priority order (e.g., longest remaining path first) as processors become free. This is the standard approach for bounded-parallelism scheduling.

### Option C: BFS-based Level Scheduling

Group tasks into "levels" by BFS from sources. All tasks at the same level can run in parallel. Simple but suboptimal -- it forces synchronization barriers between levels even when unnecessary.

| Criterion | A: Topo Sort + CPM | B: Heap-based List Scheduling | C: BFS Level Scheduling |
|---|---|---|---|
| Finds optimal makespan (unlimited P) | Yes -- exact | N/A (designed for bounded P) | No -- inserts artificial barriers |
| Handles bounded P | Needs extension | Yes -- directly models P processors | Partially -- respects levels but not durations |
| Time complexity | O(V + E) | O(V log P + E) | O(V + E) |
| Space complexity | O(V + E) | O(V + E + P) | O(V + E) |
| Implementation complexity | Simple | Moderate | Simple |
| Identifies critical path | Yes | No (but can be combined with A) | No |
| Schedule quality (bounded P) | N/A alone | Near-optimal (with CPM priority) | Often suboptimal |

### Recommendation

**Use Option A (Topological Sort + Critical Path Method) as the foundation, extended with Option B (Heap-based List Scheduling) when you have bounded parallelism.**

Reasoning:
- The critical path method gives you the theoretical minimum build time and identifies which tasks are bottlenecks.
- For practical scheduling with P workers, use the critical path lengths as priorities in a heap-based list scheduler. This is known as the **Longest Processing Time / Critical Path** heuristic and produces near-optimal schedules in practice.
- BFS level scheduling (Option C) is strictly inferior because it forces all tasks at a level to complete before the next level begins, wasting parallelism when tasks have different durations.

---

## Step 3: Design the Solution

### High-level Approach

**Topological Sort + Critical Path Method + Priority-based List Scheduling**

1. Compute a topological ordering of the DAG (Kahn's algorithm with in-degree tracking)
2. In reverse topological order, compute the **longest path from each node to any sink** -- this is the node's "critical path length" (CPL), representing how much total work depends on it
3. For unlimited parallelism: the makespan is `max(CPL[t])` over all source tasks (equivalently, the CPL of any virtual start node)
4. For bounded parallelism (P processors): use a min-heap of P processors (keyed by when each becomes free). Dispatch ready tasks in decreasing order of CPL (critical path priority). When a processor finishes a task, check if any new tasks have all dependencies satisfied and add them to the ready queue.

### Invariants

1. **Topological ordering invariant:** A task is only processed after all its predecessors have been processed.
2. **Critical path invariant:** `CPL[t] = duration[t] + max(CPL[s] for s in successors[t])`, with `CPL[t] = duration[t]` for sink nodes (no successors).
3. **Ready queue invariant:** A task enters the ready queue only when its in-degree (count of unfinished predecessors) reaches zero.
4. **Processor heap invariant:** The heap always yields the processor that becomes free earliest, ensuring no processor sits idle when work is available.

### Pseudocode

```
// --- Phase 1: Build the graph and compute in-degrees ---

function build_graph(tasks):
    // tasks is a list of (id, duration, [dependency_ids])
    adj = {}          // adjacency list: task -> list of successors
    rev_adj = {}      // reverse adjacency: task -> list of predecessors
    in_degree = {}
    duration = {}

    for each (id, dur, deps) in tasks:
        duration[id] = dur
        adj[id] = []
        rev_adj[id] = deps
        in_degree[id] = len(deps)
        for dep in deps:
            adj[dep].append(id)

    return adj, rev_adj, in_degree, duration


// --- Phase 2: Topological sort (Kahn's algorithm) ---

function topological_sort(adj, in_degree):
    queue = deque()
    for each node where in_degree[node] == 0:
        queue.push_back(node)

    order = []
    while queue is not empty:
        node = queue.pop_front()
        order.append(node)
        for successor in adj[node]:
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                queue.push_back(successor)

    if len(order) != total_number_of_tasks:
        ERROR: "Cycle detected -- not a valid DAG"

    return order


// --- Phase 3: Compute Critical Path Length (reverse topo order) ---

function compute_critical_path_lengths(adj, duration, topo_order):
    cpl = {}
    // Process in reverse topological order
    for node in reversed(topo_order):
        max_successor_cpl = 0
        for successor in adj[node]:
            max_successor_cpl = max(max_successor_cpl, cpl[successor])
        cpl[node] = duration[node] + max_successor_cpl

    return cpl

    // The overall critical path length (= minimum makespan with unlimited
    // parallelism) is max(cpl[node] for all nodes).
    // The critical path itself can be recovered by following the chain of
    // successors that achieve the maximum at each step.


// --- Phase 4: Schedule with bounded parallelism (P processors) ---

function schedule_tasks(adj, in_degree, duration, cpl, P):
    // in_degree here is a fresh copy, not the one mutated by topo sort
    // Ready queue: max-heap ordered by critical path length (highest priority first)
    ready = max_heap()
    for each node where in_degree[node] == 0:
        ready.push((cpl[node], node))

    // Processor pool: min-heap of (available_time, processor_id)
    processors = min_heap()
    for i in 0..P-1:
        processors.push((0, i))

    schedule = []       // list of (task, processor, start_time, end_time)
    finish_time = {}    // task -> when it finishes

    // We also need: for each task, track how many predecessors are still pending
    pending = copy(in_degree)

    // We also need: earliest time a task CAN start (all deps done)
    // This is max(finish_time[dep] for dep in predecessors[task])
    earliest_start = {}
    for each node:
        if pending[node] == 0:
            earliest_start[node] = 0

    while ready is not empty:
        // Pick the highest-priority ready task
        (priority, task) = ready.pop()

        // Pick the earliest-available processor
        (proc_free_time, proc_id) = processors.pop()

        // Task cannot start before both the processor is free AND all deps are done
        start = max(proc_free_time, earliest_start[task])
        end = start + duration[task]

        schedule.append((task, proc_id, start, end))
        finish_time[task] = end

        // Update processor availability
        processors.push((end, proc_id))

        // Check if any successors are now ready
        for successor in adj[task]:
            pending[successor] -= 1
            // Update earliest possible start for successor
            if successor not in earliest_start:
                earliest_start[successor] = end
            else:
                earliest_start[successor] = max(earliest_start[successor], end)

            if pending[successor] == 0:
                ready.push((cpl[successor], successor))

    makespan = max(end for (_, _, _, end) in schedule)
    return schedule, makespan
```

### Complexity Proof

**Time complexity: O(V + E + V log V)**
- Building the graph: O(V + E) -- iterate over all tasks and edges once.
- Topological sort (Kahn's): O(V + E) -- each node enqueued/dequeued once, each edge relaxed once.
- Critical path computation: O(V + E) -- one pass in reverse topological order, examining each edge once.
- List scheduling: O(V log V + E) in the worst case. Each of the V tasks is inserted into and extracted from the ready max-heap (O(log V) each). The processor heap has at most P entries, so operations on it are O(log P). Each edge is examined once when updating successor dependencies. Since P <= V, this simplifies to O(V log V + E).
- **Total: O(V log V + E)**, dominated by the heap operations in the scheduling phase. For sparse graphs (E ~ V), this is O(V log V). For dense graphs (E ~ V^2), the edge traversal dominates at O(V^2).

**Space complexity: O(V + E)**
- Adjacency list storage: O(V + E)
- In-degree, duration, CPL, finish_time arrays: O(V) each
- Heaps: O(V) for ready queue, O(P) for processor pool
- **Total: O(V + E)**

---

## Step 4: Edge Cases and Correctness

1. **Empty graph (no tasks):** Return makespan = 0 with an empty schedule. The topological sort produces an empty ordering, and the scheduling loop never executes.

2. **Single task:** Trivially scheduled on one processor. Makespan = duration of that task. Critical path = that single task.

3. **Fully sequential chain (A -> B -> C -> ...):** All tasks are on the critical path. No parallelism is possible regardless of the number of processors. Makespan = sum of all durations. The algorithm correctly computes this because each task has in-degree 1 (except the first) and only becomes ready after its predecessor finishes.

4. **Fully parallel (no dependencies):** All tasks are sources with in-degree 0. With unlimited parallelism, makespan = max(duration[t]). With P processors, the algorithm dispatches the P highest-CPL tasks first (which here equals longest individual duration), achieving near-optimal scheduling.

5. **Diamond dependencies (A -> B, A -> C, B -> D, C -> D):** D becomes ready only after both B and C finish. The `earliest_start` tracking ensures D's start time is `max(finish_time[B], finish_time[C])`, not just the finish time of whichever predecessor completes second in scheduling order.

6. **Cycle detection:** If the topological sort produces fewer nodes than exist in the graph, a cycle is present. The algorithm explicitly checks for this and reports an error. Build systems must reject cyclic dependencies.

7. **Tasks with zero duration:** Valid (e.g., phony/meta targets). They are scheduled and complete instantly. The algorithm handles this because `end = start + 0 = start`, and successors become immediately eligible.

8. **Disconnected components:** The DAG may have multiple independent subgraphs (e.g., separate build targets with no shared dependencies). Kahn's algorithm naturally handles this -- all sources from all components are enqueued. The scheduler processes them concurrently across available processors.

9. **Large fan-out / fan-in:** A single task with many successors (fan-out) or a single task with many predecessors (fan-in). The algorithm handles both correctly. Fan-in tasks accumulate `earliest_start` as the max of all predecessor finish times. Fan-out tasks release many successors into the ready queue simultaneously.

10. **P = 1 (single processor):** Degenerates to a sequential schedule. The topological ordering is still respected. The total time will be the sum of all task durations. The critical path priority ensures the most time-sensitive paths are scheduled first, though with P = 1 the total time is fixed regardless of ordering.

11. **Ties in critical path length:** When multiple ready tasks have the same CPL, the tie-breaking strategy does not affect correctness but can affect makespan. Common tie-breakers: highest out-degree (releases more successors), or longest individual duration. The algorithm as written breaks ties arbitrarily, which is acceptable in practice.

---

## Step 5: Language-Specific Handoff Notes

### Python
- `collections.deque` for Kahn's BFS queue (O(1) popleft)
- `heapq` for both the processor min-heap and the ready queue. Since `heapq` is a min-heap only, negate CPL values for the ready queue to simulate a max-heap: push `(-cpl[node], node)` and pop gives the highest CPL
- Adjacency list as `dict[str, list[str]]` or `defaultdict(list)`
- `graphlib.TopologicalSorter` (Python 3.9+) provides a built-in topological sort with a `get_ready()` / `done()` API that directly supports parallel dispatch -- worth considering as an alternative to hand-rolling Kahn's
- `networkx` provides `dag_longest_path_length()` and `topological_sort()` if you want a library-level solution, but adds a heavy dependency

### Rust
- Adjacency list as `Vec<Vec<usize>>` with index-based node IDs for cache-friendly traversal
- `BinaryHeap` for max-heap (ready queue). For the processor min-heap, wrap in `Reverse()` or use `BinaryHeap<Reverse<(u64, usize)>>`
- `VecDeque` for Kahn's BFS queue
- Consider `petgraph` crate for graph data structures -- it provides `toposort()` and is well-optimized
- Ownership is straightforward here since the graph is built once and only read during scheduling. No need for `Rc`/`RefCell` or arena allocation

### TypeScript
- No built-in heap -- use a library like `@datastructures-js/priority-queue` or implement a simple binary heap (the scheduling algorithm critically depends on efficient heap operations)
- `Map<string, string[]>` for adjacency lists
- `Map<string, number>` for duration, CPL, in-degree tracking
- For large build systems in Node.js, consider streaming the results rather than collecting the full schedule in memory
- TypeScript's `Array.prototype.sort()` is not a substitute for a heap in the scheduling loop -- it would degrade the scheduling phase to O(V^2 log V)
