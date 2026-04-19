---
name: dependency-management
description: >
  Use for bumping dependency versions, analyzing breaking changes, CVE
  remediation, lock-file hygiene, and automated update tooling
  (Dependabot, Renovate). Trigger phrases: "bump these dependencies",
  "CVE alert on package X", "update to the latest major of Y", "lock
  file is conflicting", "audit my dependency tree", "set up Dependabot /
  Renovate", "why is my bundle so big", "find a lighter alternative to
  X", "is this patch version safe", "handle the breaking change from
  vN to vN+1". Covers npm, pip/uv, and cargo. Do NOT use for broader
  application security (use security-review), performance caused by
  picking a library (use performance-profiling), for choosing which
  library to adopt (use research-agent), or for writing code that uses
  a library (use the language expert).
---

# Dependency Management

Systematic dependency updates, CVE remediation, and lock file hygiene.
Keeps the supply chain clean without breaking the build.

**Core principle:** Dependencies are other people's code running in your
application. Trust but verify — audit, pin, lock, and scan.

## When to Use

- Bumping dependencies (major, minor, or patch)
- Responding to CVE alerts or security advisories
- Migrating between major versions of a framework or library
- Setting up Dependabot or Renovate for automated updates
- Resolving dependency conflicts or lock file issues
- Auditing the dependency tree for unused or duplicated packages
- Reducing bundle size by finding lighter alternatives

## When NOT to Use

- **Application security review** beyond dependencies — use `security-review`
- **Performance issues** caused by a dependency — use `performance-profiling`
- **Choosing which library to use** for a feature — use `research-agent`
- **Writing code that uses a library** — use the relevant language expert

## The Iron Law

```
NEVER UPDATE A DEPENDENCY WITHOUT RUNNING THE FULL TEST SUITE
```

Green CI is the only acceptable evidence that an update is safe.

## Process

### Phase 1: Audit Current State

1. **List outdated dependencies:**
   ```bash
   # Node.js
   npm outdated

   # Python (uv)
   uv pip list --outdated

   # Rust
   cargo outdated
   ```

2. **Scan for known vulnerabilities:**
   ```bash
   npm audit
   pip-audit
   cargo audit
   ```

3. **Check for unused dependencies:**
   ```bash
   # Node.js
   npx depcheck

   # Python
   uv pip install deptry && deptry .
   ```

4. **Review dependency tree depth:**
   ```bash
   npm ls --depth=3
   cargo tree
   ```

### Phase 2: Assess Updates

For each dependency update, classify the risk:

| Update Type | Risk | Action |
|-------------|------|--------|
| Patch (1.2.3 → 1.2.4) | Low | Update, run tests |
| Minor (1.2.x → 1.3.0) | Medium | Read changelog, run tests |
| Major (1.x → 2.0.0) | High | Read migration guide, plan migration, run tests |
| Security fix (any version) | Urgent | Update immediately, run tests |

**Before updating a major version:**
1. Read the CHANGELOG or migration guide completely
2. Search for breaking changes that affect your usage
3. Check GitHub issues for common migration problems
4. Plan the migration — may require code changes

### Phase 3: Update Safely

**Single dependency updates (preferred):**
```bash
# Update one at a time to isolate breakage
npm install package@^2.0.0
uv add "package>=2.0,<3.0"
cargo update -p package

# Run tests after each update
npm test
uv run pytest
cargo test
```

**Lock file hygiene:**
- Always commit lock files (`package-lock.json`, `uv.lock`, `Cargo.lock`)
- Never manually edit lock files
- Regenerate if corrupted: delete and reinstall
- Review lock file diffs — unexpected changes may indicate supply chain issues

### Phase 4: Automate

**Dependabot configuration (.github/dependabot.yml):**
```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      dev-dependencies:
        dependency-type: "development"
      production-dependencies:
        dependency-type: "production"
    open-pull-requests-limit: 10
```

**Renovate (renovate.json):**
```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true
    },
    {
      "matchUpdateTypes": ["major"],
      "automerge": false
    }
  ]
}
```

## Breaking Change Analysis

When a major update has breaking changes:

1. **Grep for deprecated APIs** in your codebase
2. **Check type definitions** — TypeScript/Rust will catch removed or changed APIs at compile time
3. **Run tests** — they catch behavioral changes
4. **Search for migration codemods** — many libraries provide automated migration scripts
5. **Update incrementally** — if upgrading across multiple majors (v1 → v3), go v1 → v2 → v3

## Anti-patterns

| Anti-pattern | Why It's Bad | Instead |
|-------------|-------------|---------|
| Updating all dependencies at once | Can't isolate which update broke things | One update at a time |
| Ignoring lock files | Non-reproducible builds | Always commit lock files |
| Pinning exact versions without lock file | False sense of security (transitive deps float) | Use lock files for reproducibility |
| Ignoring CVE alerts | Known vulnerabilities in production | Triage and fix promptly |
| `npm install --force` or `--legacy-peer-deps` | Hides real conflicts | Resolve peer dependency conflicts properly |
| Vendoring without a plan to update | Forked code rots | Only vendor with an update strategy |
| No automated dependency updates | Dependencies get years behind | Set up Dependabot or Renovate |
| Updating in production branch | No rollback path | Update in feature branch, test, then merge |

## CVE Response Process

1. **Triage** — is the vulnerable code path reachable in your application?
2. **Check for patch** — is a fixed version available?
3. **Update** — if patch exists, update and test
4. **Workaround** — if no patch, can you mitigate (disable feature, add validation)?
5. **Document** — record the CVE, your assessment, and the action taken
6. **Monitor** — watch for the fix if you applied a workaround

## Tools

| Tool | Ecosystem | Purpose |
|------|-----------|---------|
| `npm audit` | Node.js | CVE scanning |
| `pip-audit` | Python | CVE scanning |
| `cargo audit` | Rust | CVE scanning |
| `depcheck` | Node.js | Find unused dependencies |
| `deptry` | Python | Find unused/missing dependencies |
| `cargo-deny` | Rust | License and CVE checking |
| `Dependabot` | GitHub | Automated update PRs |
| `Renovate` | Any | Automated update PRs (more configurable) |
| `socket.dev` | npm/PyPI | Supply chain attack detection |

## Outputs

- Dependency audit report with outdated and vulnerable packages
- Update plan with risk classification per dependency
- Updated lock files with passing CI
- Dependabot/Renovate configuration if not already present
- Chain into `verification-before-completion` to confirm all tests pass
