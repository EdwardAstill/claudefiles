# Optimal Parallel Execution Order for a DAG of Build Tasks

## Problem Statement

Given a Directed Acyclic Graph (DAG) of build tasks where each task has a known duration and a set of dependencies, find an execution schedule that minimizes total build time (the makespan) when tasks can run in parallel on unlimited processors.

## Key Insight

This is the **critical path scheduling** problem. The minimum possible build time equals the length of the **critical path** -- the longest weighted path from any source to any sink in the DAG. No amount of parallelism can reduce the total time below this bound, since every task on the critical path must execute sequentially.

## Algorithm: Critical Path Method (CPM) with Topological Scheduling

### Step 1: Topological Sort

Compute a topological ordering of tasks so that every task appears after all of its dependencies. Use Kahn's algorithm (BFS-based) since it naturally produces execution "levels" suitable for parallel scheduling.

### Step 2: Compute Earliest Start Times (Forward Pass)

For each task in topological order, compute the earliest time it can begin:

```
earliest_start[task] = max(earliest_start[dep] + duration[dep]) for all dependencies dep of task
```

For tasks with no dependencies: `earliest_start[task] = 0`.

The **makespan** (minimum total build time) is:

```
makespan = max(earliest_start[task] + duration[task]) for all tasks
```

### Step 3: Compute Latest Start Times (Backward Pass)

Working in reverse topological order:

```
latest_start[task] = min(latest_start[successor] - duration[task]) for all successors of task
```

For tasks with no successors: `latest_start[task] = makespan - duration[task]`.

### Step 4: Identify the Critical Path

A task is on the critical path if and only if:

```
earliest_start[task] == latest_start[task]
```

These tasks have zero **slack** (also called float). Any delay in a critical-path task delays the entire build.

### Step 5: Build the Parallel Schedule

Group tasks into execution waves. A task is ready to execute as soon as all its dependencies have completed. The schedule follows naturally from the earliest start times:

- At time `t`, launch all tasks whose `earliest_start[task] == t` and whose dependencies have finished.
- When a task finishes, check if any new tasks have become unblocked.

## Complete Implementation (Python)

```python
from collections import deque, defaultdict

def optimal_parallel_schedule(tasks, durations, dependencies):
    """
    Compute the optimal parallel execution schedule for a DAG of build tasks.

    Args:
        tasks: list of task identifiers (e.g., ["A", "B", "C", ...])
        durations: dict mapping task -> duration (e.g., {"A": 3, "B": 2, ...})
        dependencies: dict mapping task -> list of prerequisite tasks
                      (e.g., {"C": ["A", "B"]} means C depends on A and B)

    Returns:
        schedule: list of (start_time, task) pairs sorted by start time
        makespan: total build time
        critical_path: list of tasks on the critical path
    """
    # Build adjacency list and in-degree count
    successors = defaultdict(list)
    in_degree = {t: 0 for t in tasks}
    for task in tasks:
        for dep in dependencies.get(task, []):
            successors[dep].append(task)
            in_degree[task] += 1

    # --- Forward pass: earliest start times via Kahn's algorithm ---
    earliest_start = {}
    queue = deque()
    for t in tasks:
        if in_degree[t] == 0:
            earliest_start[t] = 0
            queue.append(t)

    topo_order = []
    while queue:
        task = queue.popleft()
        topo_order.append(task)
        for succ in successors[task]:
            candidate = earliest_start[task] + durations[task]
            if succ not in earliest_start or candidate > earliest_start[succ]:
                earliest_start[succ] = candidate
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)

    if len(topo_order) != len(tasks):
        raise ValueError("Cycle detected in the dependency graph -- not a DAG")

    # Makespan
    makespan = max(earliest_start[t] + durations[t] for t in tasks)

    # --- Backward pass: latest start times ---
    latest_start = {}
    for t in reversed(topo_order):
        if not successors[t]:
            latest_start[t] = makespan - durations[t]
        else:
            latest_start[t] = min(
                latest_start[succ] - durations[t] for succ in successors[t]
            )

    # --- Identify critical path ---
    slack = {t: latest_start[t] - earliest_start[t] for t in tasks}
    critical_tasks = [t for t in topo_order if slack[t] == 0]

    # --- Build schedule ---
    schedule = sorted((earliest_start[t], t) for t in tasks)

    return schedule, makespan, critical_tasks


# ---------- Example ----------

tasks = ["A", "B", "C", "D", "E", "F"]
durations = {"A": 3, "B": 2, "C": 4, "D": 1, "E": 5, "F": 2}
dependencies = {
    "A": [],
    "B": [],
    "C": ["A"],
    "D": ["A", "B"],
    "E": ["C"],
    "F": ["D"],
}

schedule, makespan, critical_path = optimal_parallel_schedule(
    tasks, durations, dependencies
)

print("Parallel Execution Schedule:")
print(f"{'Start':>6}  {'Task':>5}  {'Duration':>8}  {'End':>4}")
print("-" * 30)
for start, task in schedule:
    end = start + durations[task]
    marker = " *" if task in critical_path else ""
    print(f"{start:>6}  {task:>5}  {durations[task]:>8}  {end:>4}{marker}")

print(f"\nTotal build time (makespan): {makespan}")
print(f"Critical path: {' -> '.join(critical_path)}")
```

