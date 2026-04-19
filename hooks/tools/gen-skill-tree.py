#!/usr/bin/env python3
"""Generate docs/skill-tree.md from agentfiles/ SKILL.md frontmatter.

Run from repo root:  python hooks/tools/gen-skill-tree.py

Walks agentfiles/<...>/SKILL.md, pulls the first sentence of each
`description:` frontmatter field, and emits a tree rooted at agentfiles/.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "agentfiles"
OUTPUT = REPO / "docs" / "skill-tree.md"
DESC_WIDTH = 110


def _first_sentence(description: str) -> str:
    text = " ".join(description.split())
    if not text:
        return ""
    for terminator in (". ", "? ", "! "):
        idx = text.find(terminator)
        if idx != -1:
            return text[: idx + 1].rstrip()
    return text


def _read_description(skill_md: Path) -> str:
    text = skill_md.read_text()
    match = re.search(r"^---\s*\n(.*?)\n---", text, flags=re.DOTALL | re.MULTILINE)
    if not match:
        return ""
    block = match.group(1)
    m = re.search(
        r"^description:\s*(.*?)(?=^\w+:|^\Z)",
        block + "\n",
        flags=re.DOTALL | re.MULTILINE,
    )
    if not m:
        return ""
    body = m.group(1).strip()
    if body.startswith((">", "|")):
        body = body[1:].strip()
    return _first_sentence(body)


def _truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: max(0, width - 3)].rstrip() + "..."


def _collect_nodes() -> dict:
    tree: dict = {}
    for skill_md in sorted(SOURCE.rglob("SKILL.md")):
        rel = skill_md.parent.relative_to(SOURCE)
        cursor = tree
        for part in rel.parts:
            cursor = cursor.setdefault(part, {})
        cursor["__desc__"] = _truncate(_read_description(skill_md), DESC_WIDTH)
    return tree


def _is_leaf(node: dict) -> bool:
    """True if this node has a description and no sub-dirs."""
    if "__desc__" not in node:
        return False
    return all(k == "__desc__" for k in node)


def _sort_children(node: dict) -> list[tuple[str, dict]]:
    children = [(k, v) for k, v in node.items() if k != "__desc__"]
    # Leaves first, then sub-dirs; both groups alphabetical.
    children.sort(key=lambda kv: (not _is_leaf(kv[1]), kv[0]))
    return children


def _render(node: dict, prefix: str, lines: list[str]) -> None:
    children = _sort_children(node)
    for name, child in children:
        if _is_leaf(child):
            lines.append(f"{prefix}├── {name}     ← {child['__desc__']}")
        else:
            label = f"{name}/"
            if "__desc__" in child:
                label = f"{name}/     ← {child['__desc__']}"
            lines.append(f"{prefix}├── {label}")
            _render(child, prefix + "│   ", lines)


def main() -> int:
    if not SOURCE.is_dir():
        print(f"error: {SOURCE} not found", file=sys.stderr)
        return 2
    tree = _collect_nodes()
    body_lines: list[str] = ["agentfiles/"]
    _render(tree, "", body_lines)
    skill_count = sum(1 for _ in SOURCE.rglob("SKILL.md"))
    header = (
        "# Skill Tree\n\n"
        "Auto-generated from `agentfiles/`. Do not edit by hand — run "
        "`python hooks/tools/gen-skill-tree.py` from the repo root.\n\n"
        f"*{skill_count} skills across {len(_sort_children(tree))} top-level "
        "categories.*\n\n"
        "```\n"
    )
    footer = "```\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(header + "\n".join(body_lines) + "\n" + footer)
    print(f"wrote {OUTPUT.relative_to(REPO)} ({skill_count} skills)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
