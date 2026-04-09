#!/usr/bin/env bash
# install.sh — install claudefiles skills and bin tools
#
# Usage:
#   ./install.sh --global                              # install full dev-suite + bin globally
#   ./install.sh --global --category coding           # install one category globally
#   ./install.sh --global --skill agent-manager       # install one skill globally (bootstrap)
#   ./install.sh --local                              # install to current project
#   ./install.sh --local /path/to/project             # install to specific project
#   ./install.sh --local --category research          # install one category to current project
#   ./install.sh --from github:owner/repo --global    # clone from GitHub then install
#   ./install.sh --dry-run                            # preview without changes
#   ./install.sh --remove                             # remove installed symlinks
#   ./install.sh --list-categories                    # show available categories
#
# Source options:
#   (default)                    use this repo (where install.sh lives)
#   --from github:owner/repo     clone/update from GitHub, install from that copy
#
# Scope options:
#   --global  (or --user)        install to ~/.claude/skills/ + ~/.local/bin/
#   --local   (or --project)     install to <project>/.claude/skills/
#
# Granularity options (pick one):
#   (none)                       install full dev-suite as one symlink
#   --category <name>            install one top-level category (management, coding, research)
#   --skill <name>               install one named skill by its SKILL.md name field
#
# Bootstrap (install just the manager, then use it to install the rest):
#   curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/install.sh \
#     | bash -s -- --global --from github:EdwardAstill/claudefiles --skill agent-manager

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/manifest.toml"
DEV_SUITE="$SCRIPT_DIR/dev-suite"
BIN_DIR="$SCRIPT_DIR/bin"

MODE=""           # user | project
SOURCE="local"    # local | github
GITHUB_REPO=""
PROJECT_PATH=""
CATEGORY="all"    # all | <category-name>
SKILL_NAME=""     # empty = category/all mode; set = single-skill mode
DRY_RUN=false
REMOVE=false
LIST_CATS=false

# ── Argument parsing ──────────────────────────────────────────────────────────

i=0
args=("$@")
while [[ $i -lt ${#args[@]} ]]; do
    arg="${args[$i]}"
    case "$arg" in
        --global|--user)    MODE="user" ;;
        --local|--project)  MODE="project" ;;
        --dry-run)          DRY_RUN=true ;;
        --remove)           REMOVE=true ;;
        --list-categories)  LIST_CATS=true ;;
        --from)
            i=$((i+1))
            FROM_VAL="${args[$i]}"
            if [[ "$FROM_VAL" == github:* ]]; then
                SOURCE="github"
                GITHUB_REPO="${FROM_VAL#github:}"
            else
                echo "Error: unknown --from value '$FROM_VAL'. Expected: github:<owner>/<repo>" >&2
                exit 1
            fi
            ;;
        --category)
            i=$((i+1))
            CATEGORY="${args[$i]}"
            ;;
        --skill)
            i=$((i+1))
            SKILL_NAME="${args[$i]}"
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

# ── Resolve GitHub source ─────────────────────────────────────────────────────
# If --from github:owner/repo, clone or update into a local cache directory,
# then point all paths at that cache. The rest of the script is source-agnostic.

if [[ "$SOURCE" == "github" ]]; then
    CACHE_BASE="$HOME/.local/share/claudefiles-src"
    REPO_SLUG="$(echo "$GITHUB_REPO" | tr '/' '-')"
    REPO_DIR="$CACHE_BASE/$REPO_SLUG"

    if [[ -d "$REPO_DIR/.git" ]]; then
        echo "  Updating cached repo from github.com/$GITHUB_REPO ..."
        git -C "$REPO_DIR" pull --ff-only --quiet
        echo "  Up to date: $REPO_DIR"
    else
        echo "  Cloning github.com/$GITHUB_REPO → $REPO_DIR ..."
        mkdir -p "$CACHE_BASE"
        git clone --quiet "https://github.com/$GITHUB_REPO" "$REPO_DIR"
        echo "  Cloned."
    fi

    # Override all source paths to use the cached copy
    DEV_SUITE="$REPO_DIR/dev-suite"
    BIN_DIR="$REPO_DIR/bin"
    MANIFEST="$REPO_DIR/manifest.toml"
