#!/usr/bin/env python3
"""Generate skill-tree.md from agentfiles/ directory structure."""
import re
from pathlib import Path

ROOT = Path("/home/eastill/projects/agentfiles/agentfiles")

def read_frontmatter(skill_md: Path) -> tuple[str, str]:
    text = skill_md.read_text()
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return skill_md.parent.name, ""
    fm = m.group(1)
    name_m = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
    desc_m = re.search(r"^description:\s*>?\s*\n?((?:\s*.+\n?)+)", fm, re.MULTILINE)
    name = name_m.group(1).strip() if name_m else skill_md.parent.name
    desc = ""
    if desc_m:
        desc = " ".join(line.strip() for line in desc_m.group(1).splitlines()).strip()
        desc = re.sub(r"\s+", " ", desc)
        # First sentence only for brevity
        desc = desc.split(".")[0].strip() + "."
        if len(desc) > 100:
            desc = desc[:97] + "..."
    return name, desc

def tree():
    # Group skills by top-level category and subcategory
    categories = {}
    for skill_md in sorted(ROOT.rglob("SKILL.md")):
        rel = skill_md.relative_to(ROOT)
        parts = rel.parts[:-1]  # drop SKILL.md
        if not parts:
            continue
        top = parts[0]
        sub = parts[1] if len(parts) >= 2 else None
        name, desc = read_frontmatter(skill_md)
        # Router if this dir has children with SKILL.md
        children = list(skill_md.parent.rglob("*/SKILL.md"))
        is_router = len(children) > 0
        categories.setdefault(top, []).append((parts, name, desc, is_router))
    return categories

def emit(categories):
    lines = ["# Skill Tree", "",
             "Auto-generated from `agentfiles/`. Do not edit by hand — run `af tree --regenerate` (or `python hooks/tools/gen-skill-tree.py`).",
             "", "```", "agentfiles/"]
    for top in sorted(categories):
        entries = categories[top]
        # Sort by depth then path
        entries.sort(key=lambda e: (len(e[0]), e[0]))
        lines.append(f"├── {top}/")
        # Group by sub
        seen_sub = set()
        for parts, name, desc, is_router in entries:
            if len(parts) == 1:
                # category router itself
                continue
            sub = parts[1] if len(parts) > 2 else None
            leaf_name = parts[-1]
            if sub and sub not in seen_sub:
                seen_sub.add(sub)
                lines.append(f"│   ├── {sub}/")
            indent = "│   │   " if sub else "│   "
            prefix = "├── "
            suffix = f"     ← {desc}" if desc else ""
            lines.append(f"{indent}{prefix}{leaf_name}{suffix}")
    lines.append("```")
    lines.append("")
    total = sum(len([e for e in v if len(e[0]) > 1]) for v in categories.values())
    lines.append(f"**Total: {total} skills across {len(categories)} top-level categories.**")
    lines.append("")
    return "\n".join(lines)

print(emit(tree()))
