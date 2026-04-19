# Where to Change Skill Loading to Add Remote Sources

## Step 1 — Orient: How Is Skill Loading Done Today?

Before designing the change, pin down what "skill loading" actually means in this repo. Key finding from reading the code:

**There is no runtime skill-loader service.** agentfiles does not import or read SKILL.md at runtime. Instead:

- `manifest.toml` declares every skill (`[skills.<name>]`).
- `install.py` reads the manifest, discovers SKILL.md files under `agentfiles/`, and copies/links them into `~/.claude/skills/<name>/`.
- **Claude Code itself** reads `~/.claude/skills/<name>/SKILL.md` on demand when the user/agent triggers it.
- `includes.py` is the one runtime piece — it expands `includes:` fragments at skill-invocation time (preprocessor layer).
- `skill_find.py` is a keyword search over SKILL frontmatter (CLI only).

That reframes the change: the question isn't "how does the loader load from a URL," it's "how does the installer get a remote-sourced SKILL.md on disk so Claude Code can find it."

## Step 2 — Architecture Layers Touched

| Layer | File | Why |
|-------|------|-----|
| Declarative registry | `manifest.toml` | Extend schema with source field |
| Manifest parser | `tools/python/src/af/install.py` | Teach parser new field |
| Skill discovery & install | `tools/python/src/af/install.py` | Fetch remote → cache → discover uniformly |
| Fragment expansion | `tools/python/src/af/includes.py` | Decide policy for remote `includes:` |
| Keyword search | `tools/python/src/af/skill_find.py` | Make remote skills searchable |
| Bootstrap | `install.sh`, `bootstrap.sh` | Only if cache dir needs bootstrapping |
| Telemetry | `hooks/skill-logger.py` | Optional — tag source in log |
| Cross-cutting | tests/, docs/, README.md | Standard |

## Step 3 — Ordered Change List

### 1. `manifest.toml` (design anchor — touch first)

**Why:** This is the single source of truth for every skill. The whole install pipeline is driven by it; the shape you pick here propagates everywhere.

**Change type:** Schema extension. Add an optional `source` field per skill:

```toml
[skills.foo]
tools = ["Read"]
category = "research"
source = "https://example.com/skills/foo/SKILL.md"   # NEW, optional
# optional:
source_checksum = "sha256:..."
```

Default (when absent) = `local` = existing behavior. Design decision to make up front: does `source` point at a single SKILL.md or a directory manifest? Picking single-file keeps scope tight.

### 2. `tools/python/src/af/install.py` — `_parse_manifest` (modify)

**Why:** The current TOML-lite parser only captures `tools`, `mcp`, `cli`, `category`. It silently drops unknown fields. You need it to capture `source` (and optionally `source_checksum`).

**Change type:** Modify the existing function. In the `elif current_section == "skills" and current_key and "=" in line:` branch, add a case for `source` / `source_checksum` that stores as a string rather than a list.

### 3. `tools/python/src/af/install.py` — new `_fetch_remote_skill` helper

**Why:** You need a single place where network fetches happen, with checksum verification if declared and atomic write.

**Change type:** New function. Roughly:

```python
def _fetch_remote_skill(name: str, url: str, cache_dir: Path, checksum: str | None) -> Path:
    target_dir = cache_dir / name
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "SKILL.md"
    # urllib.request.urlopen + write to target.with_suffix(".tmp"), verify checksum, rename.
    return target
```

Cache dir default: `Path.home() / ".cache" / "agentfiles" / "remote-skills"`.

### 4. `tools/python/src/af/install.py` — `_discover_all_skills` (modify)

**Why:** The current function walks `agentfiles/` for SKILL.md files locally. Remote-sourced skills don't live in `agentfiles/`. Rather than making the rest of the install flow polymorphic, make the cache look like another skills directory.

**Change type:** Modify. Before the existing `rglob("SKILL.md")` walk, fetch all remote skills into the cache and then walk both `agentfiles/` and the cache. Result: uniform downstream processing.

### 5. `tools/python/src/af/install.py` — the install-time flow itself

**Why:** Wire the fetch step at the right moment. It must happen before discovery, and before the copy/symlink into `~/.claude/skills/`.

**Change type:** Add a new step to the existing install orchestration, calling `_fetch_remote_skill` for every skill that has a `source` URL in the parsed manifest.

### 6. `tools/python/src/af/includes.py` — `find_repo_root` / `includes_root`

**Why:** Fragment expansion looks in `agentfiles/includes/`. If remote skills want to declare `includes:`, those fragments need to be reachable.

