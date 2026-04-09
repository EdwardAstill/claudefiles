#!/usr/bin/env bash
# port-finder.sh — find the next available port starting from a base port
#
# Usage:
#   port-finder.sh [base-port]
#
# Defaults to starting from 3001. Returns the first free port.

set -euo pipefail

BASE="${1:-3001}"
PORT="$BASE"

while true; do
    if ! ss -tuln 2>/dev/null | grep -q ":$PORT " && \
       ! lsof -i ":$PORT" &>/dev/null 2>&1; then
        echo "$PORT"
        exit 0
    fi
    PORT=$((PORT + 1))
    if [[ "$PORT" -gt 9999 ]]; then
        echo "Error: no free port found between $BASE and 9999" >&2
        exit 1
    fi
done
