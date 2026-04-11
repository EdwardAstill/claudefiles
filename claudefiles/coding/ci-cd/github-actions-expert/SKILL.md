---
name: github-actions-expert
description: >
  Use when writing, debugging, or reviewing GitHub Actions workflows. Also use
  when a workflow is failing, a job is unexpectedly skipped, secrets or permissions
  are misconfigured, matrix builds are behaving oddly, or Actions cache is stale.
  Expert with workflow syntax, runner environments, and gh CLI for CI operations.
---

# GitHub Actions Expert

Expert authoring and debugging for GitHub Actions workflows.

## Debugging a Failing Workflow

**Step 1: Get the failure details**

```bash
# List recent runs for the workflow
gh run list --workflow <name>.yml --limit 5

# View failed run details
gh run view <run-id> --log-failed
```

**Step 2: Identify the failure type**

| Symptom | Likely cause |
|---------|-------------|
| `Permission denied` | Missing `permissions:` block or GITHUB_TOKEN scope |
| `Context access might be invalid` | Typo in `${{ secrets.X }}` or secret not set |
| Job skipped unexpectedly | `if:` condition evaluated false; check `needs` context |
| Inconsistent behaviour across runs | Non-deterministic env; pin action versions |
| Cache miss every run | Cache key too specific; check `hashFiles()` pattern |
| Artifact not found | Different `name:` in upload vs download step |

**Step 3: Check the workflow locally (if needed)**

```bash
# act — run workflows locally (https://github.com/nektos/act)
act push --job <job-name> --secret-file .secrets
```

## Workflow Structure

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read       # always declare minimum permissions

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: bun test
```

**Key rules:**
- Always pin third-party actions to a commit SHA (`uses: actions/checkout@11bd...`)
- Declare minimum `permissions:` at workflow or job level
- Use `${{ env.VAR }}` for values shared across steps, not repeated `${{ secrets.X }}`
- Separate lint/test/deploy jobs — don't chain unrelated work in one job

## Matrix Builds

```yaml
strategy:
  matrix:
    node: [18, 20, 22]
    os: [ubuntu-latest, macos-latest]
  fail-fast: false   # don't cancel other jobs on first failure
```

To target a specific matrix cell:

```yaml
if: matrix.os == 'ubuntu-latest' && matrix.node == 20
```

## Secrets and Environments

```yaml
environment: production   # requires deployment environment to be configured in repo settings
env:
  API_KEY: ${{ secrets.API_KEY }}   # never echo secrets — they're masked in logs
```

Debug: `gh secret list --repo owner/repo`

## Caching

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.bun/install/cache
    key: ${{ runner.os }}-bun-${{ hashFiles('**/bun.lock') }}
    restore-keys: |
      ${{ runner.os }}-bun-
```

If cache is stale: bump the key manually or delete via
`gh cache delete <cache-id> --repo owner/repo`.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `${{ github.token }}` directly | Use `secrets.GITHUB_TOKEN` or `permissions` block |
| `if: ${{ ... }}` with extra `${{ }}` | In `if:` context, write `if: condition` without wrapping |
| Workflow triggers on wrong events | Check `on:` — `pull_request` fires on PR; `push` fires on direct push |
| Steps share state via files but no artifact | Use `upload-artifact`/`download-artifact` between jobs |
| Unpinned third-party actions | Always pin to SHA for security |
