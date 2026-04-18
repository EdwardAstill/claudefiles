"""Plan YAML loader, schema dataclasses, and DAG validator.

Phase 1 core of `af plan-exec`. No CLI, no dispatch, no state mutation.
See docs/plans/2026-04-18-plan-yaml-schema.md section 3 (schema) and
section 5 (tooling) for the authoritative spec.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

import yaml


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class PlanParseError(Exception):
    """Raised when a plan YAML cannot be parsed into the schema."""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


VALID_ON_FAIL = {"retry", "escalate", "pause"}
VALID_REVIEWERS = {"spec", "code_quality"}
VALID_NODE_TYPES = {"implement", "review", "verify", "pause", "loop"}
MAX_PARALLEL_CAP = 10


@dataclass
class Files:
    create: list[str] = field(default_factory=list)
    modify: list[str] = field(default_factory=list)
    test: list[str] = field(default_factory=list)


@dataclass
class BaseNode:
    id: str
    type: str
    description: str = ""
    depends_on: list[str] = field(default_factory=list)
    prose_ref: str | None = None
    files: Files = field(default_factory=Files)
    verify: list[str] = field(default_factory=list)
    on_fail: str | None = None


@dataclass
class ImplementNode(BaseNode):
    pass


@dataclass
class VerifyNode(BaseNode):
    pass


@dataclass
class ReviewNode(BaseNode):
    reviewer: str | None = None


@dataclass
class PauseNode(BaseNode):
    prompt: str | None = None


@dataclass
class LoopNode(BaseNode):
    items: list[Any] | None = None
    from_: str | None = None
    body: list[Node] = field(default_factory=list)
    until: str | None = None
    max_parallel: int = 1


Node = Union[ImplementNode, VerifyNode, ReviewNode, PauseNode, LoopNode]


@dataclass
class PlanMeta:
    slug: str = ""
    prose: str | None = None
    goal: str = ""


@dataclass
class Plan:
    version: int
    plan: PlanMeta
    nodes: list[Node]
    source_path: Path | None = None


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _coerce_files(raw: Any, where: str) -> Files:
    if raw is None:
        return Files()
    if not isinstance(raw, dict):
        raise PlanParseError(f"{where}: 'files' must be a mapping, got {type(raw).__name__}")
    return Files(
        create=list(raw.get("create") or []),
        modify=list(raw.get("modify") or []),
        test=list(raw.get("test") or []),
    )


def _coerce_node(raw: Any, where: str) -> Node:
    if not isinstance(raw, dict):
        raise PlanParseError(f"{where}: node must be a mapping, got {type(raw).__name__}")

    node_type = raw.get("type")
    node_id = raw.get("id")
    if not node_id:
        raise PlanParseError(f"{where}: node missing required field 'id'")
    if not node_type:
        raise PlanParseError(f"{where} (id={node_id}): node missing required field 'type'")
    if node_type not in VALID_NODE_TYPES:
        raise PlanParseError(
            f"{where} (id={node_id}): unknown node type '{node_type}'. "
            f"Expected one of: {sorted(VALID_NODE_TYPES)}"
        )

    common = {
        "id": node_id,
        "type": node_type,
        "description": raw.get("description", "") or "",
        "depends_on": list(raw.get("depends_on") or []),
        "prose_ref": raw.get("prose_ref"),
        "files": _coerce_files(raw.get("files"), f"{where} (id={node_id})"),
        "verify": list(raw.get("verify") or []),
        "on_fail": raw.get("on_fail"),
    }

    if node_type == "implement":
        return ImplementNode(**common)
    if node_type == "verify":
        return VerifyNode(**common)
    if node_type == "review":
        return ReviewNode(**common, reviewer=raw.get("reviewer"))
    if node_type == "pause":
        return PauseNode(**common, prompt=raw.get("prompt"))
    if node_type == "loop":
        body_raw = raw.get("body") or []
        if not isinstance(body_raw, list):
            raise PlanParseError(f"{where} (id={node_id}): loop 'body' must be a list")
        body: list[Node] = [
            _coerce_node(item, f"{where} (id={node_id}).body[{i}]")
            for i, item in enumerate(body_raw)
        ]
        max_parallel = raw.get("max_parallel", 1)
        if not isinstance(max_parallel, int):
            raise PlanParseError(
                f"{where} (id={node_id}): loop 'max_parallel' must be an integer"
            )
        return LoopNode(
            **common,
            items=raw.get("items"),
            from_=raw.get("from"),
            body=body,
            until=raw.get("until"),
            max_parallel=max_parallel,
        )

    # Unreachable given validation above, but keep mypy/pyright happy.
    raise PlanParseError(f"{where} (id={node_id}): unhandled type '{node_type}'")


def load(path: Path) -> Plan:
    """Load a plan YAML from disk. Raises PlanParseError on malformed input."""
    path = Path(path)
    if not path.exists():
        raise PlanParseError(f"plan file not found: {path}")
    try:
        text = path.read_text()
    except OSError as e:
        raise PlanParseError(f"could not read {path}: {e}") from e

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        loc = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        raise PlanParseError(f"YAML parse error in {path}{loc}: {e}") from e

    if data is None:
        raise PlanParseError(f"{path}: plan file is empty")
    if not isinstance(data, dict):
        raise PlanParseError(f"{path}: top-level must be a mapping, got {type(data).__name__}")

    version = data.get("version")
    if version is None:
        raise PlanParseError(f"{path}: missing required top-level field 'version'")

    plan_meta_raw = data.get("plan") or {}
    if not isinstance(plan_meta_raw, dict):
        raise PlanParseError(f"{path}: 'plan' must be a mapping")
    plan_meta = PlanMeta(
        slug=plan_meta_raw.get("slug", "") or "",
        prose=plan_meta_raw.get("prose"),
        goal=plan_meta_raw.get("goal", "") or "",
    )

    nodes_raw = data.get("nodes")
    if not isinstance(nodes_raw, list):
        raise PlanParseError(f"{path}: 'nodes' must be a list")

    nodes: list[Node] = [
        _coerce_node(item, f"{path}:nodes[{i}]") for i, item in enumerate(nodes_raw)
    ]
    return Plan(version=int(version), plan=plan_meta, nodes=nodes, source_path=path)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def _all_ids(plan: Plan) -> list[str]:
    """Return all node ids including loop bodies (for duplicate detection)."""
    out: list[str] = []
    for n in plan.nodes:
        out.append(n.id)
        if isinstance(n, LoopNode):
            for inner in n.body:
                out.append(inner.id)
    return out


def _top_level_ids(plan: Plan) -> set[str]:
    return {n.id for n in plan.nodes}


def validate(plan: Plan, repo_root: Path | None = None) -> list[str]:
    """Return a list of validation error strings; empty list means valid.

    `repo_root` controls where `files.create` / `files.modify` paths are
    resolved. Defaults to the plan's parent directory's repo-ish root
    (current working directory if no source_path).
    """
    errors: list[str] = []

    # Resolve repo root for filesystem invariants.
    if repo_root is None:
        repo_root = Path.cwd()
    repo_root = Path(repo_root)

    # (a) Unique ids (across top-level and loop bodies).
    seen: dict[str, int] = {}
    for node_id in _all_ids(plan):
        seen[node_id] = seen.get(node_id, 0) + 1
    for node_id, count in seen.items():
        if count > 1:
            errors.append(f"duplicate node id '{node_id}' appears {count} times")

    top_ids = _top_level_ids(plan)

    # (b) depends_on resolves. Top-level deps must reference top-level ids.
    for n in plan.nodes:
        for dep in n.depends_on:
            if dep not in top_ids:
                errors.append(
                    f"node '{n.id}' depends_on '{dep}' which is not defined at top level"
                )

    # (c) Cycle detection via Kahn's algorithm on top-level nodes.
    if not any(
        "duplicate node id" in e or "depends_on" in e for e in errors
    ) or True:  # still run even if dangling, to catch cycles too
        in_degree = {n.id: 0 for n in plan.nodes}
        adj: dict[str, list[str]] = {n.id: [] for n in plan.nodes}
        for n in plan.nodes:
            for dep in n.depends_on:
                if dep in in_degree:
                    adj[dep].append(n.id)
                    in_degree[n.id] += 1
        # Kahn's
        queue = sorted([nid for nid, d in in_degree.items() if d == 0])
        visited = 0
        while queue:
            nid = queue.pop(0)
            visited += 1
            for nxt in sorted(adj[nid]):
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)
            queue.sort()
        if visited != len(plan.nodes):
            remaining = sorted([nid for nid, d in in_degree.items() if d > 0])
            errors.append(f"cycle detected among nodes: {remaining}")

    # (d) Type-specific required fields.
    def _check_node(n: Node, context: str = "") -> None:
        prefix = f"node '{n.id}'" + (f" (in {context})" if context else "")
        if isinstance(n, ReviewNode):
            if not n.reviewer:
                errors.append(f"{prefix}: review node missing 'reviewer'")
            elif n.reviewer not in VALID_REVIEWERS:
                errors.append(
                    f"{prefix}: review.reviewer '{n.reviewer}' not in {sorted(VALID_REVIEWERS)}"
                )
        if isinstance(n, PauseNode):
            if not n.prompt or not str(n.prompt).strip():
                errors.append(f"{prefix}: pause node missing 'prompt'")
        if isinstance(n, LoopNode):
            has_items = n.items is not None and len(n.items) > 0
            has_from = bool(n.from_)
            if not has_items and not has_from:
                errors.append(
                    f"{prefix}: loop node requires either 'items' or 'from'"
                )
            if has_items and has_from:
                errors.append(
                    f"{prefix}: loop node cannot set both 'items' and 'from'"
                )
            if n.max_parallel > MAX_PARALLEL_CAP:
                errors.append(
                    f"{prefix}: loop.max_parallel={n.max_parallel} exceeds cap {MAX_PARALLEL_CAP}"
                )
            if n.max_parallel < 1:
                errors.append(
                    f"{prefix}: loop.max_parallel must be >= 1 (got {n.max_parallel})"
                )
            if not n.body:
                errors.append(f"{prefix}: loop node missing 'body'")
            for inner in n.body:
                _check_node(inner, context=f"loop '{n.id}'")

        # (g) on_fail enum.
        if n.on_fail is not None and n.on_fail not in VALID_ON_FAIL:
            errors.append(
                f"{prefix}: on_fail '{n.on_fail}' not in {sorted(VALID_ON_FAIL)}"
            )

    for n in plan.nodes:
        _check_node(n)

    # (e) files.create paths must NOT exist.
    # (f) files.modify paths MUST exist.
    def _check_files(n: Node, context: str = "") -> None:
        prefix = f"node '{n.id}'" + (f" (in {context})" if context else "")
        for p in n.files.create:
            full = (repo_root / p).resolve()
            if full.exists():
                errors.append(
                    f"{prefix}: files.create path already exists: {p}"
                )
        for p in n.files.modify:
            full = (repo_root / p).resolve()
            if not full.exists():
                errors.append(
                    f"{prefix}: files.modify path does not exist: {p}"
                )
        if isinstance(n, LoopNode):
            for inner in n.body:
                _check_files(inner, context=f"loop '{n.id}'")

    for n in plan.nodes:
        _check_files(n)

    return errors


# ---------------------------------------------------------------------------
# Topological sort
# ---------------------------------------------------------------------------


def toposort(plan: Plan) -> list[Node]:
    """Return top-level nodes in dispatch order.

    Stable: within a dependency level, sort alphabetically by id. Raises
    ValueError if the plan has a cycle (run `validate` first to surface
    a friendlier message).
    """
    by_id = {n.id: n for n in plan.nodes}
    in_degree = {nid: 0 for nid in by_id}
    adj: dict[str, list[str]] = {nid: [] for nid in by_id}
    for n in plan.nodes:
        for dep in n.depends_on:
            if dep in by_id:
                adj[dep].append(n.id)
                in_degree[n.id] += 1

    out: list[Node] = []
    # Level-by-level, alphabetical within level.
    ready = sorted([nid for nid, d in in_degree.items() if d == 0])
    while ready:
        nid = ready.pop(0)
        out.append(by_id[nid])
        for nxt in adj[nid]:
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                ready.append(nxt)
        ready.sort()

    if len(out) != len(plan.nodes):
        raise ValueError("plan has a cycle; toposort not possible")
    return out


# ---------------------------------------------------------------------------
# State file (minimal stub)
# ---------------------------------------------------------------------------


VALID_STATES = {"pending", "running", "done", "failed"}


@dataclass
class StateFile:
    """Per-plan run state. {node_id: pending|running|done|failed}.

    Phase 2 extensions: `mark`, `reset`, `status_summary`, `ready_nodes`.
    """

    states: dict[str, str] = field(default_factory=dict)
    path: Path | None = None

    @classmethod
    def load(cls, path: Path) -> StateFile:
        path = Path(path)
        if not path.exists():
            return cls(states={}, path=path)
        try:
            data = json.loads(path.read_text() or "{}")
        except json.JSONDecodeError as e:
            raise PlanParseError(f"state file {path} is not valid JSON: {e}") from e
        if not isinstance(data, dict):
            raise PlanParseError(f"state file {path}: top-level must be a mapping")
        states: dict[str, str] = {}
        for k, v in data.items():
            if not isinstance(v, str) or v not in VALID_STATES:
                raise PlanParseError(
                    f"state file {path}: invalid state '{v}' for node '{k}'"
                )
            states[str(k)] = v
        return cls(states=states, path=path)

    def save(self, path: Path | None = None) -> None:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("StateFile.save requires a path (none stored and none provided)")
        target.write_text(json.dumps(self.states, indent=2, sort_keys=True) + "\n")
        self.path = target

    # ------------------------------------------------------------------
    # Phase 2 mutation helpers
    # ------------------------------------------------------------------

    def mark(self, node_id: str, status: str) -> None:
        """Set node_id to status and persist. Raises ValueError on bad status."""
        if status not in VALID_STATES:
            raise ValueError(
                f"invalid status '{status}'; must be one of {sorted(VALID_STATES)}"
            )
        self.states[node_id] = status
        if self.path is not None:
            self.save(self.path)

    @classmethod
    def reset(cls, path: Path) -> None:
        """Wipe the state file at path (no-op if missing)."""
        path = Path(path)
        if path.exists():
            path.unlink()

    def status_summary(self) -> dict[str, int]:
        """Return counts per status (pending/running/done/failed)."""
        out = {s: 0 for s in sorted(VALID_STATES)}
        for v in self.states.values():
            if v in out:
                out[v] += 1
        return out

    def ready_nodes(self, plan: Plan) -> list[Node]:
        """Return top-level nodes whose deps are all `done` and own status is `pending`.

        A node's own status is `pending` if it is not in the state map or the
        state map records `pending` explicitly. Order matches toposort.
        """
        order = toposort(plan)
        out: list[Node] = []
        for n in order:
            own = self.states.get(n.id, "pending")
            if own != "pending":
                continue
            deps_done = all(
                self.states.get(dep) == "done" for dep in n.depends_on
            )
            if deps_done:
                out.append(n)
        return out
