#!/usr/bin/env bash
# install.sh — install agentfiles skills and bin tools for both Claude and Gemini
#
# Usage:
#   ./install.sh --global                              # install full agentfiles + bin globally
#   ./install.sh --global --category coding           # install one category globally
#   ./install.sh --global --skill agent-manager       # install one skill globally (bootstrap)
#   ./install.sh --local                              # install to current project
#   ./install.sh --local /path/to/project             # install to specific project
#   ./install.sh --local --category research          # install one category to current project
#   ./install.sh --from github:owner/repo --global    # clone from GitHub then install
#   ./install.sh --dry-run                            # preview without changes
#   ./install.sh --remove                             # remove installed symlinks
#   ./install.sh --list-categories                    # show available categories

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/manifest.toml"
AGENTFILES="$SCRIPT_DIR/agentfiles"

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

if [[ "$SOURCE" == "github" ]]; then
    REPO_DIR="$HOME/.agentfiles"

    if [[ -d "$REPO_DIR/.git" ]]; then
        echo "  Updating cached repo from github.com/$GITHUB_REPO ..."
        git -C "$REPO_DIR" pull --ff-only --quiet
        echo "  Up to date: $REPO_DIR"
    else
        echo "  Cloning github.com/$GITHUB_REPO → $REPO_DIR ..."
        mkdir -p "$(dirname "$REPO_DIR")"
        git clone --quiet "https://github.com/$GITHUB_REPO" "$REPO_DIR"
        echo "  Cloned."
    fi

    # Override all source paths to use the cached copy
    AGENTFILES="$REPO_DIR/agentfiles"
    BIN_DIR="$REPO_DIR/bin"
    MANIFEST="$REPO_DIR/manifest.toml"
fi

# ── List categories ───────────────────────────────────────────────────────────

if "$LIST_CATS"; then
    echo "Available categories:"
    echo "  all         — install the full agentfiles (default)"
    for d in "$AGENTFILES"/*/; do
        [[ -f "$d/SKILL.md" ]] && echo "  $(basename "$d")"
    done
    exit 0
fi

if [[ -z "$MODE" ]]; then
    echo "Error: specify --global (or --local <path>)" >&2
    exit 1
fi

if [[ "$MODE" == "project" && -z "$PROJECT_PATH" ]]; then
    PROJECT_PATH="$(pwd)"
fi

# ── Resolve install targets ───────────────────────────────────────────────────

TARGETS=()
if [[ "$MODE" == "user" ]]; then
    TARGETS+=("$HOME/.claude/skills")
    TARGETS+=("$HOME/.gemini/skills")
else
    TARGETS+=("$PROJECT_PATH/.claude/skills")
    TARGETS+=("$PROJECT_PATH/.gemini/skills")
fi

# ── Resolve skill source ──────────────────────────────────────────────────────

SKILL_SRC=""
SKILL_LINK_NAME=""

if [[ -n "$SKILL_NAME" ]]; then
    while IFS= read -r skill_md; do
        found_name="$(awk '/^name:/ { gsub(/^name: */, ""); print; exit }' "$skill_md" 2>/dev/null)"
        if [[ "$found_name" == "$SKILL_NAME" ]]; then
            SKILL_SRC="$(dirname "$skill_md")"
            SKILL_LINK_NAME="$SKILL_NAME"
            break
        fi
    done < <(find "$AGENTFILES" -name "SKILL.md" 2>/dev/null)

    if [[ -z "$SKILL_SRC" ]]; then
        echo "Error: skill '$SKILL_NAME' not found in agentfiles" >&2
        exit 1
    fi

elif [[ "$CATEGORY" == "all" ]]; then
    SKILLS_FLAT="$SCRIPT_DIR/skills"
    mkdir -p "$SKILLS_FLAT"
    while IFS= read -r link; do
        name="$(basename "$link")"
        if ! find "$AGENTFILES" -name "SKILL.md" | xargs grep -l "^name: $name$" &>/dev/null; then
            rm "$link"
        fi
    done < <(find "$SKILLS_FLAT" -maxdepth 1 -type l 2>/dev/null)

    while IFS= read -r skill_md; do
        dir="$(dirname "$skill_md")"
        sub_skills=$(find "$dir" -mindepth 2 -name "SKILL.md" 2>/dev/null | wc -l)
        if [[ "$sub_skills" -eq 0 ]]; then
            name=$(awk '/^name:/ { gsub(/^name: */, ""); print; exit }' "$skill_md")
            rel="$(python3 -c "import os; print(os.path.relpath('$dir', '$SKILLS_FLAT'))")"
            ln -sf "$rel" "$SKILLS_FLAT/$name"
        fi
    done < <(find "$AGENTFILES" -name "SKILL.md")
    SKILL_SRC="$SKILLS_FLAT"
