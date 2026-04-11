---
name: typescript-expert
description: >
  TypeScript toolchain and conventions specialist. Use when you need
  typescript-language-server LSP diagnostics, bun/npm tooling, biome linting,
  or strict typing patterns — the tooling integration the base model doesn't
  enforce. Covers strict typing, generics, type narrowing, bun/npm tooling,
  and live code introspection via the typescript-language-server LSP.
---

# TypeScript Expert

Deep TypeScript knowledge — strict type system, modern patterns, runtime tooling,
and live LSP introspection. Uses typescript-language-server for type analysis and
context7 for package docs (best coverage of any language in the suite).

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
- **Version check:** `cf versions --write` reads `package.json` and lockfiles

## Toolchain

| Tool | Purpose | Command |
|------|---------|---------|
| `bun` | Runtime, package manager, test runner | `bun add <pkg>`, `bun test` |
| `tsc` | Type checker (no emit) | `tsc --noEmit` |
| `biome` | Linter and formatter (fast, replaces eslint + prettier) | `biome check .` |
| `tsx` | Run TS files directly | `bunx tsx file.ts` |

## Strict Mode

Always use strict mode. In `tsconfig.json`:
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

These catch real bugs. If existing code has errors under strict, fix them rather than loosening the config.

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

**`unknown` over `any`** — forces explicit narrowing before use.

**Async/await** — always handle errors; avoid floating promises.

**Imports** — use explicit `.js` extensions for ESM; use `type` imports for type-only:
```typescript
import type { User } from './types.js'
```

## Anti-patterns

| Anti-pattern | Instead |
|-------------|---------|
| `as any` | Fix the type or use `unknown` + narrowing |
| `as SomeType` casts | Use type guards or `satisfies` |
| `// @ts-ignore` | Fix the underlying issue |
| Optional chaining everywhere `?.` | Model nullability explicitly in types |
| Enums | Prefer `as const` objects or union types |

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
| Missing `"strict": true` in tsconfig | Always start strict — costs more to add later |
| `as any` to silence type errors | Fix the type — `any` breaks the safety model |
| Mutating objects directly | Prefer immutable updates: `{ ...obj, field: newValue }` |
| Floating promises without await | `void doThing()` if intentional, `await` otherwise |
| `require()` in new code | Always `import` — `require()` loses types |
| `JSON.parse()` without validation | Use zod or valibot to parse external data |

## Outputs

- Strictly typed, biome-clean code
- LSP diagnostics report for any file reviewed
- `tsconfig.json` with strict settings if scaffolding
