---
name: security-review
description: >
  Use when reviewing code for security vulnerabilities, hardening an application,
  or before deploying to production. Covers OWASP top 10, dependency CVEs, secrets
  exposure, injection vectors, auth/authz issues, and cryptographic misuse.
  High-priority — invoke before any code reaches production.
---

# Security Review

Systematic security audit for application code, dependencies, and configuration.
Finds vulnerabilities before attackers do.

**Core principle:** Defense in depth. No single check is sufficient — layer
pattern matching, dependency scanning, and manual review.

## When to Use

- Before merging code that handles user input, authentication, or authorization
- Before deploying any service to production
- When adding new dependencies (especially from npm, PyPI, crates.io)
- When handling secrets, tokens, API keys, or credentials
- When implementing cryptographic operations
- When reviewing API endpoints for access control
- During periodic security audits of existing codebases

## When NOT to Use

- **Performance issues** — use `performance-profiling`
- **General code quality** — use `simplify` or `refactoring-patterns`
- **Test coverage gaps** — use `tdd`
- **Infrastructure hardening** — use `infrastructure-expert` (network, firewall, TLS config)

## The Iron Law

```
ASSUME ALL INPUT IS HOSTILE UNTIL VALIDATED
```

Every boundary — HTTP request, file upload, database query, environment variable,
deserialized object — is an attack surface.

## Process

### Phase 1: Threat Surface Mapping

1. **Identify entry points** — HTTP endpoints, CLI args, file readers, message consumers
2. **Map trust boundaries** — where does untrusted data cross into trusted context?
3. **Catalog sensitive operations** — auth, payment, PII access, admin functions
4. **Check dependency tree** — `npm audit`, `pip-audit`, `cargo audit`, `trivy`

### Phase 2: OWASP Top 10 Scan

| Vulnerability | What to Look For |
|---------------|-----------------|
| **A01: Broken Access Control** | Missing auth checks, IDOR, path traversal, CORS misconfiguration |
| **A02: Cryptographic Failures** | Hardcoded secrets, weak hashing (MD5/SHA1 for passwords), HTTP for sensitive data |
| **A03: Injection** | SQL concatenation, unsanitized shell commands, template injection, XSS |
| **A04: Insecure Design** | Missing rate limiting, no account lockout, business logic bypass |
| **A05: Security Misconfiguration** | Debug mode in prod, default credentials, verbose error messages |
| **A06: Vulnerable Components** | Known CVEs in dependencies, outdated frameworks |
| **A07: Auth Failures** | Weak passwords allowed, missing MFA, session fixation |
| **A08: Data Integrity Failures** | Unsigned updates, insecure deserialization, CI/CD pipeline tampering |
| **A09: Logging Failures** | No audit trail, logging sensitive data, missing alerting |
| **A10: SSRF** | Unvalidated URLs in fetch/request calls, DNS rebinding |

### Phase 3: Pattern Matching

Search the codebase for known dangerous patterns:

```bash
# Secrets exposure
grep -rn "password\s*=" --include="*.py" --include="*.ts" --include="*.js"
grep -rn "API_KEY\|SECRET\|TOKEN" --include="*.env*" --include="*.yml"
grep -rn "BEGIN.*PRIVATE KEY" .

# SQL injection
grep -rn "f\".*SELECT\|f\".*INSERT\|f\".*UPDATE\|f\".*DELETE" --include="*.py"
grep -rn "execute.*\+" --include="*.py" --include="*.js"

# Command injection
grep -rn "os\.system\|subprocess\.call.*shell=True\|exec(" --include="*.py"
grep -rn "child_process\.exec\b" --include="*.js" --include="*.ts"

# Insecure deserialization
grep -rn "pickle\.loads\|yaml\.load(" --include="*.py"
grep -rn "JSON\.parse.*eval\|unserialize" --include="*.php"
```

### Phase 4: Auth and Session Review

1. **Authentication** — verify password hashing uses bcrypt/argon2/scrypt, never MD5/SHA
2. **Authorization** — every endpoint checks permissions, not just authentication
3. **Session management** — secure cookie flags (HttpOnly, Secure, SameSite), token expiry
4. **CSRF protection** — state-changing operations require CSRF tokens
5. **Rate limiting** — login, registration, password reset endpoints are rate-limited

### Phase 5: Verification

Run automated scanners where available:
- `npm audit` / `pip-audit` / `cargo audit` for dependency CVEs
- `trivy` for container image scanning
- `semgrep` for static analysis with security rulesets
- `gitleaks` or `trufflehog` for secrets in git history

## Anti-patterns

| Anti-pattern | Why It's Dangerous | Instead |
|-------------|-------------------|---------|
| Rolling your own crypto | Subtle bugs that look correct but aren't | Use well-tested libraries (libsodium, bcrypt) |
| Secrets in source code | Committed to git history forever | Use environment variables, secret managers |
| `eval()` on user input | Arbitrary code execution | Parse explicitly, use safe alternatives |
| Disabling HTTPS in dev | Dev habits leak to prod | Use HTTPS everywhere, even locally |
| Trusting client-side validation | Trivially bypassed | Always validate server-side |
| Logging PII or secrets | Audit log becomes a liability | Sanitize logs, redact sensitive fields |
| Blanket CORS `*` | Any origin can make authenticated requests | Whitelist specific origins |
| `chmod 777` | World-readable/writable files | Least privilege: `644` for files, `755` for dirs |

## Tools

| Tool | Purpose | Command |
|------|---------|---------|
| `npm audit` | Node.js dependency CVEs | `npm audit --production` |
| `pip-audit` | Python dependency CVEs | `pip-audit` |
| `cargo audit` | Rust dependency CVEs | `cargo audit` |
| `trivy` | Container and filesystem scanning | `trivy fs .` |
| `semgrep` | Static analysis (security rules) | `semgrep --config=auto .` |
| `gitleaks` | Secrets in git history | `gitleaks detect` |
| `Grep` | Pattern matching for dangerous code | Search for known vulnerable patterns |

## Outputs

- Threat surface map listing all entry points and trust boundaries
- Vulnerability findings with severity (Critical/High/Medium/Low)
- Specific remediation steps for each finding
- Dependency audit results with CVE references
- Chain into `verification-before-completion` to confirm fixes