fi

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
    echo "Error: specify --global (or --local <path>)" >&2
    echo "Usage: $0 [--global|--local [<path>]] [--from github:<owner>/<repo>] [--category <name>|--skill <name>] [--dry-run] [--remove]" >&2
    exit 1
fi

if [[ "$MODE" == "project" && -z "$PROJECT_PATH" ]]; then
    PROJECT_PATH="$(pwd)"
fi

# ── Resolve install target ────────────────────────────────────────────────────

if [[ "$MODE" == "user" ]]; then
    SKILLS_TARGET="$HOME/.claude/skills"
else
    SKILLS_TARGET="$PROJECT_PATH/.claude/skills"
fi

BIN_TARGET="$HOME/.local/bin"

# ── Resolve skill source and link name ───────────────────────────────────────
# Three modes: full dev-suite, one category, or one named skill.

SKILL_SRC=""
SKILL_LINK_NAME=""

if [[ -n "$SKILL_NAME" ]]; then
    # Single-skill mode: find the skill directory by SKILL.md name field
    while IFS= read -r skill_md; do
        found_name="$(awk '/^name:/ { gsub(/^name: */, ""); print; exit }' "$skill_md" 2>/dev/null)"
        if [[ "$found_name" == "$SKILL_NAME" ]]; then
            SKILL_SRC="$(dirname "$skill_md")"
            SKILL_LINK_NAME="$SKILL_NAME"
            break
        fi
    done < <(find "$DEV_SUITE" -name "SKILL.md" 2>/dev/null)

    if [[ -z "$SKILL_SRC" ]]; then
        echo "Error: skill '$SKILL_NAME' not found in dev-suite" >&2
        echo "Run $0 --list-categories to see available categories, or check dev-suite/ for skill names." >&2
        exit 1
    fi

elif [[ "$CATEGORY" == "all" ]]; then
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
    if [[ -n "$SKILL_NAME" ]]; then
        echo "Installing claudefiles skill: $SKILL_NAME"
    elif [[ "$CATEGORY" != "all" ]]; then
        echo "Installing claudefiles category: $CATEGORY"
    else
        echo "Installing claudefiles dev-suite"
    fi

    echo "  Source        : $SKILL_SRC"
    echo "  Skills target : $SKILLS_TARGET"
    [[ "$MODE" == "user" && -z "$SKILL_NAME" && "$CATEGORY" == "all" ]] && echo "  Bin target    : $BIN_TARGET"
    "$DRY_RUN" && echo "  [dry-run mode — no changes will be made]"
    echo ""

    echo "Skills:"
    do_symlink "$SKILL_SRC" "$SKILLS_TARGET/$SKILL_LINK_NAME"

    # Only install bin tools on global installs, and only for full dev-suite or all-category installs
    if [[ "$MODE" == "user" && -z "$SKILL_NAME" && "$CATEGORY" == "all" ]]; then
        echo ""
        echo "Bin tools:"
        while IFS= read -r entry; do
            [[ -z "$entry" ]] && continue
            do_symlink "$BIN_DIR/$entry" "$BIN_TARGET/$entry"
            chmod +x "$BIN_DIR/$entry" 2>/dev/null || true
        done < <(parse_bin_entries)
    fi

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
    echo "Removing claudefiles skills"
    "$DRY_RUN" && echo "  [dry-run mode — no changes will be made]"
    echo ""

    echo "Skills:"
    do_remove "$SKILLS_TARGET/$SKILL_LINK_NAME"

    if [[ "$MODE" == "user" && -z "$SKILL_NAME" && "$CATEGORY" == "all" ]]; then
        echo ""
        echo "Bin tools:"
        while IFS= read -r entry; do
            [[ -z "$entry" ]] && continue
            do_remove "$BIN_TARGET/$entry"
        done < <(parse_bin_entries)
    fi

    echo ""
    echo "Done."
}

# ── Run ───────────────────────────────────────────────────────────────────────

if "$REMOVE"; then
    remove_all
else
    install_all
fi
