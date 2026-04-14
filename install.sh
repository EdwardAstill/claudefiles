#!/usr/bin/env bash
# install.sh — minimal bootstrap for agentfiles
#
# Installs two things:
#   1. The `af` CLI (via uv tool install)
#   2. The `agentfiles-manager` skill globally (symlinked into ~/.claude/skills/ and ~/.gemini/skills/)
#
# Everything else — full skill installation, CLI tool dependencies, per-project
# setup — is handled by `af install`. Run `af install --help` after bootstrap.
#
# Usage:
#   ./install.sh                # bootstrap af CLI + agentfiles-manager
#   ./install.sh --dry-run      # preview without changes
#   ./install.sh --remove       # remove installed symlinks and af CLI
#
# After bootstrap:
#   af install --global         # install all skills + CLI tools globally
#   af install --local          # install skills into current project
#   af install --help           # see all options

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTFILES="$SCRIPT_DIR/agentfiles"

DRY_RUN=false
REMOVE=false

# ── Argument parsing ──────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        --dry-run)  DRY_RUN=true ;;
        --remove)   REMOVE=true ;;
        --help|-h)
            echo "Usage: ./install.sh [--dry-run] [--remove]"
            echo ""
            echo "Bootstrap agentfiles: installs af CLI + agentfiles-manager skill."
            echo "After bootstrap, use 'af install' for everything else."
            exit 0
            ;;
        *)
            echo "Error: unknown argument '$arg'. Use --help for usage." >&2
            exit 1
            ;;
    esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────

do_symlink() {
    local src="$1" dst="$2"
    if "$DRY_RUN"; then
        echo "  [dry-run] symlink: $dst → $src"
        return
    fi
    mkdir -p "$(dirname "$dst")"
    if [[ -L "$dst" ]]; then
        rm "$dst"
    fi
    ln -s "$src" "$dst"
    echo "  [link] $dst → $src"
}

do_remove() {
    local dst="$1"
    if "$DRY_RUN"; then
        echo "  [dry-run] remove: $dst"
        return
    fi
    if [[ -L "$dst" ]]; then
        rm "$dst"
        echo "  [removed] $dst"
    fi
}

# ── Find the agentfiles-manager skill directory ─────────────────────────────

find_skill_dir() {
    local skill_md
    while IFS= read -r skill_md; do
        local found_name
        found_name="$(awk '/^name:/ { gsub(/^name: */, ""); print; exit }' "$skill_md" 2>/dev/null)"
        if [[ "$found_name" == "agentfiles-manager" ]]; then
            dirname "$skill_md"
            return
        fi
    done < <(find "$AGENTFILES" -name "SKILL.md" 2>/dev/null)
    echo ""
}

MANAGER_DIR="$(find_skill_dir)"
if [[ -z "$MANAGER_DIR" ]]; then
    echo "Error: agentfiles-manager skill not found in $AGENTFILES" >&2
    exit 1
fi

# ── Install targets ──────────────────────────────────────────────────────────

CLAUDE_SKILLS="$HOME/.claude/skills"
GEMINI_SKILLS="$HOME/.gemini/skills"

# ── Remove ───────────────────────────────────────────────────────────────────

if "$REMOVE"; then
    echo "Removing agentfiles bootstrap..."
    do_remove "$CLAUDE_SKILLS/agentfiles-manager"
    do_remove "$CLAUDE_SKILLS/hooks"
    do_remove "$GEMINI_SKILLS/agentfiles-manager"
    do_remove "$GEMINI_SKILLS/hooks"
    if "$DRY_RUN"; then
        echo "  [dry-run] uv tool uninstall af"
    else
        uv tool uninstall af 2>/dev/null && echo "  [ok] af CLI removed" || echo "  [skip] af CLI not installed"
    fi
    exit 0
fi

# ── Install ──────────────────────────────────────────────────────────────────

echo "Bootstrapping agentfiles..."

# 1. Install af CLI
if "$DRY_RUN"; then
    echo "  [dry-run] uv tool install -e $SCRIPT_DIR/tools/python/"
else
    uv tool install --force -e "$SCRIPT_DIR/tools/python/" --quiet
    echo "  [ok] af CLI installed"
fi

# 2. Symlink agentfiles-manager skill
for target in "$CLAUDE_SKILLS" "$GEMINI_SKILLS"; do
    if [[ -L "$target" && ! -d "$target" ]]; then
        rm "$target"
    fi
    mkdir -p "$target"
    do_symlink "$MANAGER_DIR" "$target/agentfiles-manager"
done

# 3. Symlink hooks
HOOKS_SRC="$SCRIPT_DIR/hooks"
do_symlink "$HOOKS_SRC" "$CLAUDE_SKILLS/hooks"
do_symlink "$HOOKS_SRC" "$GEMINI_SKILLS/hooks"

# 4. Wire hooks into settings
if "$DRY_RUN"; then
    bash "$SCRIPT_DIR/hooks/install-hooks.sh" --dry-run
    echo "  [dry-run] would configure Gemini hooks"
else
    bash "$SCRIPT_DIR/hooks/install-hooks.sh"
    bash "$SCRIPT_DIR/hooks/install-gemini-hooks.sh" --target "$HOME/.gemini"
fi

echo ""
echo "Bootstrap complete. Next steps:"
echo "  af install              # install all skills + CLI tools globally"
echo "  af install --local      # install skills into current project"
echo "  af install --help       # see all options"
