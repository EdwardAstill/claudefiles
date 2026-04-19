"""af audit — manifest consistency audit, scoped to the agentfiles repo.

Runs the full set of consistency checks defined in the `audit` subagent
(agentfiles/agents/audit.md). Emits a structured per-check report.

Checks:
  1. skill dirs → manifest
  2. manifest → skill dirs
  3. agent files → manifest
  4. manifest → agent files
  5. skill cli → [cli.*]
  6. [cli.*] → skill reference
  7. cli tools in PATH
  8. skills/ registry symlinks are valid and complete
  9. hook script health (shebangs resolve, declared deps resolvable,
     bash binaries on PATH, hooks.json commands executable)
 10. plan pair drift (docs/plans/*.yaml <-> .md stay in sync)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import typer

app = typer.Typer(help="Audit the agentfiles manifest for consistency.")


_TOML_SECTION_RE = re.compile(r'^\[(skills|agents|cli|modes)\.(?:"([^"]+)"|([^\]"]+))\]')
_CLI_LIST_RE = re.compile(r'cli\s*=\s*\[([^\]]+)\]')


def _find_repo_root() -> Path:
    for p in (Path.cwd(), *Path.cwd().parents):
        if (p / "manifest.toml").is_file() and (p / "agentfiles").is_dir():
            return p
    typer.echo("error: not inside an agentfiles repo (no manifest.toml + agentfiles/)", err=True)
    raise typer.Exit(code=2)


def _parse_manifest(path: Path) -> dict[str, set[str]]:
    sections: dict[str, set[str]] = {
        "skills": set(),
        "agents": set(),
        "cli": set(),
        "modes": set(),
    }
    declared_cli: set[str] = set()
    for line in path.read_text().splitlines():
        m = _TOML_SECTION_RE.match(line.strip())
        if m:
            # Group 2 = quoted key body; group 3 = bare key. Exactly one fires.
            sections[m.group(1)].add(m.group(2) or m.group(3))
            continue
        cli_m = _CLI_LIST_RE.search(line)
        if cli_m:
            for name in re.findall(r'"([^"]+)"', cli_m.group(1)):
                declared_cli.add(name)
    sections["declared_cli"] = declared_cli
    return sections


def _skills_on_disk(agentfiles_dir: Path) -> set[str]:
    names: set[str] = set()
    for skill_md in agentfiles_dir.rglob("SKILL.md"):
        # Skip agents/ dir (not a skill dir)
        if "agents" in skill_md.parent.parts:
            continue
        for line in skill_md.read_text().splitlines():
            if line.startswith("name:"):
                names.add(line.split(":", 1)[1].strip())
                break
    return names


def _modes_on_disk(agentfiles_dir: Path) -> set[str]:
    modes_dir = agentfiles_dir / "modes"
    if not modes_dir.is_dir():
        return set()
    names: set[str] = set()
    for mode_md in modes_dir.glob("*/MODE.md"):
        for line in mode_md.read_text().splitlines():
            if line.startswith("name:"):
                names.add(line.split(":", 1)[1].strip())
                break
    return names


def _agents_on_disk(agentfiles_dir: Path) -> set[str]:
    agents_dir = agentfiles_dir / "agents"
    if not agents_dir.is_dir():
        return set()
    names: set[str] = set()
    for md in agents_dir.glob("*.md"):
        for line in md.read_text().splitlines():
            if line.startswith("name:"):
                names.add(line.split(":", 1)[1].strip())
                break
        else:
            names.add(md.stem)
    return names


def _registry_symlinks(repo_root: Path) -> tuple[set[str], list[str]]:
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        return set(), []
    names: set[str] = set()
    problems: list[str] = []
    for entry in skills_dir.iterdir():
        if entry.name.startswith("."):
            continue
        if not entry.is_symlink():
            problems.append(f"skills/{entry.name} — not a symlink (real file/dir, should be ../agentfiles/...)")
            continue
        target = entry.resolve()
        if not target.exists():
            problems.append(f"skills/{entry.name} — broken symlink → {entry.readlink()}")
            continue
        names.add(entry.name)
    return names, problems


# ── Check 9 helpers: hook script health ──────────────────────────────────────

_UV_SCRIPT_BLOCK_RE = re.compile(
    r"#\s*///\s*script\s*\n(?P<body>(?:#.*\n)+?)#\s*///",
    re.MULTILINE,
)
_DEPS_LINE_RE = re.compile(r"dependencies\s*=\s*\[(?P<body>[^\]]*)\]", re.DOTALL)
_DEP_STRING_RE = re.compile(r'"([^"]+)"|\'([^\']+)\'')
_BASH_BIN_RE = re.compile(
    r"(?:^|[\s;|&`$(])"
    r"(jq|git|af|uv|python3?|curl|wget|grep|sed|awk|rg|fzf|notify-send|"
    r"gh|npm|node|bun|cargo|rustc|make|docker|kubectl|ssh|rsync)"
    r"(?=\s|$|[);|&`])"
)
_HOOK_CMD_RE = re.compile(r'"command"\s*:\s*"([^"]+)"')
# ${CLAUDE_PLUGIN_ROOT} is expanded at hook-invocation time by Claude Code.
_PLUGIN_ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}"


def _parse_uv_script_deps(source: str) -> tuple[bool, list[str], str | None]:
    """Extract declared deps from a PEP 723 inline script block.

    Returns (has_block, deps, error_message). If the file has no block,
    returns (False, [], None) — caller treats as "no deps to validate".
    If the block is malformed, returns (True, [], error).
    """
    m = _UV_SCRIPT_BLOCK_RE.search(source)
    if not m:
        return False, [], None
    body = m.group("body")
    # Strip the leading '# ' from each line to get a TOML-ish body.
    stripped = "\n".join(
        (line[2:] if line.startswith("# ") else (line[1:] if line.startswith("#") else line))
        for line in body.splitlines()
    )
    dep_m = _DEPS_LINE_RE.search(stripped)
    if not dep_m:
        # No deps line → treated as empty.
        return True, [], None
    deps_body = dep_m.group("body")
    deps: list[str] = []
    for tok in _DEP_STRING_RE.finditer(deps_body):
        dep = tok.group(1) or tok.group(2)
        if dep:
            deps.append(dep)
    return True, deps, None


def _parse_shebang(source: str) -> str | None:
    """Return the interpreter path from a shebang, or None if absent."""
    first = source.splitlines()[0] if source else ""
    if not first.startswith("#!"):
        return None
    # `#!/usr/bin/env -S uv run --script` → interpreter is `/usr/bin/env`
    parts = first[2:].strip().split()
    return parts[0] if parts else None


def _dep_package_name(spec: str) -> str:
    """Strip version specifiers / extras from a PEP 508 dep string."""
    # 'requests>=2.0', 'rich[jupyter]~=13', 'foo ; python_version<"3.12"'
    name = re.split(r"[<>=!~;\[\s]", spec, maxsplit=1)[0].strip()
    return name


def _check_dep_resolvable(dep: str, timeout: float = 20.0) -> tuple[bool, str]:
    """Verify a dep spec is resolvable via uv. Does not import it.

    Uses `uv pip install --dry-run` in an ephemeral environment — fast
    enough for an audit (uv caches metadata), and avoids actually
    executing the hook. Returns (ok, error_message).
    """
    if shutil.which("uv") is None:
        return False, "uv not on PATH"
    try:
        proc = subprocess.run(
            ["uv", "pip", "install", "--dry-run", "--quiet", dep],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "UV_NO_PROGRESS": "1"},
        )
    except subprocess.TimeoutExpired:
        return False, f"uv resolution timed out after {timeout}s"
    except OSError as e:
        return False, f"uv invocation failed: {e}"
    if proc.returncode == 0:
        return True, ""
    err = (proc.stderr or proc.stdout or "").strip().splitlines()
    # Return the last non-empty line — usually the most specific error.
    last = next((line for line in reversed(err) if line.strip()), "")
    return False, last or f"uv exited {proc.returncode}"


def _audit_hooks(repo_root: Path) -> list[str]:
    """Validate hook scripts can actually run. Returns a list of issue strings."""
    hooks_dir = repo_root / "hooks"
    if not hooks_dir.is_dir():
        return []

    issues: list[str] = []
    # Iterate hook script files (top-level only — subdirs like hooks/hooks/
    # or hooks/tests/ aren't wired into hooks.json).
    for entry in sorted(hooks_dir.iterdir()):
        if not entry.is_file():
            continue
        if entry.name in {"hooks.json", "README.md"}:
            continue
        if entry.suffix in {".md", ".json", ".toml"}:
            continue
        if entry.name.startswith("install-"):
            # Installers are user-run, not Claude-run hooks.
            continue

        try:
            source = entry.read_text()
        except (OSError, UnicodeDecodeError):
            continue

        # Shebang sanity — first line points at an interpreter that exists.
        interp = _parse_shebang(source)
        if interp is not None and not Path(interp).exists():
            issues.append(
                f"  ✗ hook {entry.name} — shebang interpreter '{interp}' not found\n"
                f"    → fix: install {Path(interp).name} or update the shebang"
            )

        if entry.suffix == ".py":
            has_block, deps, block_err = _parse_uv_script_deps(source)
            if block_err:
                issues.append(f"  ✗ hook {entry.name} — malformed uv-script block: {block_err}")
            for spec in deps:
                pkg = _dep_package_name(spec)
                ok, err = _check_dep_resolvable(spec)
                if not ok:
                    issues.append(
                        f"  ✗ hook {entry.name} — declared dep '{spec}' not resolvable: {err}\n"
                        f"    → fix: uv pip install {pkg}"
                    )
        else:
            # Treat as a shell script — scan for binary invocations.
            seen: set[str] = set()
            for m in _BASH_BIN_RE.finditer(source):
                seen.add(m.group(1))
            for binary in sorted(seen):
                # `python` is acceptable if `python3` exists.
                if binary == "python" and shutil.which("python3") is not None:
                    continue
                if shutil.which(binary) is None:
                    # Shell scripts often fall back gracefully (e.g. the
                    # statusline tries jq then python3). Only flag if both
                    # the binary AND common aliases are missing — here we
                    # trust the script's own `command -v` guards and flag
                    # only binaries we're confident are hard requirements.
                    # To keep noise low, flag once per (hook, binary).
                    issues.append(
                        f"  ? hook {entry.name} — references '{binary}' but not on PATH\n"
                        f"    → fix: install {binary} (may be optional if script guards with `command -v`)"
                    )

    # hooks.json commands resolve and are executable.
    hooks_json = hooks_dir / "hooks.json"
    if hooks_json.is_file():
        try:
            cfg = json.loads(hooks_json.read_text())
        except json.JSONDecodeError as e:
            issues.append(f"  ✗ hooks/hooks.json — invalid JSON: {e}")
            cfg = None
        if cfg:
            for cmd in _extract_hook_commands(cfg):
                resolved = cmd.replace(_PLUGIN_ROOT_VAR, str(repo_root)).strip('"').strip()
                # Strip surrounding quotes left from the JSON spec.
                if resolved.startswith('"') and resolved.endswith('"'):
                    resolved = resolved[1:-1]
                path = Path(resolved)
                if not path.exists():
                    issues.append(
                        f"  ✗ hooks.json references {cmd} — resolved path {resolved} does not exist\n"
                        f"    → fix: update hooks.json or restore the missing file"
                    )
                elif not os.access(path, os.X_OK):
                    issues.append(
                        f"  ✗ hooks.json references {cmd} — {resolved} is not executable\n"
                        f"    → fix: chmod +x {resolved}"
                    )

    return issues


def _audit_plan_pairs(repo_root: Path) -> tuple[list[str], int]:
    """Run the same drift logic as `af check plans`, scoped to docs/plans.

    Returns (issues, pair_count). Reuses `af.check.check_plan_pair` — no
    duplicated drift logic.
    """
    from af import check as _check  # local import avoids circular concerns

    plans_dir = repo_root / "docs" / "plans"
    if not plans_dir.is_dir():
        return [], 0

    issues: list[str] = []
    pairs: list[tuple[Path, Path]] = []
    for yaml_path in sorted(plans_dir.glob("*.yaml")):
        md_path = yaml_path.with_suffix(".md")
        if md_path.exists():
            pairs.append((yaml_path, md_path))

    for yaml_path, md_path in pairs:
        for msg in _check.check_plan_pair(yaml_path, md_path):
            issues.append(
                f"  ✗ plan '{yaml_path.name}' — {msg}\n"
                f"    → fix: reconcile {yaml_path.name} with {md_path.name} "
                f"(see `af check plans`)"
            )
    return issues, len(pairs)


def _extract_hook_commands(cfg: dict) -> list[str]:
    """Flatten hooks.json into a list of command strings."""
    out: list[str] = []
    for event_entries in (cfg.get("hooks") or {}).values():
        if not isinstance(event_entries, list):
            continue
        for entry in event_entries:
            for h in (entry or {}).get("hooks", []):
                cmd = h.get("command")
                if isinstance(cmd, str):
                    out.append(cmd)
    return out


@app.callback(invoke_without_command=True)
def audit(
    fix: bool = typer.Option(False, "--fix", help="Auto-repair obvious drift (missing registry symlinks)."),
):
    """Run the full manifest consistency audit."""
    repo_root = _find_repo_root()
    agentfiles_dir = repo_root / "agentfiles"
    manifest_path = repo_root / "manifest.toml"

    manifest = _parse_manifest(manifest_path)
    disk_skills = _skills_on_disk(agentfiles_dir)
    disk_agents = _agents_on_disk(agentfiles_dir)
    disk_modes = _modes_on_disk(agentfiles_dir)
    registry_skills, registry_problems = _registry_symlinks(repo_root)

    issues: list[str] = []
    passed: list[str] = []

    # Check 1: skill dirs → manifest
    missing_in_manifest = disk_skills - manifest["skills"]
    if missing_in_manifest:
        for n in sorted(missing_in_manifest):
            issues.append(f"  ✗ skill '{n}' on disk — add [skills.{n}] entry to manifest.toml")
        passed.append(f"CHECK 1 (skill dirs → manifest): {len(disk_skills) - len(missing_in_manifest)}/{len(disk_skills)} ok, {len(missing_in_manifest)} missing")
    else:
        passed.append(f"CHECK 1 (skill dirs → manifest): ✓ all {len(disk_skills)} registered")

    # Check 2: manifest → skill dirs
    orphan_skill_entries = manifest["skills"] - disk_skills
    if orphan_skill_entries:
        for n in sorted(orphan_skill_entries):
            issues.append(f"  ✗ manifest [skills.{n}] has no SKILL.md — create or remove the entry")

    # Check 3: agent files → manifest
    missing_agent_entries = disk_agents - manifest["agents"]
    if missing_agent_entries:
        for n in sorted(missing_agent_entries):
            issues.append(f"  ✗ agent '{n}' on disk — add [agents.{n}] entry to manifest.toml")

    # Check 4: manifest → agent files
    orphan_agent_entries = manifest["agents"] - disk_agents
    if orphan_agent_entries:
        for n in sorted(orphan_agent_entries):
            issues.append(f"  ✗ manifest [agents.{n}] has no .md file — create or remove the entry")

    # Check 5: skill cli → [cli.*]
    declared = manifest["declared_cli"]
    registered = manifest["cli"]
    undeclared_cli = declared - registered
    if undeclared_cli:
        for n in sorted(undeclared_cli):
            issues.append(f"  ✗ CLI '{n}' referenced by a skill but [cli.{n}] missing from manifest")

    # Check 6: [cli.*] → skill reference
    orphan_cli = registered - declared
    if orphan_cli:
        for n in sorted(orphan_cli):
            issues.append(f"  ✗ [cli.{n}] registered but no skill declares cli = [\"{n}\"]")

    # Check 7: cli tools on PATH
    missing_cli = [n for n in sorted(registered) if shutil.which(n) is None]
    if missing_cli:
        for n in missing_cli:
            issues.append(f"  ✗ CLI '{n}' not on PATH — see [cli.{n}] install hint in manifest.toml")

    # Check 8: registry symlinks
    if registry_problems:
        for p in registry_problems:
            issues.append(f"  ✗ {p}")
    missing_registry = disk_skills - registry_skills
    if missing_registry:
        for n in sorted(missing_registry):
            issues.append(f"  ✗ agentfiles skill '{n}' has no skills/{n} registry symlink — af install won't see it")

    # Check 9: hook script health
    hook_issues = _audit_hooks(repo_root)
    issues.extend(hook_issues)
    if not hook_issues:
        hooks_dir = repo_root / "hooks"
        n_hooks = 0
        if hooks_dir.is_dir():
            n_hooks = sum(
                1 for e in hooks_dir.iterdir()
                if e.is_file()
                and e.suffix not in {".md", ".json", ".toml"}
                and e.name != "hooks.json"
                and not e.name.startswith("install-")
            )
        passed.append(f"CHECK 9 (hook script health): ✓ all {n_hooks} hooks resolve")

    # Check 10: plan pair drift
    plan_issues, plan_pair_count = _audit_plan_pairs(repo_root)
    issues.extend(plan_issues)
    if not plan_issues:
        if plan_pair_count == 0:
            passed.append("CHECK 10 (plan pair drift): ✓ no plan pairs to check")
        else:
            passed.append(
                f"CHECK 10 (plan pair drift): ✓ all {plan_pair_count} pair(s) in sync"
            )

    # Check 11: modes on disk ↔ manifest
    missing_mode_entries = disk_modes - manifest["modes"]
    orphan_mode_entries = manifest["modes"] - disk_modes
    if missing_mode_entries:
        for n in sorted(missing_mode_entries):
            issues.append(
                f"  ✗ mode '{n}' on disk — add [modes.{n}] entry to manifest.toml"
            )
    if orphan_mode_entries:
        for n in sorted(orphan_mode_entries):
            issues.append(
                f"  ✗ manifest [modes.{n}] has no MODE.md — create or remove the entry"
            )
    if not missing_mode_entries and not orphan_mode_entries:
        passed.append(f"CHECK 11 (mode dirs ↔ manifest): ✓ all {len(disk_modes)} registered")

    # ── --fix mode: repair safely-repairable drift ──────────────────────────
    if fix:
        fixed: list[str] = []
        # Fix 8a: create missing registry symlinks
        skills_by_name: dict[str, Path] = {}
        for skill_md in agentfiles_dir.rglob("SKILL.md"):
            if "agents" in skill_md.parent.parts:
                continue
            for line in skill_md.read_text().splitlines():
                if line.startswith("name:"):
                    skills_by_name[line.split(":", 1)[1].strip()] = skill_md.parent
                    break
        skills_dir = repo_root / "skills"
        skills_dir.mkdir(exist_ok=True)
        for name in sorted(missing_registry):
            src = skills_by_name.get(name)
            if src is None:
                continue
            rel = Path("..") / src.relative_to(repo_root)
            dst = skills_dir / name
            if dst.exists() or dst.is_symlink():
                continue
            dst.symlink_to(rel)
            fixed.append(f"  ✓ created skills/{name} → {rel}")

        # Fix 8b: remove broken registry symlinks
        for entry in list(skills_dir.iterdir()):
            if entry.is_symlink() and not entry.exists():
                target = entry.readlink()
                entry.unlink()
                fixed.append(f"  ✓ removed broken symlink skills/{entry.name} (was → {target})")

        if fixed:
            typer.echo("")
            typer.echo("Auto-repaired:")
            for line in fixed:
                typer.echo(line)
            typer.echo(f"  ({len(fixed)} fixes applied — re-run `af audit` to see remaining issues)")

    # Render
    for line in passed:
        typer.echo(line)
    if issues:
        typer.echo("")
        typer.echo("Issues:")
        for line in issues:
            typer.echo(line)

    total_checks = 11
    failed_checks = sum([
        bool(missing_in_manifest),
        bool(orphan_skill_entries),
        bool(missing_agent_entries),
        bool(orphan_agent_entries),
        bool(undeclared_cli),
        bool(orphan_cli),
        bool(missing_cli),
        bool(registry_problems or missing_registry),
        bool(hook_issues),
        bool(plan_issues),
        bool(missing_mode_entries or orphan_mode_entries),
    ])
    typer.echo("")
    typer.echo(f"SUMMARY: {total_checks - failed_checks}/{total_checks} checks passed, {len(issues)} issue(s)")
    if failed_checks:
        raise typer.Exit(code=1)
