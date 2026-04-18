# tests/

Skill-tester workspaces. **Not** Python unit tests — those live at
`tools/python/tests/`.

## Layout

```
tests/<skill-name>/
  evals.json                    canonical eval prompts + reference answers
  iteration-N/
    <eval-name>/
      with_skill/outputs/response.md
      without_skill/outputs/response.md
      with_skill/grading.json
      without_skill/grading.json
    benchmark.json              per-iteration rubric aggregate

tests/<skill-name>-workspace/   scratch + in-flight eval runs
```

## Contents (2026-04-18)

- `dsa-expert/` — 10 LeetCode-Hard style prompts for the `dsa-expert` skill, plus iteration outputs.
- `dsa-expert-workspace/` — scratch workspace with additional eval runs and a `system-architecture-workspace/` from a separate test pass.

## Running

```bash
af test-skill <skill-name>        # scaffold a fresh iteration
# then invoke the skill-tester subagent to run the evals
```

See `agentfiles/agents/skill-tester.md` for the subagent that consumes these
workspaces.
