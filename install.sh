#!/usr/bin/env bash
# install.sh — install claudefiles dev-suite skills and bin tools
#
# Usage:
#   ./install.sh --user                        # install all skills + bin
#   ./install.sh --user --category coding      # install only coding/ category
#   ./install.sh --project ./                  # install to project scope
#   ./install.sh --project ./ --category research
#   ./install.sh --dry-run                     # preview without changes
#   ./install.sh --remove                      # remove installed symlinks
#   ./install.sh --list-categories             # show available categories
#
# Valid categories: all (default), management, coding, research

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/manifest.toml"
DEV_SUITE="$SCRIPT_DIR/dev-suite"
BIN_DIR="$SCRIPT_DIR/bin"

MODE=""           # user | project
PROJECT_PATH=""
CATEGORY="all"
DRY_RUN=false
REMOVE=false
LIST_CATS=false

# ── Argument parsing ──────────────────────────────────────────────────────────

i=0
args=("$@")
while [[ $i -lt ${#args[@]} ]]; do
    arg="${args[$i]}"
    case "$arg" in
        --user)             MODE="user" ;;
        --project)          MODE="project" ;;
        --dry-run)          DRY_RUN=true ;;
        --remove)           REMOVE=true ;;
        --list-categories)  LIST_CATS=true ;;
        --category)
            i=$((i+1))
            CATEGORY="${args[$i]}"
            ;;
        /*)   PROJECT_PATH="$arg" ;;
        ./*)  PROJECT_PATH="$(realpath "$arg")" ;;
        .)    PROJECT_PATH="$(realpath "$arg")" ;;
        *)
            if [[ "$MODE" == "project" && -z "$PROJECT_PATH" ]]; then
                PROJECT_PATH="$(realpath "$arg")"
            fi
            ;;
    esac
    i=$((i+1))
done

# ── List categories ───────────────────────────────────────────────────────────

if "$LIST_CATS"; then
    echo "Available categories:"
    echo "  all         — install the full dev-suite (default)"
    for d in "$DEV_SUITE"/*/; do
        [[ -f "$d/SKILL.md" ]] && echo "  $(basename "$d")"
    done
    exit 0
fi

if [[ -z "$MODE" ]]; then
    echo "Error: specify --user or --project <path>" >&2
    echo "Usage: $0 [--user|--project <path>] [--category <name>] [--dry-run] [--remove]" >&2
    exit 1
fi

if [[ "$MODE" == "project" && -z "$PROJECT_PATH" ]]; then
    PROJECT_PATH="$(pwd)"
fi

# ── Resolve skill source and install target ───────────────────────────────────

if [[ "$CATEGORY" == "all" ]]; then
    SKILL_SRC="$DEV_SUITE"
    SKILL_LINK_NAME="dev-suite"
else
    SKILL_SRC="$DEV_SUITE/$CATEGORY"
    SKILL_LINK_NAME="cf-$CATEGORY"
    if [[ ! -d "$SKILL_SRC" ]]; then
        echo "Error: category '$CATEGORY' not found in dev-suite/" >&2
        echo "Run $0 --list-categories to see available categories." >&2
        exit 1
    fi
fi

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
    do_symlink "$SKILL_SRC" "$SKILLS_TARGET/$SKILL_LINK_NAME"

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
    do_remove "$SKILLS_TARGET/$SKILL_LINK_NAME"

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
