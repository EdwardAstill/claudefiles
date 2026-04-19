# Research: Rust vs Go for a High-Traffic API Gateway / Network Proxy

**Depth level:** Standard. If you want a deep-dive with per-benchmark breakdowns and hiring-pool analysis, ask.

## Claim-Type Audit

| Claim | Type | Weight |
|---|---|---|
| "Rust is 10x faster than Go" | Marketing / selective benchmarks | Low |
| "Discord saw 10x memory and 5x tail latency improvement" | Single production case study | Moderate (one data point, well-documented) |
| "No-GC means lower tail latency" | Architectural principle | High (this is mechanistic, not benchmark-dependent) |
| "Rust developer velocity is worse" | Community consensus + experience reports | Moderate-high |
| "Go's GC is fine" | Contextual engineering claim | Moderate |
| "Cloudflare Pingora handles ~1T req/day in Rust" | Production case | Moderate-high |

## Consensus

**Strong consensus (high confidence):**
- **Rust has a real, architectural tail-latency advantage** because there is no garbage collector. Go's GC produces stop-the-world pauses that show up in p99 and especially p99.9.
- **Go has a real developer-velocity advantage.** Faster compile times, simpler concurrency model (goroutines vs async Rust's Send/Sync/Pin/lifetime interactions), easier hiring.
- **Average throughput is comparable.** For typical request-response HTTP workloads, Go and Rust are within 20-50% on throughput in most benchmarks; the dominant factor is usually the framework, not the language.

**Moderate consensus:**
- **Rust uses 2-4x less memory** for equivalent network services (consistent across Discord, Figma, 1Password reports and TechEmpower).
- **Rust's async ecosystem (Tokio/Hyper/Tonic) has closed much of the maturity gap with Go's net/http** over 2023-2026 but is still less polished for some cloud-native workflows.

**Contested:**
- The "crossover point" at which Rust's latency win justifies its development cost.
- Whether long-term Rust productivity reaches Go's — some reports say yes after 6-12 months, others say no.

## Nuances

### Where Rust's advantage is real

1. **Tail latency under load** (p99, p99.9). No GC pauses. Discord 2020's "Why Discord is switching from Go to Rust" reports ~5x tail-latency reduction; Cloudflare's Pingora (Rust) replaced their nginx deployment and handles ~1T req/day.
2. **Memory footprint**. Typical network service: Rust 50-80 MB, Go 100-320 MB. 2-4x is a realistic multiplier, not marketing.
3. **CPU efficiency under high load**. Zero-cost abstractions, monomorphization, no runtime.
4. **Correctness at compile time** for concurrent code (Send/Sync prevent entire classes of data races).

### Where Rust's advantage is overstated

1. **Average throughput**. "Rust is N times faster than Go" benchmarks are usually (a) synthetic hot loops (Rust wins big), (b) HTTP servers (Rust wins by 20-50%, not 10x). Pick your benchmark.
2. **Long-term developer productivity**. After 6-12 months, experienced Rust teams ship reasonably fast — but onboarding remains expensive.
3. **Cloud-native ecosystem**. Go's lead in k8s/CNCF tooling, gRPC, protobuf, operators is genuine and has not closed as fast as people predicted.
4. **"Memory safety" as a differentiator vs Go**. Go is also memory-safe (GC). The difference is unsafe-FFI ergonomics and data-race prevention, not memory safety per se.

### Where Go genuinely wins

1. **Developer velocity.** Productive in ~1 week, proficient in ~1 month. Rust: productive in ~1 month, proficient in ~3-6 months.
2. **Compile times.** Go sub-second incremental; Rust 10-60s typical even with mold/sccache. Matters for inner loop and CI costs.
3. **Cloud-native ecosystem.** Most of CNCF is Go. k8s operators, CRDs, prometheus exporters, protobuf tooling — all first-class in Go.
4. **Hiring pool.** Go has 5-10x more job-ready engineers than Rust in 2026 in most markets.
5. **Error handling and readability for typical service code.** Rust's `Result` is powerful; Go's `if err != nil` is boring but consistent and scannable.
6. **Goroutines are simpler than async Rust.** The Send/Sync/Pin/'static interaction in async Rust is a real cognitive cost.

### Where Go loses

1. **GC tail-latency spikes** under high load, especially with large heaps.
2. **Weaker type system.** No sum types (until generics + interface tricks), nil pointer panics, interface-value-is-nil gotcha.
3. **Error handling verbosity** compounds in hot paths with many fallible calls.
4. **Goroutine leaks** are easy to introduce and hard to diagnose.

## Known Pitfalls

### If you pick Rust
- Compile time on CI/CD becomes a real cost; budget for mold, sccache, and potentially remote-cache infrastructure.
- Async Rust Send/Sync across .await is a real ongoing cost, not a one-time onboarding hit.
- Premature generics / trait abstraction is common; encourage concrete code first.
- Cargo dependency depth can be large — supply-chain discipline required.
- Ownership can push bad designs (arc-and-mutex-everywhere) when the team is still learning.
- Hiring in non-SF/NY markets is harder and more expensive.

### If you pick Go
- GC tuning (GOGC, GOMEMLIMIT) becomes your problem under load; know when you need it.
- Nil pointer panics and the interface-nil gotcha recur.
- Goroutine leaks — enforce context cancellation and bounded concurrency.
- Error handling noise can hide logic; code-review discipline matters.
- Interface pollution / over-abstraction — common style drift.
- Generics are new (1.18+) and some libraries haven't adopted them cleanly.

## Contradictions / Open Questions

| Disagreement | Why |
|---|---|
| Discord: "Go was unacceptable, Rust fixed it." Many others: "Go is fine." | Discord's workload was cache-heavy with millions of small objects — the adversarial case for Go's GC. Most workloads aren't that. |
| TechEmpower: Rust frameworks dominate. Real-world: Go is ubiquitous. | Benchmarks optimize for JSON-serialization hot loops. Real services are bottlenecked on I/O, DB, upstreams. |
| "Rust is slow to write." vs "After 6 months you're as fast as Go." | Depends heavily on what you're writing. CRUD code: Rust catches up. Novel concurrent code: Rust stays slower longer. |
| Actix-web vs Axum vs Hyper debate within Rust. | Framework choice has larger performance impact than language choice in most benchmarks. |

## Recommended Direction

**The right answer depends on your p99 budget:**

- **Sub-millisecond tail latency target + CPU-bound work** → Rust. Cloudflare Pingora is the reference architecture. This is the one case where the cost is clearly worth it.
- **p99 target of 5-50 ms + I/O-bound on upstreams** → Go. GC pauses are below measurement noise; Go's ecosystem and velocity win. Almost all API gateways live here.
- **Unsure** → prototype the hot path in both, measure on your actual workload, decide with data.

### Polyglot is increasingly the correct answer

The 2026 trend isn't Rust-vs-Go; it's both-in-their-lane. Go for control plane, orchestration, high-level services; Rust for the data-plane hot paths, proxies, inference. Don't force a mono-language choice when the workload is heterogeneous.

### Steelman alternatives
- **Rust when Go is "good enough":** correct if you have engineers who want to learn it AND you can afford the 3-6 month ramp; wrong if you're picking it for resume reasons. Flag resume-driven architecture explicitly.
- **Go when Rust would be better:** correct for 80% of API gateways; wrong when you have a genuinely sub-ms SLO, or when you're going to spend the next 5 years fighting GC tuning.
- **C++ or Zig:** not mainstream for this decision but real options; C++ when you need mature ecosystems like Envoy; Zig if you want C-level control with better ergonomics and are comfortable with an immature ecosystem.

## Source Quality Note

- **Strongest evidence:** Production case studies (Discord, Cloudflare Pingora, Figma, Dropbox) — these describe real workloads with before/after numbers.
- **Moderate evidence:** TechEmpower benchmarks — useful for directional comparison but heavily contested as representative of production workloads.
- **Weakest evidence:** Medium blog posts citing "5x latency wins" without methodology. Treat specific multipliers as illustrative of direction, not magnitude.
- **Near-absent:** Peer-reviewed performance research on the exact decision. Mostly vendor and practitioner reporting.

## Further Investigation

- Define your actual p99 SLO. If you don't have one, the decision is premature.
- Prototype the hot path in both languages with your expected traffic pattern. Two weeks per side is usually enough to tell.
- Count your team's Rust-experienced engineers. If zero, budget 6+ months ramp.
- Read **Cloudflare's Pingora blog post** (2022) as the reference architecture for Rust-for-proxies.
- Read **Discord's "Why we switched to Rust" (2020)** and **their followups** for the canonical case.
- Read **Dropbox's Go adoption (Magic Pocket)** and their later selective Rust adoption for the pragmatic path.
- Review **TechEmpower methodology** before citing its benchmarks — understand what's being measured.

**Confidence summary:**
- "Rust has lower tail latency" → strong confidence (mechanistic + confirmed production).
- "Go has better developer velocity" → strong confidence.
- "Rust saves 2-4x memory" → moderate-strong confidence.
- "Specific multipliers (10x, 5x) apply to your workload" → low confidence; depends entirely on your workload shape.
- "Rust ecosystem has caught up to Go for cloud-native" → weak; still behind in 2026.
