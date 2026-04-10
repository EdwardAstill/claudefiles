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
    git clone https://github.com/EdwardAstill/claudefiles "$CLONE_DIR"
fi

# Note about old clone location
if [[ -d "$HOME/.claudefiles" && ! -L "$HOME/.claudefiles" ]]; then
    echo "Note: old ~/.claudefiles/ clone detected — safe to remove after verifying bootstrap succeeded."
fi

# Install cf package
echo "Installing cf package..."
uv tool install -e "$CLONE_DIR/tools/python/"

# Ensure cf is on PATH for this shell
export PATH="$(uv tool dir --bin):$PATH"

# Install skills
echo "Installing skills..."
cf install --global --source "$CLONE_DIR" "$@"

echo ""
echo "Done! Run 'cf agents' to see installed skills and tools."
