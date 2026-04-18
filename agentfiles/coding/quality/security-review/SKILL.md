---
name: security-review
description: >
  Use when reviewing code for security vulnerabilities, hardening an application,
  or before deploying to production. Covers OWASP top 10, dependency CVEs, secrets
  exposure, injection vectors, auth/authz issues, and cryptographic misuse.
  High-priority — invoke before any code reaches production.
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
