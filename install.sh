#!/usr/bin/env bash
# install.sh — install claudefiles dev-suite skills and bin tools
#
# Usage:
#   ./install.sh --user              # install to ~/.claude/skills/ and ~/.local/bin/
#   ./install.sh --project ./        # install to ./.claude/skills/ and ~/.local/bin/
#   ./install.sh --project /path     # install to /path/.claude/skills/ and ~/.local/bin/
#   ./install.sh --dry-run           # show what would happen without making changes
#   ./install.sh --remove            # remove installed symlinks
#
# Combine flags:
#   ./install.sh --user --dry-run
#   ./install.sh --project ./ --remove

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/manifest.toml"
DEV_SUITE="$SCRIPT_DIR/dev-suite"
BIN_DIR="$SCRIPT_DIR/bin"

MODE=""           # user | project
PROJECT_PATH=""
DRY_RUN=false
REMOVE=false

# ── Argument parsing ──────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        --user)      MODE="user" ;;
        --project)   MODE="project" ;;
        --dry-run)   DRY_RUN=true ;;
        --remove)    REMOVE=true ;;
        /*)          PROJECT_PATH="$arg" ;;
        ./*)         PROJECT_PATH="$(realpath "$arg")" ;;
        .)           PROJECT_PATH="$(realpath "$arg")" ;;
        *)
            # Allow --project path as next token (handled by positional)
            if [[ "$MODE" == "project" && -z "$PROJECT_PATH" ]]; then
                PROJECT_PATH="$(realpath "$arg")"
            fi
            ;;
    esac
done

if [[ -z "$MODE" ]]; then
    echo "Error: specify --user or --project <path>" >&2
    echo "Usage: $0 [--user|--project <path>] [--dry-run] [--remove]" >&2
    exit 1
fi

if [[ "$MODE" == "project" && -z "$PROJECT_PATH" ]]; then
    PROJECT_PATH="$(pwd)"
fi

# ── Resolve targets ───────────────────────────────────────────────────────────

if [[ "$MODE" == "user" ]]; then
    SKILLS_TARGET="$HOME/.claude/skills"
else
    SKILLS_TARGET="$PROJECT_PATH/.claude/skills"
fi

BIN_TARGET="$HOME/.local/bin"

# ── Helpers ───────────────────────────────────────────────────────────────────

log() { echo "  $*"; }

do_symlink() {
    local src="$1" dst="$2"
    if "$DRY_RUN"; then
        echo "  [dry-run] symlink: $dst → $src"
        return
    fi
    mkdir -p "$(dirname "$dst")"
    if [[ -L "$dst" ]]; then
        echo "  [skip] already linked: $dst"
    elif [[ -e "$dst" ]]; then
        echo "  [warn] exists (not a symlink): $dst — skipping"
    else
        ln -s "$src" "$dst"
        echo "  [link] $dst → $src"
    fi
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
    elif [[ -e "$dst" ]]; then
        echo "  [warn] $dst exists but is not a symlink — skipping"
    else
        echo "  [skip] not found: $dst"
    fi
}

# ── Read bin entries from manifest.toml ───────────────────────────────────────

parse_bin_entries() {
    # Simple TOML parser for [bin] install = ["a", "b"]
    awk '/^\[bin\]/{found=1;next} found && /^\[/{found=0} found' "$MANIFEST" \
        | grep '^install' \
        | sed 's/.*=\s*//' \
        | tr -d '[]"' \
        | tr ',' '\n' \
        | tr -d ' \t' \
        | grep -v '^$'
}

# ── Install ───────────────────────────────────────────────────────────────────

install_all() {
    echo ""
    echo "Installing claudefiles dev-suite"
    echo "  Skills target : $SKILLS_TARGET"
    echo "  Bin target    : $BIN_TARGET"
    "$DRY_RUN" && echo "  [dry-run mode — no changes will be made]"
    echo ""

    echo "Skills:"
    do_symlink "$DEV_SUITE" "$SKILLS_TARGET/dev-suite"

    echo ""
    echo "Bin tools:"
    while IFS= read -r entry; do
        [[ -z "$entry" ]] && continue
        do_symlink "$BIN_DIR/$entry" "$BIN_TARGET/$entry"
        chmod +x "$BIN_DIR/$entry" 2>/dev/null || true
    done < <(parse_bin_entries)

    # Add .claudefiles/ to project .gitignore on project installs
    if [[ "$MODE" == "project" ]]; then
        local ignore="$PROJECT_PATH/.gitignore"
        if "$DRY_RUN"; then
            echo "  [dry-run] add .claudefiles/ to $ignore"
        elif ! grep -qxF '.claudefiles/' "$ignore" 2>/dev/null; then
            echo '.claudefiles/' >> "$ignore"
            echo "  [gitignore] added .claudefiles/ to $ignore"
        else
            echo "  [skip] .claudefiles/ already in $ignore"
        fi
    fi

    echo ""
    echo "Done."
    echo ""
    if ! "$DRY_RUN"; then
        echo "To activate skills, start a new Claude Code session."
        if [[ "$MODE" == "project" ]]; then
            echo "Skills installed to project: $PROJECT_PATH"
            echo "Run cf-init inside the project to populate the agent bus."
        fi
    fi
}

# ── Remove ────────────────────────────────────────────────────────────────────

remove_all() {
    echo ""
    echo "Removing claudefiles dev-suite"
    "$DRY_RUN" && echo "  [dry-run mode — no changes will be made]"
    echo ""

    echo "Skills:"
    do_remove "$SKILLS_TARGET/dev-suite"

    echo ""
    echo "Bin tools:"
    while IFS= read -r entry; do
        [[ -z "$entry" ]] && continue
        do_remove "$BIN_TARGET/$entry"
    done < <(parse_bin_entries)

    echo ""
    echo "Done."
}

# ── Run ───────────────────────────────────────────────────────────────────────

if "$REMOVE"; then
    remove_all
else
    install_all
fi
