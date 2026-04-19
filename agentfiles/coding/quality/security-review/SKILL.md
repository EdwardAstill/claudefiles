---
name: security-review
description: >
  Use when scanning code for security vulnerabilities, hardening an app
  before production, or auditing a specific threat surface. Trigger
  phrases: "security review this code", "audit for OWASP top 10", "check
  for SQL injection / XSS / SSRF", "scan for exposed secrets", "is this
  auth flow safe", "review the crypto usage here", "CVE check on my
  deps", "is this input validation enough", "harden this before we
  deploy", "run a security pass on the repo". Dispatches a restricted
  read-only subagent (see agentfiles/agents/security-review.md) that
  returns grouped findings by severity with file:line + fix. Do NOT use
  for general dependency bumps (use dependency-management), for code
  correctness bugs (use systematic-debugging), or for observability /
  audit logging beyond compliance (use observability).
---

# Security Review (dispatcher)

This capability now runs as a **subagent** — see
`agentfiles/agents/security-review.md`. It's a subagent because:

- Tool list is restricted to read-only to prevent accidental edits mid-review.
- Output is verbose (scan results, pattern matches, CVE lists) and
  shouldn't flood the parent context.
- Task is self-contained: scan, report, done.

## How to invoke

Dispatch via the Agent tool:

```
subagent_type: security-review
prompt: |
  Run a full security review on <target directory or files>.
  Focus: OWASP Top 10, secrets, dependency CVEs, auth/authz, crypto.
  Return: grouped findings by severity with file:line, trigger, and fix.
```

The subagent returns a structured report. For follow-up remediation,
chain into `verification-before-completion` after fixes land.

## When to use this skill instead of the subagent directly

Almost never. This skill exists so that `/security-review` routes to the
subagent. If you already know you want a security review, call the Agent
tool directly.
