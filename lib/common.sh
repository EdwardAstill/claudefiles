#!/usr/bin/env bash
# common.sh — shared utilities for claudefiles bin scripts
#
# Source this from any bin script:
#   CF_LIB="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)/../lib"
#   source "$CF_LIB/common.sh"
#
# Using readlink -f ensures the real path is resolved even when called via symlink
# from ~/.local/bin/.

# Find the project's git root (or pwd if not in a git repo)
cf_git_root() {
    git rev-parse --show-toplevel 2>/dev/null || pwd
}

# Require git — exit with error if not in a repo
cf_require_git() {
    if ! git rev-parse --show-toplevel &>/dev/null; then
        echo "Error: not inside a git repository" >&2
        exit 1
    fi
}

# Path to the .claudefiles bus directory (does not create it)
cf_bus() {
    echo "$(cf_git_root)/.claudefiles"
}

# Create the bus directory if it doesn't exist, return its path
cf_ensure_bus() {
    local bus
    bus="$(cf_bus)"
    mkdir -p "$bus"
    echo "$bus"
}

# Check if the bus exists and has content
cf_bus_exists() {
    [[ -d "$(cf_bus)" ]]
}

# Append .claudefiles/ to the project's .gitignore if not already present
cf_gitignore_bus() {
    local git_root
    git_root="$(cf_git_root)"
    local ignore="$git_root/.gitignore"
    if ! grep -qxF '.claudefiles/' "$ignore" 2>/dev/null; then
        echo '.claudefiles/' >> "$ignore"
        echo "  [gitignore] added .claudefiles/ to $ignore"
    fi
}
