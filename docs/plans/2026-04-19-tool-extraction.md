# Tool extraction — externalize standalone CLIs out of agentfiles

**Status:** designed, not yet started.
**Decided:** 2026-04-19 during scope review.
**Rules doc:** [`docs/reference/what-belongs-here.md`](../reference/what-belongs-here.md).

---

## Scope

Extract six `af` subcommands that are standalone CLIs, not agent-system
infrastructure, into their own repos. Each becomes an independent tool with
its own release cadence. The agentfiles skill that references the tool stays
here.

## Extraction table

| # | `af <cmd>` | New repo | Skill staying in agentfiles | Notes |
|---|---|---|---|---|
| 1 | `af youtube` | `EdwardAstill/yt-cli` | `youtube` skill | transcripts / audio / summaries / search |
| 2 | `af webscraper` | `EdwardAstill/webscraper` | `web-scraper` skill | inspect / scaffold / fetch |
| 3 | `af terminal` | `EdwardAstill/termread` | `terminal-read` skill | tmux / screen scrollback capture |
| 4 | `af screenshot` | `EdwardAstill/shotty` | fold into `computer-control` recipes | Hyprland/Wayland screenshots |
| 5 | `af secrets` | `EdwardAstill/secrets` | *(no skill)* | env / secrets management |
| 6 | `af worktree` | `EdwardAstill/gwt` | `git-worktree-workflow` skill | git worktree + port alloc + `--launch` flag (see note) |

### Worktree generalization

`af worktree` today auto-launches `claude <worktree>` — that's the one
agent-specific bit. In `gwt`, make the launch optional: `--launch <cmd>`
flag or `GWT_LAUNCH_CMD` env var. Default = print path, don't launch.
Agentfiles' `git-worktree-workflow` skill tells the agent to invoke
`gwt <branch> --launch claude`.

## Extraction pattern (apply to each tool)

1. **Create remote repo**
   - `gh repo create EdwardAstill/<name> --public --description="..."`
   - Clone to `~/projects/<name>/`

2. **Scaffold**
   - `README.md` — what the tool does, install, usage, examples
   - `LICENSE` — match agentfiles' license
   - `pyproject.toml` — if Python, `uv init`; pin deps per tool
   - `.gitignore` — standard

3. **Move code**
   - Copy `tools/python/src/af/<cmd>.py` → the new repo's module
   - Copy any `tools/python/tests/test_<cmd>.py` → tests
   - Drop any `af.*` imports that don't carry their weight; replace with stdlib
     or small helper. Goal: tool has no `af` dependency.
   - Add a console-script entry in `pyproject.toml`:
     `[project.scripts]\n<name> = "<package>:main"`

4. **Verify the new tool**
   - `uv pip install -e .` in a clean venv
   - Run its test suite: `pytest`
   - Smoke test the CLI: `<name> --help`, then one happy-path invocation

5. **Wire skill to external tool**
   - Edit `agentfiles/<category>/<skill>/SKILL.md` so its instructions tell
     the agent to run `<name> <args>`, not `af <cmd>`.
   - Update any trigger phrases / examples.

6. **Remove from agentfiles**
   - Delete `tools/python/src/af/<cmd>.py`
   - Delete `tools/python/tests/test_<cmd>.py` (if any)
   - Remove the `("<cmd>", "<cmd>")` line from `tools/python/src/af/main.py`
   - If the tool had entries in `manifest.toml` `[cli.*]`, remove them
   - Run `af audit` — must stay 11/11 green

7. **Update `eastill`**
   - Flip the repo's row from `*(planned)*` to `active`
   - Commit + push the profile README

8. **Commit in both repos**
   - In the new repo: initial commit with full history
   - In agentfiles: single commit `chore(extract): move <cmd> to EdwardAstill/<name>`

## Order — easiest first

1. **yt-cli** *(youtube)* — self-contained, clear inputs/outputs, already has `af youtube transcript/audio/summary/channel/playlists/search` subcommands. Testable end-to-end.
2. **webscraper** — similar shape, a few more subcommands (inspect/scaffold/fetch). JSONL/CSV/SQLite outputs.
3. **gwt** *(worktree)* — small surface but has the `--launch` generalization. Prove the skill-references-external-tool pattern.
4. **termread** *(terminal)* — tmux/screen integration, captures scrollback. Useful but rarely breaks.
5. **shotty** *(screenshot)* — thin wrapper around `grim` / `slurp` on Wayland. Small.
6. **secrets** — no skill to rewire, just moves code.

Rationale: start with tools that have clear test cases. Build confidence in the pattern before tackling edge cases.

## Per-tool session estimate

| Step | Time |
|---|---|
| Create + scaffold remote | 20 min |
| Move code, strip `af.*` deps | 30-60 min |
| Verify (tests + smoke) | 20 min |
| Wire skill to external tool | 15 min |
| Remove from agentfiles, run audit | 15 min |
| Update `eastill` | 5 min |
| Commit + push both | 10 min |
| **Per tool** | **~2-2.5 hrs** |

**6 tools × 2 hrs = 12 hrs** = 2-3 focused sessions.

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Tool has transitive `af.*` dep that's hard to extract | Write a tiny local helper in the new repo; don't pull in `af` |
| User has `af <cmd>` muscle memory, new CLI name confuses | Briefly keep `af <cmd>` as a thin shim that shells out to the new tool — remove after a release or two |
| Shared helpers in `af.lib` or `af.context` | Copy only what's needed; don't take the whole lib |
| Tests assume agentfiles repo layout | Rewrite to be self-contained |

## Done criteria

- All 6 repos live under `EdwardAstill/`, flipped to `active` in `eastill`
- Each has: README, LICENSE, pyproject.toml, passing tests, installable via
  `uv pip install -e .` or `pipx install`
- Agentfiles `af audit` stays 11/11 green throughout
- Agentfiles skills that reference these tools invoke them by their new CLI
  names (no `af <cmd>` references in skill bodies)
- `tools/python/src/af/` no longer contains: `youtube.py`, `webscraper.py`,
  `terminal.py`, `screenshot.py`, `secrets.py`, `worktree.py`

## Out of scope for this plan

- `af hub`, `af repo`, `af preview`, `af note`, `af read`, `af init` — not yet
  classified; investigate and decide separately.
- Packaging / publishing to PyPI — each tool is installable from source for
  now. Revisit once a tool has external users.
- CI setup beyond basic pytest — add GitHub Actions only when needed.

## Next actions

1. Spawn `yt-cli` extraction as the template run (next session).
2. Refine this plan after the first extraction — record any surprises.
3. Continue through the list in order.
