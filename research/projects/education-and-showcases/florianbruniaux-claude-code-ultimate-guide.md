# FlorianBruniaux/claude-code-ultimate-guide

**URL:** https://github.com/FlorianBruniaux/claude-code-ultimate-guide
**Stars:** ~3,600 | **Type:** Comprehensive teaching guide + threat-modeling reference

## What It Is

A single-author, 6-months-of-daily-practice distillation of Claude Code knowledge — explicitly positioned as teaching "the WHY, not just the what." Not a tool collection; a study reference.

- **24K+ lines** of reference material across 16 specialized guides
- **228 production-ready templates** for agents, commands, hooks, skills
- **Security hardening track** with threat intelligence: 24 CVEs tracked, 655 malicious skills catalogued
- **Methodology coverage** — TDD, SDD (spec-driven), BDD workflows mapped onto agent workflows
- **Multi-agent coordination patterns** plus DevOps/SRE-shaped operational guidance
- **271-question knowledge validation quiz** (junior / senior / power-user progression)
- **41 visual diagrams** for architecture and lifecycle concepts

---

## What It Does Well

- **Threat modeling is unique in the ecosystem** — most Claude Code resources hand-wave security; this one tracks specific CVEs and malicious-skill patterns by name. Directly useful for hardening any skill marketplace or trust boundary.
- **Trade-off framing** — explains *why* one approach wins over another, not just config recipes. Rare for community guides.
- **Structured learning paths** with explicit difficulty tiers; usable as an onboarding curriculum, not just a reference dump
- **Methodology layer (TDD/SDD/BDD)** — most guides skip software-engineering methodology entirely and just show prompts; this one connects them

---

## Weaknesses

- **Single-author opinionation** — patterns reflect one practitioner's workflow; not all generalize cleanly
- **Sheer volume is the cost** — 24K lines means high signal but also high search-time; no skill-router-style discovery layer
- **Some content drifts toward Claude Code release notes** — sections age fast as the CLI evolves
- **Templates are documentation-shaped, not installable** — you read them and adapt, not `af add` them

---

## Take

The best public reference for **production hardening and threat modeling** of a Claude Code setup — agentfiles' security story (currently just `safety-gate.py` blocking destructive bash commands) could pull directly from the malicious-skills catalog and CVE tracker for a stronger threat model. Also worth mining the **methodology section** for a future agentfiles "spec-driven development" mode that complements the existing planner / verify-first modes.
