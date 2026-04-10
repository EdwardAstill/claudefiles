---
name: rust-expert
description: >
  Rust language expert. Use when writing, debugging, or reviewing Rust code.
  Covers ownership, borrowing, lifetimes, error handling, cargo toolchain,
  and live code introspection via the rust-analyzer LSP.
---

# Rust Expert

Deep Rust knowledge — ownership model, type system, async patterns, cargo
ecosystem, and live LSP introspection via rust-analyzer.

## LSP — rust-analyzer

Always run LSP diagnostics before suggesting changes. rust-analyzer surfaces
borrow checker errors, lifetime issues, unused imports, and type mismatches
with full context — far more useful than reading error output alone.

```
LSP: hover       — type, trait impls, and docs for any expression
LSP: diagnostics — borrow errors, type errors, clippy lints
LSP: definition  — jump to source (including std and deps)
LSP: references  — find all usages
LSP: inlay hints — show inferred types inline
```

Install: `rustup component add rust-analyzer`

## Documentation

- **Crate docs:** docs.rs — WebFetch `https://docs.rs/<crate>/<version>/<crate>/` for any crate
- **std:** doc.rust-lang.org/std — WebFetch for stdlib types and traits
- **context7:** covers popular crates (tokio, serde, axum) — try it first, fall back to docs.rs
- **Version check:** `cf-versions --write` reads `Cargo.toml` and `Cargo.lock`
- **Local docs:** `cargo doc --open` to browse all deps locally

## Toolchain

| Tool | Purpose | Command |
|------|---------|---------|
| `cargo` | Build, test, package manager | `cargo build`, `cargo test`, `cargo add <crate>` |
| `clippy` | Linter — catches real bugs | `cargo clippy -- -D warnings` |
| `rustfmt` | Formatter | `cargo fmt` |
| `rust-analyzer` | LSP | via editor |
| `cargo-watch` | Re-run on file change | `cargo watch -x test` |

## Ownership and Borrowing

**The rules:**
1. Each value has one owner
2. When the owner goes out of scope, the value is dropped
3. You can have many immutable references OR one mutable reference, never both

**Prefer borrowing over cloning** — clone only when you've confirmed ownership transfer isn't possible or isn't worth the complexity.

**Lifetimes** — add lifetime annotations only when the compiler asks for them. Most code doesn't need explicit lifetimes.

## Error Handling

Use `Result<T, E>` everywhere. Never panic in library code.

```rust
// Prefer
fn parse(s: &str) -> Result<u32, ParseError> { ... }

// Use ? to propagate
fn process(input: &str) -> Result<Output, AppError> {
    let n = parse(input)?;
    Ok(transform(n))
}
```

Use `thiserror` for library errors, `anyhow` for application errors.

## Async

Use `tokio` for async runtime. Annotate with `#[tokio::main]`. Prefer `async fn`
over manually constructing futures. Use `tokio::spawn` for concurrent tasks,
`tokio::join!` for parallel awaits.

## Idiomatic Patterns

**Newtype pattern** — wrap primitives to add type safety:
```rust
struct UserId(u64);
```

**Builder pattern** — for structs with many optional fields.

**`impl Trait` in return position** — avoids naming complex types.

**Iterators over loops** — prefer `.map()`, `.filter()`, `.collect()` over manual loops.

## Anti-patterns

| Anti-pattern | Instead |
|-------------|---------|
| `.unwrap()` in production code | Use `?` or handle the error |
| `.clone()` to satisfy borrow checker | Rethink ownership structure |
| `Arc<Mutex<T>>` everywhere | Consider whether shared state is needed |
| Raw pointer manipulation | Use safe abstractions |
| Ignoring clippy warnings | Fix them — they're almost always right |

## Testing

**Unit tests** — co-locate with source in `#[cfg(test)]` modules:
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_valid_input() {
        assert_eq!(parse("42"), Ok(42));
    }

    #[test]
    fn rejects_empty_string() {
        assert!(parse("").is_err());
    }
}
```

**Integration tests** — in `tests/` directory, separate crate:
```
src/lib.rs
tests/
  integration_test.rs   # can only access public API
```

**Run:**
```bash
cargo test                        # all tests
cargo test test_name              # filter by name
cargo test -- --nocapture         # show println! output
```

**cargo-nextest** (faster, better output):
```bash
cargo install cargo-nextest
cargo nextest run
```

## Package Management

**Add dependencies:**
```bash
cargo add serde --features derive   # add with features
cargo add tokio --features full     # async runtime
cargo add --dev proptest            # dev-only dep
```

**Workspace (monorepo):**
```toml
# Cargo.toml at root
[workspace]
members = ["crates/*"]
resolver = "2"
```

**Features** — gate optional functionality:
```toml
[features]
default = ["std"]
std = []
async = ["dep:tokio"]
```

**Lock file:** `Cargo.lock` — commit for binaries, gitignore for libraries.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `.unwrap()` in production | Use `?` to propagate, or handle the error explicitly |
| `.clone()` to appease borrow checker | Rethink ownership — clone is often a design smell |
| `Arc<Mutex<T>>` as default shared state | Consider channels or ownership transfer first |
| Ignoring clippy warnings | Fix them — `cargo clippy -- -D warnings` in CI |
| `impl` blocks scattered across files | Group all `impl Foo` in one place |
| Returning `Box<dyn Error>` from lib | Define a proper error type with `thiserror` |

## Outputs

- Clippy-clean, rustfmt-formatted code
- LSP diagnostics report for any file reviewed
- `Cargo.toml` with appropriate dependencies if scaffolding
