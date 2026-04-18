"""Phase 1 tests for `af plan-exec` core: loader, dataclasses, validator."""
from __future__ import annotations

from pathlib import Path

import pytest

from af.plan_exec import (
    ImplementNode,
    LoopNode,
    PauseNode,
    Plan,
    PlanParseError,
    ReviewNode,
    StateFile,
    load,
    toposort,
    validate,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def test_load_valid_plan_from_fixture():
    plan = load(FIXTURES / "plan_example.yaml")
    assert plan.version == 1
    assert plan.plan.slug == "af-session-resume"
    assert len(plan.nodes) == 6
    ids = [n.id for n in plan.nodes]
    assert ids == [
        "spec_contract",
        "cli_wiring",
        "spec_review",
        "human_gate_ux",
        "docs_per_surface",
        "quality_review",
    ]
    # Typed coercion.
    by_id = {n.id: n for n in plan.nodes}
    assert isinstance(by_id["spec_contract"], ImplementNode)
    assert isinstance(by_id["spec_review"], ReviewNode)
    assert by_id["spec_review"].reviewer == "spec"
    assert isinstance(by_id["human_gate_ux"], PauseNode)
    assert isinstance(by_id["docs_per_surface"], LoopNode)
    assert by_id["docs_per_surface"].max_parallel == 3
    assert by_id["docs_per_surface"].items == [
        "docs/wiki/af-session.md",
        "README.md",
        "AGENTS.md",
    ]
    assert len(by_id["docs_per_surface"].body) == 1


def test_load_minimal_valid_plan(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan:
  slug: x
  goal: do a thing
nodes:
  - id: only_node
    type: implement
    description: do the thing
""",
    )
    plan = load(p)
    assert len(plan.nodes) == 1
    errors = validate(plan, repo_root=tmp_path)
    assert errors == []


def test_load_rejects_missing_id(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - type: implement
    description: no id here
""",
    )
    with pytest.raises(PlanParseError, match="missing required field 'id'"):
        load(p)


def test_load_rejects_unknown_type(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: a
    type: not_a_real_type
    description: bad
""",
    )
    with pytest.raises(PlanParseError, match="unknown node type"):
        load(p)


def test_load_rejects_empty_file(tmp_path):
    p = _write(tmp_path, "plan.yaml", "")
    with pytest.raises(PlanParseError, match="empty"):
        load(p)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def test_validate_duplicate_ids(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: dupe
    type: implement
    description: first
  - id: dupe
    type: implement
    description: second
""",
    )
    plan = load(p)
    errors = validate(plan, repo_root=tmp_path)
    assert any("duplicate node id 'dupe'" in e for e in errors)


def test_validate_dangling_depends_on(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: a
    type: implement
    depends_on: [ghost]
    description: depends on missing node
""",
    )
    plan = load(p)
    errors = validate(plan, repo_root=tmp_path)
    assert any("depends_on 'ghost'" in e for e in errors)


def test_validate_detects_cycle(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: a
    type: implement
    depends_on: [c]
    description: a
  - id: b
    type: implement
    depends_on: [a]
    description: b
  - id: c
    type: implement
    depends_on: [b]
    description: c
""",
    )
    plan = load(p)
    errors = validate(plan, repo_root=tmp_path)
    assert any("cycle detected" in e for e in errors)


def test_validate_pause_without_prompt(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: gate
    type: pause
    description: missing prompt
""",
    )
    plan = load(p)
    errors = validate(plan, repo_root=tmp_path)
    assert any("pause node missing 'prompt'" in e for e in errors)


def test_validate_loop_without_items_or_from(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: lp
    type: loop
    description: no items, no from
    body:
      - id: inner
        type: implement
        description: body
""",
    )
    plan = load(p)
    errors = validate(plan, repo_root=tmp_path)
    assert any("requires either 'items' or 'from'" in e for e in errors)


def test_validate_files_create_rejects_existing(tmp_path):
    # Pre-create the file the plan promises to create.
    (tmp_path / "already_here.txt").write_text("x")
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: a
    type: implement
    description: should fail
    files:
      create:
        - already_here.txt
""",
    )
    plan = load(p)
    errors = validate(plan, repo_root=tmp_path)
    assert any("files.create path already exists" in e for e in errors)


def test_validate_files_modify_requires_existing(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: a
    type: implement
    description: should fail
    files:
      modify:
        - nope.txt
""",
    )
    plan = load(p)
    errors = validate(plan, repo_root=tmp_path)
    assert any("files.modify path does not exist" in e for e in errors)


def test_validate_on_fail_enum(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: a
    type: implement
    description: bogus on_fail
    on_fail: bogus
""",
    )
    plan = load(p)
    errors = validate(plan, repo_root=tmp_path)
    assert any("on_fail 'bogus'" in e for e in errors)


def test_validate_loop_max_parallel_cap(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: lp
    type: loop
    description: too wide
    items: [a, b]
    max_parallel: 11
    body:
      - id: inner
        type: implement
        description: body
""",
    )
    plan = load(p)
    errors = validate(plan, repo_root=tmp_path)
    assert any("exceeds cap 10" in e for e in errors)


# ---------------------------------------------------------------------------
# Topological sort
# ---------------------------------------------------------------------------


def test_toposort_chain(tmp_path):
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: a
    type: implement
    description: a
  - id: b
    type: implement
    depends_on: [a]
    description: b
  - id: c
    type: implement
    depends_on: [b]
    description: c
""",
    )
    plan = load(p)
    order = [n.id for n in toposort(plan)]
    assert order == ["a", "b", "c"]


def test_toposort_stable_alphabetical_within_level(tmp_path):
    # Two independent roots should come out alphabetical.
    p = _write(
        tmp_path,
        "plan.yaml",
        """
version: 1
plan: {slug: x}
nodes:
  - id: zeta
    type: implement
    description: z
  - id: alpha
    type: implement
    description: a
  - id: mid
    type: implement
    depends_on: [alpha, zeta]
    description: m
""",
    )
    plan = load(p)
    order = [n.id for n in toposort(plan)]
    assert order == ["alpha", "zeta", "mid"]


# ---------------------------------------------------------------------------
# StateFile stub
# ---------------------------------------------------------------------------


def test_statefile_roundtrip(tmp_path):
    sf = StateFile(states={"a": "pending", "b": "done"})
    target = tmp_path / "plan.state.json"
    sf.save(target)
    loaded = StateFile.load(target)
    assert loaded.states == {"a": "pending", "b": "done"}


def test_statefile_load_missing_returns_empty(tmp_path):
    sf = StateFile.load(tmp_path / "nothing.json")
    assert sf.states == {}
