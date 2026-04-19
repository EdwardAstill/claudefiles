# Adding Remote Skill Sources

To add remote URL as a skill source, you would touch the following files:

## 1. `manifest.toml`

Extend the `[skills.<name>]` schema to accept a `source = "https://..."` field. This is the declarative registry.

## 2. `tools/python/src/af/install.py`

Two changes needed here:

- `_parse_manifest` — currently parses tools, mcp, cli, category. Extend it to capture the new `source` field.
- `_discover_all_skills` — currently walks `agentfiles/` for SKILL.md files. Extend to fetch remote skills into a local cache (e.g., `~/.cache/agentfiles/remote-skills/<name>/`) before discovery, so the rest of the install flow sees on-disk files.

Also add a new helper like `_fetch_remote_skill(name, url, cache_dir)` that downloads and caches.

## 3. `tools/python/src/af/includes.py`

If remote skills can reference `includes:` fragments, you may need to extend the include resolver to know about the cache. Otherwise document that remote skills can't use includes.

## 4. `tools/python/src/af/skill_find.py`

Extend `_find_skills_root` to also scan the remote cache, so `af skill-find` can discover remote skills.

## 5. Tests and docs

Add tests in `tools/python/tests/` for manifest parsing, fetch-and-cache, error cases. Update docs under `docs/reference/skills.md`.

## Cross-cutting concerns

- Security: adding remote fetch is a trust boundary. Consider pinning by checksum.
- Offline install: add a `--no-remote` flag.
- `hooks/skill-logger.py` — might want to log source type per skill invocation for attribution.
- Plan-exec does NOT need changes — it doesn't load skills.

Order: manifest.toml → install.py → includes.py/skill_find.py → tests → docs.
