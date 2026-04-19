# Rust vs Go for an API Gateway / Network Proxy

Both are strong choices. The honest answer is: Rust wins on tail latency and memory, Go wins on velocity and ecosystem, and the right choice depends on your p99 budget more than on any language-level comparison.

## Performance: what the numbers actually show

**Average throughput**: comparable. In most HTTP benchmarks (TechEmpower, etc.) Rust frameworks like Actix-web or Axum are 20-50% faster than Go's Fiber or stdlib net/http, not 10x. The popular "Rust is 10x faster" claim comes from synthetic CPU-bound microbenchmarks, not HTTP serving.

**Tail latency (p99, p99.9)**: this is where Rust has a real advantage. Go's GC causes stop-the-world pauses that show up in the tail. Discord's 2020 migration report showed ~5x tail latency reduction. Cloudflare's Pingora (Rust replacement for nginx, ~1T req/day) is built around this advantage. The architectural reason — no GC — is solid, not benchmark-dependent.

**Memory**: Rust services typically use 50-80 MB vs Go's 100-320 MB. 2-4x less memory is a consistent finding.

## Where Rust's advantage is overstated

- "10x faster" — misleading for HTTP workloads; true only for CPU-bound microbenchmarks.
- "Memory safety over Go" — Go is also memory safe. The difference is data-race prevention and unsafe-FFI ergonomics.
- "Async Rust is mature now" — the Send/Sync/Pin/lifetime interactions are real ongoing cognitive cost, not just onboarding.
- "Cloud-native ecosystem has caught up" — it hasn't; most of k8s/CNCF is still Go-first.

## Where Go genuinely wins

- **Developer velocity**: productive in ~1 week, proficient in ~1 month. Rust is more like 1 month to productive, 3-6 to proficient.
- **Compile times**: Go sub-second incremental; Rust 10-60s even with mold/sccache.
- **Cloud-native ecosystem**: k8s, operators, prometheus, protobuf — all Go-first.
- **Hiring pool**: roughly 5-10x more Go engineers than Rust in 2026.
- **Goroutines are simpler than async Rust** — real concurrency productivity advantage for typical services.

## Where Go loses

- GC tail-latency spikes under load.
- No sum types, nil-pointer panics, interface-nil gotchas.
- Verbose error handling can hide logic in hot paths.
- Goroutine leaks are common and hard to diagnose.

## Production case studies worth knowing

- **Discord 2020**: Go → Rust on a read-heavy cache service; reported 10x memory and 5x tail latency improvement. Adversarial case for Go's GC (millions of small cached objects).
- **Cloudflare Pingora (2022)**: Rust replaces nginx; handles ~1T req/day; the reference architecture for Rust-as-proxy.
- **Figma, 1Password**: smaller but similar stories on Rust for performance-critical paths.
- **Dropbox Magic Pocket**: went to Go for storage. Later added Rust for performance-critical pieces. Pragmatic polyglot.

## How to decide for your gateway

Ask yourself what your p99 target is:

- **Sub-millisecond p99 + CPU-bound**: Rust. This is where the architectural win is clear.
- **5-50 ms p99 + I/O-bound on upstreams**: Go is fine. GC pauses will be below measurement noise. This is where most API gateways actually live.
- **Don't know yet**: prototype both on your actual workload. Two weeks per side usually decides it.

## Failure modes to budget for

**Rust:**
- CI compile time becomes infrastructure work.
- Async Send/Sync across .await is ongoing friction, not one-time.
- Premature generics/trait abstractions common early on.
- Hiring is harder.

**Go:**
- GC tuning (GOGC, GOMEMLIMIT) becomes your problem under load.
- Interface pollution and over-abstraction.
- Goroutine leaks — enforce context propagation.

## The polyglot option

The 2026 trend isn't choosing one — it's using Go for control plane / orchestration / most services, and Rust for data-plane hot paths (proxies, inference). Consider whether you actually have to pick.

## Honesty on source quality

Specific numbers (5x, 10x) come from blog posts about specific workloads. TechEmpower is directional at best. The strongest signals are production case studies and the architectural reasoning (GC vs no-GC). Peer-reviewed research on this decision is sparse.

## Recommendation

For a typical API gateway where you need low-to-moderate tail latency and good throughput: **Go is the pragmatic choice**. Pingora-level use cases where sub-ms p99 is real: **Rust**. Don't pick Rust for resume reasons; don't pick Go because you've always used Go. Measure your actual requirement first.
