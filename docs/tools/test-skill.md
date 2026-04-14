# af test-skill

Scaffold a skill test workspace for benchmarking with the `skill-tester` skill.

**Source:** `tools/python/src/af/test_skill.py`

## Usage

```bash
af test-skill <skill-name>    # first run: create evals.json template
                               # second run: create iteration workspace
```

## Workflow

1. **First run** — creates `tests/<skill-name>/evals.json` with an empty template
2. **Fill in evals** — add 4 hard benchmark questions with prompts and reference answers
3. **Second run** — creates `tests/<skill-name>/iteration-1/` workspace
4. **Invoke skill-tester** — tell Claude to run evals using the `skill-tester` skill

## Example

```bash
af test-skill dsa-expert
# Edit tests/dsa-expert/evals.json with 4 hard questions
af test-skill dsa-expert
# "Workspace ready at tests/dsa-expert/iteration-1/"
# Now invoke skill-tester to run the evals
```

## Files created

| Path | Purpose |
|------|---------|
| `tests/<name>/evals.json` | Eval prompts and reference answers |
| `tests/<name>/iteration-N/` | Workspace for grading outputs |

See the `skill-tester` skill for the full evaluation process and rubric.