**Change type:** Two options:
- **(a) Simple:** disallow `includes:` on remote skills and document the restriction. Small code change — validate at fetch time.
- **(b) Full:** generalize `find_repo_root` and `includes_root` to accept a list of root candidates, fetch remote include fragments into the cache under `remote-skills/<name>/includes/`, and have the resolver check the local tree first then the cache.

I would ship (a) first and only promote to (b) if a remote skill actually needs includes.

### 7. `tools/python/src/af/skill_find.py` — `_find_skills_root`

**Why:** Currently walks up the cwd for `agentfiles/`. Remote skills in the cache won't be found, so `af skill-find <keyword>` misses them.

**Change type:** Small modification. Return a list of roots, or add a secondary walk over the cache directory. The `rglob("SKILL.md")` loop below handles both uniformly.

### 8. `install.sh` / `bootstrap.sh` — minor or no change

**Why:** Only touch if:
- You want a `--no-remote` escape hatch surfaced at bootstrap (for fully offline installs).
- You want to pre-create the cache directory.

Otherwise this is just a docs update inside the README.

### 9. `hooks/skill-logger.py` — optional telemetry

**Why:** Currently the logger derives `skill_name` from the SKILL.md parent dir. If remote skills land in a distinct cache path, the skill_name is still the dir basename (same shape), but you lose provenance.

**Change type:** Optional. Add a `source` field to the log entry — `local` vs `remote` — inferred from the SKILL.md's parent path prefix. Accompanying change in `hook_types.py` is not needed (this is an output shape, not an input shape). Consumers (`af log`, `af metrics`, `af skill-usage`) would need parallel updates if you want to surface the new field in reports.

### 10. `plan_exec.py` / `plan_exec_cli.py` — NO change

**Why:** Explicitly worth calling out. `plan_exec` does not load skills; it validates plan YAML and tracks state. Skill invocation happens one layer up in the driving skill, and that reaches skills via Claude Code's built-in SKILL.md resolution — not via our code. So the remote-source change is invisible to plan_exec.

## Step 4 — Cross-Cutting Concerns

### Tests (`tools/python/tests/`)
- `_parse_manifest` with a new `source` field.
- `_fetch_remote_skill` happy path (mock `urllib.request.urlopen`).
- `_fetch_remote_skill` failure modes: unreachable URL, non-200, checksum mismatch, atomic-write safety (interrupted download doesn't leave a garbage file).
- `_discover_all_skills` with mixed local and cached remote entries.
- Install end-to-end with a fake manifest entry pointing at a local file:// URL.

### Docs
- `docs/reference/skills.md` — describe the new `source` field and semantics.
- `docs/skill-tree.md` — if it visualizes sources, add a badge / note for remote.
- `README.md` — if offline-install instructions change, update them.

### Security (design decision, document)
Remote fetch is a trust boundary. Options to discuss and pick:
- Require checksum in manifest for every remote entry (fail install if mismatch).
- Require the URL to be on an allowlist domain.
- Sign manifests and verify signature at install time.

The cheapest pragmatic default: require `source_checksum` for remote entries, fail closed on missing checksum, make verification part of `_fetch_remote_skill`.

### CLI surface
- Consider adding `af install --refresh-remote` to force-redownload the cache (otherwise cached files are reused).
- Consider `af install --no-remote` for explicit offline installs.

## Step 5 — Summary and When to Stop

### Execution order for the change

1. `manifest.toml` — declare shape (design anchor).
2. `install.py:_parse_manifest` — learn the shape.
3. `install.py:_fetch_remote_skill` — new helper.
4. `install.py:_discover_all_skills` + install flow — wire fetch before discovery.
5. Tests for steps 2–4.
6. `skill_find.py:_find_skills_root` — discoverability.
7. `includes.py` — restrict or extend per (a)/(b).
8. Docs.
9. (Optional) `skill-logger.py` — telemetry.

Entry point for the change is `manifest.toml`; every downstream touch follows from its declared shape.

### When to stop (what you can now answer)

- **"Does plan_exec need changes?"** → No. It doesn't load skills.
- **"Does the Claude Code runtime need changes?"** → No. It reads `~/.claude/skills/<name>/SKILL.md` unchanged. Our job ends at getting the file there.
- **"What's the riskiest part?"** → Trust boundary of the fetch. Mitigate with checksum pinning.
- **"Can I defer the includes question?"** → Yes. Ship with `includes: []` disallowed on remote skills (option a); upgrade to option b only when a remote skill actually needs fragments.
