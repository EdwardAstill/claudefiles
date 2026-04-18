---
name: typescript-expert
description: >
  TypeScript toolchain and conventions specialist. Use when you need
  typescript-language-server LSP diagnostics, bun/npm tooling, biome linting,
  or strict typing patterns — the tooling integration the base model doesn't
  enforce. Covers strict typing, generics, type narrowing, bun/npm tooling,
  and live code introspection via the typescript-language-server LSP.
includes:
  - typescript/tsc-strict
---

# TypeScript Expert

Deep TypeScript knowledge — strict type system, modern patterns, runtime tooling,
and live LSP introspection. Uses typescript-language-server for type analysis and
context7 for package docs (best coverage of any language in the suite). Strict
`tsconfig.json` flags, forbidden escape hatches, and `tsc --noEmit` workflow live
in the `typescript/tsc-strict` fragment (see `## Shared Conventions`); this file
is for TS-specific patterns, testing, and the bun toolchain.

## LSP — typescript-language-server

Always run LSP diagnostics before suggesting fixes. The TS language server surfaces
type errors, incorrect generics, missing properties, and signature mismatches.

```
LSP: hover       — full inferred type of any expression
LSP: diagnostics — type errors, strict mode violations
LSP: definition  — jump to declaration (including .d.ts for npm packages)
LSP: references  — find all usages across the project
LSP: rename      — safe rename across all files
```

Install: `bun install -g typescript typescript-language-server`

## Documentation

- **npm packages:** context7 MCP — excellent coverage, always use for library questions
- **TypeScript itself:** typescriptlang.org/docs — WebFetch for language features
- **Version check:** `af versions --write` reads `package.json` and lockfiles

## Toolchain at a glance

| Tool    | Purpose                                               | Covered in fragment     |
|---------|-------------------------------------------------------|-------------------------|
| `bun`   | Runtime, package manager, test runner                 | inline below            |
| `tsc`   | Type checker (no emit)                                | `typescript/tsc-strict` |
| `biome` | Linter and formatter (fast, replaces eslint+prettier) | inline below            |
| `tsx`   | Run TS files directly                                 | `bunx tsx file.ts`      |

## Idiomatic Patterns

**Prefer `type` over `interface`** for most cases — types are more composable:
```typescript
type User = { id: string; name: string }
type Admin = User & { role: 'admin' }
```

**Type narrowing** — use discriminated unions and type guards over casts:
```typescript
type Result<T> = { ok: true; value: T } | { ok: false; error: string }
```

**Async/await** — always handle errors; avoid floating promises.

(Strict typing rules, `unknown` vs `any`, forbidden escape hatches, and type-only
import syntax live in the `typescript/tsc-strict` fragment.)

## Anti-patterns

| Anti-pattern | Instead |
|-------------|---------|
| Optional chaining everywhere `?.` | Model nullability explicitly in types |
| Mutating objects directly | Prefer immutable updates: `{ ...obj, field: newValue }` |
| Floating promises without await | `void doThing()` if intentional, `await` otherwise |
| `require()` in new code | Always `import` — `require()` loses types |
| `JSON.parse()` without validation | Use zod or valibot to parse external data |

(`as any`, `@ts-ignore`, and enum bans are in the `typescript/tsc-strict` fragment.)

## Testing

**Runner:** `bun test` — built-in, no config needed. Falls back to vitest for complex setups.

**Structure:**
```
src/
  feature.ts
  feature.test.ts    # co-locate tests with source
tests/
  integration/       # tests that need real deps
```

**bun test basics:**
```typescript
import { describe, test, expect, beforeEach } from 'bun:test'

describe('UserService', () => {
  test('creates a user with valid input', () => {
    const user = createUser({ name: 'Alice', email: 'alice@example.com' })
    expect(user.id).toBeDefined()
    expect(user.name).toBe('Alice')
  })

  test('throws on invalid email', () => {
    expect(() => createUser({ name: 'Bob', email: 'not-an-email' }))
      .toThrow('Invalid email')
  })
})
```

**Run:**
```bash
bun test                      # all tests
bun test --watch              # re-run on change
bun test src/feature.test.ts  # specific file
```

**Mock:**
```typescript
import { mock } from 'bun:test'
const fetchMock = mock(() => Promise.resolve({ ok: true }))
```

## Package Management

**New project:**
```bash
bun init              # creates package.json, tsconfig.json, index.ts
bun add express       # add dependency
bun add -d @types/node vitest  # dev dependency
```

**Lock file:** `bun.lockb` — binary lockfile, always commit. Use `bun install --frozen-lockfile` in CI.

**Scripts in package.json:**
```json
{
  "scripts": {
    "dev": "bun run --watch src/index.ts",
    "build": "bun build src/index.ts --outdir dist",
    "test": "bun test",
    "typecheck": "tsc --noEmit"
  }
}
```

**Run a file directly:**
```bash
bun src/index.ts     # no compile step needed
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Mutating objects directly | Prefer immutable updates: `{ ...obj, field: newValue }` |
| Floating promises without await | `void doThing()` if intentional, `await` otherwise |
| `require()` in new code | Always `import` — `require()` loses types |
| `JSON.parse()` without validation | Use zod or valibot to parse external data |

(Strict-mode, `as any`, and `@ts-ignore` mistakes are covered in the `typescript/tsc-strict` fragment.)

## Outputs

- Strictly typed, biome-clean code
- LSP diagnostics report for any file reviewed
- `tsconfig.json` with strict settings if scaffolding
