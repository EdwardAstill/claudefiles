---
name: performance-profiling
description: >
  Use when code is correct but too slow or memory-hungry, and you need to
  find the real bottleneck with measurement. Trigger phrases: "this is
  slow — where's the bottleneck", "profile this with py-spy / perf",
  "generate a flamegraph", "memory is growing over time — leak",
  "latency p99 is too high", "benchmark before and after", "CPU pegged
  at 100%", "this endpoint got slower after the change", "is this
  algorithm the bottleneck or is it IO", "establish a perf baseline".
  Covers profiling tools, flamegraph reading, allocation profiling, and
  benchmark-driven optimization. Do NOT use when code is incorrect (use
  systematic-debugging first), for slow SQL (use database-expert), for
  slow CI builds (use github-actions-expert), or for algorithmic
  redesign once the hotspot is found (use dsa-expert).
---

# Performance Profiling

Systematic performance optimization driven by measurement, not intuition.
Finds actual bottlenecks instead of optimizing what you assume is slow.

**Core principle:** Measure before optimizing. Intuition about performance is
wrong more often than it is right.

## When to Use

- Code is functionally correct but doesn't meet performance requirements
- Response times or throughput have degraded after a change
- Memory usage is growing unexpectedly (potential leaks)
- Need to establish performance baselines before a change
- Choosing between algorithmic approaches with different complexity
- Production profiling to diagnose live performance issues

## When NOT to Use

- **Code is incorrect** — fix bugs first with `systematic-debugging`
- **Database queries are slow** — use `database-expert` for query optimization
- **Build/CI is slow** — use `github-actions-expert` for CI pipeline optimization
- **Premature optimization** — if there is no measured problem, don't optimize

## The Iron Law

```
NO OPTIMIZATION WITHOUT A PROFILE FIRST
```

If you haven't profiled, you don't know what's slow. Period.

## Process

### Phase 1: Establish Baseline

1. **Define the metric** — what are you measuring? Latency (p50/p95/p99), throughput (req/s), memory (peak/resident), startup time
2. **Create a reproducible benchmark** — same input, same environment, multiple runs
3. **Record the baseline** — actual numbers, not "it feels slow"
4. **Set the target** — what number constitutes "fast enough"?

```bash
# Python: simple timing
uv run python -m timeit -s "from module import func" "func(data)"

# Rust: cargo bench (criterion)
cargo bench

# Node.js: built-in perf hooks
node --prof app.js && node --prof-process isolate-*.log
```

### Phase 2: Profile

Choose the right profiler for the bottleneck type:

| Bottleneck Type | Tool | Command |
|----------------|------|---------|
| CPU (Python) | py-spy | `py-spy record -o profile.svg -- python app.py` |
| CPU (Rust/C) | perf + flamegraph | `perf record ./app && flamegraph --perfdata perf.data` |
| CPU (Node.js) | clinic.js | `npx clinic flame -- node app.js` |
| Memory (Python) | memray | `python -m memray run app.py` |
| Memory (Rust) | DHAT (valgrind) | `valgrind --tool=dhat ./target/debug/app` |
| Memory (Node.js) | heapdump | `node --inspect app.js` → Chrome DevTools |
| I/O blocking | strace/ltrace | `strace -e trace=read,write -c ./app` |
| Async (Python) | py-spy | `py-spy record --native -- python async_app.py` |
| General (any) | Flamegraph | Visual call-stack frequency analysis |

### Phase 3: Analyze

1. **Read the flamegraph** — widest bars are where time is spent, not deepest stacks
2. **Identify the hot path** — which function/method consumes the most time?
3. **Check algorithmic complexity** — is the hot path O(n^2) when it could be O(n)?
4. **Look for allocation pressure** — excessive object creation in tight loops
5. **Check I/O patterns** — synchronous I/O blocking the event loop or main thread

### Phase 4: Optimize (One Thing at a Time)

1. **Pick the single biggest bottleneck** from the profile
2. **Form a hypothesis** — "Changing X will reduce time by approximately Y%"
3. **Implement the change** — one optimization at a time
4. **Re-profile** — did the number actually improve?
5. **If no improvement** — revert and pick the next bottleneck
6. **Repeat** until target is met or gains are marginal

### Common Optimization Strategies

| Strategy | When to Use |
|----------|-------------|
| **Algorithm change** (O(n^2) → O(n log n)) | Hot path has unnecessary complexity |
| **Caching / memoization** | Same computation repeated with same inputs |
| **Batch I/O** | Many small reads/writes → fewer large ones |
| **Lazy evaluation** | Computing values that may not be needed |
| **Data structure change** | List search → hashmap lookup |
| **Connection pooling** | Opening new connections per request |
| **Async / concurrency** | I/O-bound work blocking CPU-bound work |
| **Reduce allocations** | Object churn in tight loops |

## Memory Profiling

Memory issues are distinct from CPU issues. Profile them separately.

**Leak detection pattern:**
1. Take heap snapshot at time T1
2. Run workload
3. Take heap snapshot at time T2
4. Compare — objects that grow without bound are leaks

**Common memory leaks:**
- Event listeners not removed
- Caches without eviction policy (grows forever)
- Closures capturing large objects
- Circular references preventing GC (in reference-counted languages)

## Anti-patterns

| Anti-pattern | Why It's Wrong | Instead |
|-------------|---------------|---------|
| Optimizing without profiling | You'll optimize the wrong thing | Profile first, always |
| Optimizing "just in case" | Premature optimization, wasted effort | Optimize when measured need exists |
| Multiple optimizations at once | Can't attribute improvement | One change, re-measure, repeat |
| Micro-benchmarks for macro decisions | Loop timing doesn't reflect real workload | Benchmark realistic scenarios |
| Caching everything | Memory bloat, stale data bugs | Cache only measured hot paths |
| "Rewrite in X language" as first step | Usually algorithmic, not language-bound | Fix the algorithm first |
| Ignoring p99 latency | Tail latency affects real users | Measure and optimize percentiles |
| Optimizing cold paths | Negligible impact on total time | Focus on the hot path only |

## Tools

| Tool | Language | Purpose |
|------|----------|---------|
| `py-spy` | Python | Sampling profiler, flamegraphs |
| `memray` | Python | Memory profiler with flamegraphs |
| `perf` | Linux (any) | System-level CPU profiling |
| `flamegraph` | Any | Flamegraph generation from perf data |
| `criterion` | Rust | Statistical benchmarking |
| `clinic.js` | Node.js | Flamegraph and event loop profiling |
| `Instruments` | macOS (any) | Time Profiler, Allocations |
| `hyperfine` | CLI (any) | Command-line benchmarking with statistics |
| `vegeta` | HTTP | HTTP load testing |
| `wrk` | HTTP | HTTP benchmarking |

## Outputs

- Baseline performance numbers with environment details
- Profiling results (flamegraph SVG, memory timeline)
- Bottleneck identification with evidence
- Optimization applied with before/after measurements
- Chain into `tdd` for regression benchmarks, `verification-before-completion` to confirm
