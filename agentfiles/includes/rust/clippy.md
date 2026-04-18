---
name: rust/clippy
---

# Clippy — Invocations and Interpretation

Clippy is not optional. Most of its lints surface real bugs, not style
nits. Run it before every commit and treat warnings as errors in CI.

## Canonical invocations

```bash
cargo clippy --all-targets --all-features         # lint everything
cargo clippy --all-targets -- -D warnings         # fail on any warning
cargo clippy --fix --allow-dirty --allow-staged   # auto-fix safe lints
cargo clippy --workspace --all-targets            # multi-crate workspace
```

`--all-targets` covers tests, benches, and examples — which is where the
worst `unwrap()`s hide. `-D warnings` is how you gate CI; do not rely on
exit codes alone without it.

## Lint groups you should care about

- **`clippy::correctness`** — almost certainly a bug. Fix these first.
- **`clippy::suspicious`** — likely a bug. Fix before shipping.
- **`clippy::perf`** — real performance wins (e.g. `collect::<Vec<_>>` then
  iterate again).
- **`clippy::complexity`** — simplifications that also tend to be correct.
- **`clippy::style`** — idiom nits. Accept most; push back on the rest with
  a targeted `#[allow(...)]` plus a comment.
- **`clippy::pedantic`** — opt-in. Useful on libraries. Noisy on apps.
- **`clippy::nursery`** — experimental, can churn. Enable case-by-case.

Project-level config in `Cargo.toml`:

```toml
[lints.clippy]
pedantic = { level = "warn", priority = -1 }
missing_errors_doc = "allow"
module_name_repetitions = "allow"
```

Use negative priority so the group sits below individual overrides.

## Interpreting common lints

| Lint                              | Usually means                                         |
|-----------------------------------|-------------------------------------------------------|
| `clippy::unwrap_used`             | Production `.unwrap()` — replace with `?` or `expect` |
| `clippy::needless_clone`          | You took ownership you didn't need                    |
| `clippy::needless_collect`        | Drop the `.collect()`, keep the iterator              |
| `clippy::redundant_closure`       | Pass the function directly: `.map(f)` not `.map(\|x\| f(x))` |
| `clippy::needless_pass_by_value`  | Take `&T`, not `T`, when you don't need ownership     |
| `clippy::match_wildcard_for_single_variants` | Spell out the variants, don't `_ =>` real cases |
| `clippy::large_enum_variant`      | Box the big variant to keep the enum small            |

If you disagree with a lint:

```rust
#[allow(clippy::too_many_arguments)] // TODO: refactor in PR #456
fn big_fn(...) { ... }
```

Always attach a one-line reason. Silent `#[allow]` is a code smell.

## Clippy + rustfmt + rust-analyzer

- Run `cargo fmt` before `cargo clippy`. Formatting changes suppress some
  clippy false positives around whitespace.
- `rust-analyzer` runs clippy on save via
  `"rust-analyzer.check.command": "clippy"`. Turn it on — instant feedback
  is the whole point.
- In CI: `cargo fmt --check && cargo clippy --all-targets -- -D warnings
  && cargo test`. In that order.

## Outputs expected from skills using clippy

- `cargo clippy --all-targets -- -D warnings` clean.
- `rustfmt` clean.
- Any `#[allow(clippy::...)]` carries a justification comment.
