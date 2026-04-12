#!/usr/bin/env bash
# bootstrap.sh — install claudefiles from GitHub on a new machine
#
# Usage (one-liner):
#   curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
#
# Or clone and run locally:
#   bash bootstrap.sh

set -euo pipefail

CLONE_DIR="$HOME/.local/share/claudefiles-src"

if [[ -d "$CLONE_DIR/.git" ]]; then
    echo "Updating claudefiles..."
    git -C "$CLONE_DIR" pull --ff-only
else
    echo "Cloning claudefiles..."
    mkdir -p "$(dirname "$CLONE_DIR")"
    git clone https://github.com/EdwardAstill/claudefiles "$CLONE_DIR"
fi

exec bash "$CLONE_DIR/install.sh" --global "$@"
