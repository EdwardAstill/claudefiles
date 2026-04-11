#!/usr/bin/env bash
# bootstrap.sh — install claudefiles from GitHub (or re-run to update)
set -euo pipefail

CLONE_DIR="$HOME/.local/share/claudefiles-src"

# Clone or pull
if [[ -d "$CLONE_DIR/.git" ]]; then
    echo "Updating claudefiles..."
    git -C "$CLONE_DIR" pull --ff-only
else
    echo "Cloning claudefiles..."
    mkdir -p "$(dirname "$CLONE_DIR")"
    git clone https://github.com/EdwardAstill/claudefiles "$CLONE_DIR"
fi

# Note about old clone location
if [[ -d "$HOME/.claudefiles" && ! -L "$HOME/.claudefiles" ]]; then
    echo "Note: old ~/.claudefiles/ clone detected — safe to remove after verifying bootstrap succeeded."
fi

# Install cf Python CLI
echo "Installing cf package..."
uv tool install --force -e "$CLONE_DIR/tools/python/"

# Install skills and bin tools via install.sh (single source of truth)
echo "Installing skills..."
bash "$CLONE_DIR/install.sh" --global "$@"

echo ""
echo "Done! Run 'cf agents' to see installed skills and tools."
