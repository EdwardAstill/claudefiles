---
name: typescript-expert
description: >
  TypeScript and JavaScript expert. Use when writing, debugging, or reviewing
  TS/JS code. Covers strict typing, generics, type narrowing, bun/npm tooling,
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
- **Version check:** `cf-versions --write` reads `package.json` and lockfiles

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

## Outputs

- Strictly typed, biome-clean code
- LSP diagnostics report for any file reviewed
- `tsconfig.json` with strict settings if scaffolding
