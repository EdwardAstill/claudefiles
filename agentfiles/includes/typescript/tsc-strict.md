---
name: typescript/tsc-strict
---

# TypeScript — Strict Typing Rules

Every TypeScript project in this suite runs under `"strict": true` plus a
handful of extra flags that catch real bugs. If existing code fails under
strict, fix the code — do not loosen the config.

## Required tsconfig flags

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noPropertyAccessFromIndexSignature": true,
    "isolatedModules": true,
    "skipLibCheck": false,
    "moduleResolution": "bundler",
    "target": "ES2022"
  }
}
```

What each one buys you:

- **`strict`** — `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`,
  and siblings. The baseline.
- **`noUncheckedIndexedAccess`** — `arr[0]` is `T | undefined`, not `T`.
  Catches off-by-one and empty-array bugs at compile time.
- **`exactOptionalPropertyTypes`** — `{ x?: number }` no longer silently
  accepts `{ x: undefined }`. Matches the type you wrote.
- **`noImplicitOverride`** — demand the `override` keyword so renames in
  the parent don't silently detach subclass methods.
- **`skipLibCheck: false`** — we'd rather see a bad `.d.ts` than ship it.

## Typecheck, don't emit

```bash
tsc --noEmit                    # whole project
tsc --noEmit -p tsconfig.test.json
```

Wire `typecheck` as an npm/bun script:

```json
{
  "scripts": {
    "typecheck": "tsc --noEmit"
  }
}
```

Run it in CI before tests — a typecheck failure makes test output noise.

## Patterns the config rewards

- **Discriminated unions** over optional properties:
  ```ts
  type Result<T> =
    | { ok: true; value: T }
    | { ok: false; error: string }
  ```
- **`unknown` over `any`.** Forces you to narrow before use.
- **`satisfies` over `as`.** Checks the constraint without widening.
- **`type` aliases for most shapes**, `interface` only for extendable
  public API surfaces.
- **Explicit return types on exported functions.** Inference is fine
  internally; boundaries deserve a contract.

## Type-only imports

With `isolatedModules` and modern bundlers, type-only imports must be
marked:

```ts
import type { User } from "./types.js"
import { createUser, type CreateUserInput } from "./users.js"
```

ESM + `.js` extensions — yes, even in `.ts` files. This is the source of
most "works in dev, breaks in build" issues.

## Forbidden escape hatches

| Ban              | Instead                                     |
|------------------|---------------------------------------------|
| `as any`         | Fix the type, or narrow from `unknown`      |
| `// @ts-ignore`  | `// @ts-expect-error reason` (fails loud when fixed) |
| `Function` type  | A specific `(a: A) => R` signature          |
| `Object` / `{}`  | `Record<string, unknown>` or a real shape   |
| Enums            | `as const` object or a string union         |

If an `any` is truly necessary (interop with untyped JS), isolate it in a
helper named `unsafe*` and export a typed wrapper.
