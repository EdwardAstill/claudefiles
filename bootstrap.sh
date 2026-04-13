#!/usr/bin/env bash
# bootstrap.sh — install agentfiles from GitHub on a new machine
#
# Usage (one-liner):
#   curl -fsSL https://raw.githubusercontent.com/EdwardAstill/agentfiles/main/bootstrap.sh | bash
#
# Or clone and run locally:
#   bash bootstrap.sh

set -euo pipefail

CLONE_DIR="$HOME/.local/share/agentfiles-src"

if [[ -d "$CLONE_DIR/.git" ]]; then
    echo "Updating agentfiles..."
    git -C "$CLONE_DIR" pull --ff-only
else
    echo "Cloning agentfiles..."
    mkdir -p "$(dirname "$CLONE_DIR")"
    git clone https://github.com/EdwardAstill/agentfiles "$CLONE_DIR"
fi

exec bash "$CLONE_DIR/install.sh" --global "$@"