else
    SKILL_SRC="$AGENTFILES/$CATEGORY"
    SKILL_LINK_NAME="af-$CATEGORY"
fi

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

wire_gemini_hooks() {
    local gemini_settings
    local target_skills
    if [[ "$MODE" == "user" ]]; then
        gemini_settings="$HOME/.gemini/settings.json"
        target_skills="$HOME/.gemini"
    else
        gemini_settings="$PROJECT_PATH/.gemini/settings.json"
        target_skills="$PROJECT_PATH/.gemini"
    fi
    
    echo "Gemini Hooks:"
    if "$DRY_RUN"; then
        echo "  [dry-run] would configure Gemini hooks in $gemini_settings"
        return
    fi
    
    bash "$SCRIPT_DIR/hooks/install-gemini-hooks.sh" --target "$target_skills"
}

# ── Install ───────────────────────────────────────────────────────────────────

install_all() {
    echo "Installing agentfiles"
    
    # Install CLI for global mode
    if [[ "$MODE" == "user" ]]; then
        if "$DRY_RUN"; then
            echo "  [dry-run] uv tool install -e $SCRIPT_DIR/tools/python/"
        else
            uv tool install --force -e "$SCRIPT_DIR/tools/python/" --quiet
            echo "  [ok] af CLI installed"
        fi
    fi

    for target in "${TARGETS[@]}"; do
        echo "Target: $target"
        if [[ -z "$SKILL_LINK_NAME" ]]; then
            while IFS= read -r skill_dir; do
                name="$(basename "$skill_dir")"
                do_symlink "$(realpath "$skill_dir")" "$target/$name"
            done < <(find "$SKILL_SRC" -maxdepth 1 -mindepth 1 -type l | sort)
        else
            do_symlink "$SKILL_SRC" "$target/$SKILL_LINK_NAME"
        fi
        
        # Link hooks specifically for Claude convention
        if [[ "$target" == *".claude/skills" ]]; then
            local hooks_src="$SCRIPT_DIR/hooks"
            do_symlink "$hooks_src" "$target/hooks"
        fi
        # Link hooks for Gemini as well (convention-over-config is easier)
        if [[ "$target" == *".gemini/skills" ]]; then
            local hooks_src="$SCRIPT_DIR/hooks"
            do_symlink "$hooks_src" "$target/hooks"
        fi
    done

    if [[ "$MODE" == "user" ]]; then
        if "$DRY_RUN"; then
            bash "$SCRIPT_DIR/hooks/install-hooks.sh" --dry-run
            wire_gemini_hooks
        else
            bash "$SCRIPT_DIR/hooks/install-hooks.sh"
            wire_gemini_hooks
        fi
    fi

    # Gitignore
    if [[ "$MODE" == "project" ]]; then
        local ignore="$PROJECT_PATH/.gitignore"
        if "$DRY_RUN"; then
            echo "  [dry-run] add .agentfiles/ to $ignore"
        elif ! grep -qxF '.agentfiles/' "$ignore" 2>/dev/null; then
            echo '.agentfiles/' >> "$ignore"
        fi
    fi
}

remove_all() {
    for target in "${TARGETS[@]}"; do
        echo "Removing from: $target"
        if [[ -z "$SKILL_LINK_NAME" ]]; then
            while IFS= read -r skill_dir; do
                name="$(basename "$skill_dir")"
                do_remove "$target/$name"
            done < <(find "$SKILL_SRC" -maxdepth 1 -mindepth 1 -type l | sort)
        else
            do_remove "$target/$SKILL_LINK_NAME"
        fi
        # Remove hooks link
        if [[ "$target" == *".claude/skills" || "$target" == *".gemini/skills" ]]; then
            do_remove "$target/hooks"
        fi
    done
}

if "$REMOVE"; then
    remove_all
else
    install_all
fi