### Example Output

```
Parallel Execution Schedule:
 Start   Task  Duration   End
------------------------------
     0      A         3     3  *
     0      B         2     2
     3      C         4     7  *
     3      D         1     4
     7      E         5    12  *
     4      F         2     6

Total build time (makespan): 12
Critical path: A -> C -> E
```

The DAG looks like this (durations in parentheses):

```
A(3) -----> C(4) -----> E(5)
  \                        
   \---> D(1) ----> F(2)  
        /                  
B(2) --/                   
```

Tasks A and B start in parallel at time 0. Once A finishes at time 3, both C and D can start. E begins after C completes at time 7 and finishes at time 12. The critical path A -> C -> E determines the makespan of 12.

## Complexity Analysis

| Operation | Time Complexity | Space Complexity |
|---|---|---|
| Topological sort (Kahn's) | O(V + E) | O(V + E) |
| Forward pass (earliest start) | O(V + E) | O(V) |
| Backward pass (latest start) | O(V + E) | O(V) |
| **Total** | **O(V + E)** | **O(V + E)** |

Where V = number of tasks and E = number of dependency edges.

## Handling Limited Parallelism

The solution above assumes unlimited parallel workers. If you have a **fixed number of processors P**, the problem becomes NP-hard in general (it reduces to multiprocessor scheduling). Practical approaches for that case:

1. **List Scheduling Heuristic**: Sort tasks by their critical-path priority (longest remaining path to any sink). When a processor becomes free, assign it the highest-priority ready task. This gives a schedule within a factor of (4/3 - 1/(3P)) of optimal.

2. **Hu's Algorithm**: If all tasks have unit duration and the DAG is a forest (tree-shaped dependencies), Hu's algorithm produces an optimal schedule in O(V + E).

3. **ILP / Constraint Programming**: For exact solutions with limited processors, formulate as an integer linear program or use a CP-SAT solver (e.g., Google OR-Tools).

## Practical Considerations for Build Systems

- **Dynamic durations**: If task durations vary between runs, use recent historical averages or P90 estimates.
- **Resource constraints**: Some tasks may need specific resources (e.g., GPU, network). Model these as additional resource-capacity constraints.
- **Incremental builds**: Prune unchanged tasks from the DAG before scheduling -- only rebuild tasks whose inputs have changed.
- **Real build tools**: Systems like Bazel, Ninja, and Make already implement variants of this algorithm internally. If you are building a custom scheduler, the CPM approach above is the standard foundation.

## Summary

The optimal parallel execution order for a DAG of build tasks is determined by the **Critical Path Method**:

1. Topologically sort the tasks.
2. Forward pass to compute earliest start times.
3. Backward pass to compute latest start times and identify the critical path.
4. Schedule each task at its earliest start time.

The algorithm runs in **O(V + E)** time and produces a schedule whose makespan equals the critical path length -- the theoretical minimum.
