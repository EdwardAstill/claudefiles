#!/usr/bin/env bash
# install-log-review-timer.sh — install the weekly `af log review` systemd
# user timer.
#
# Copies hooks/systemd/af-log-review.{service,timer} to
# ~/.config/systemd/user/, rewrites ExecStart= to the real `af` path on this
# host, reloads the user systemd manager, and enables + starts the timer.
#
# Idempotent: safe to re-run. Will overwrite the installed unit files and
# re-enable the timer.
#
# Usage:
#   ./hooks/install-log-review-timer.sh [--dry-run] [--uninstall]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_DIR="$REPO_ROOT/hooks/systemd"
DEST_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="af-log-review.service"
TIMER_NAME="af-log-review.timer"
DRY_RUN=false
UNINSTALL=false

for arg in "$@"; do
    case "$arg" in
        --dry-run)   DRY_RUN=true ;;
        --uninstall) UNINSTALL=true ;;
        -h|--help)
            sed -n '2,15p' "$0"
            exit 0
            ;;
        *)
            echo "unknown arg: $arg" >&2
            exit 2
            ;;
    esac
done

run() {
    if "$DRY_RUN"; then
        echo "  [dry-run] $*"
    else
        echo "  [run] $*"
        "$@"
    fi
}

if "$UNINSTALL"; then
    echo "  Uninstalling $TIMER_NAME ..."
    if systemctl --user list-unit-files "$TIMER_NAME" &>/dev/null; then
        run systemctl --user disable --now "$TIMER_NAME" || true
    fi
    run rm -f "$DEST_DIR/$TIMER_NAME" "$DEST_DIR/$SERVICE_NAME"
    run systemctl --user daemon-reload
    echo "  Done."
    exit 0
fi

# Resolve `af` path on this host so the unit's ExecStart= is correct even if
# the user installed `af` somewhere other than ~/.local/bin/.
AF_PATH="$(command -v af || true)"
if [[ -z "$AF_PATH" ]]; then
    echo "ERROR: 'af' not found on PATH. Run 'uv tool install --editable tools/python' first." >&2
    exit 1
fi
echo "  af resolved to: $AF_PATH"

# Verify source units exist.
for f in "$SERVICE_NAME" "$TIMER_NAME"; do
    if [[ ! -f "$SRC_DIR/$f" ]]; then
        echo "ERROR: missing $SRC_DIR/$f" >&2
        exit 1
    fi
done

# Make destination dir.
run mkdir -p "$DEST_DIR"

# Copy the timer verbatim — no per-host substitutions needed.
if "$DRY_RUN"; then
    echo "  [dry-run] cp $SRC_DIR/$TIMER_NAME $DEST_DIR/$TIMER_NAME"
else
    cp "$SRC_DIR/$TIMER_NAME" "$DEST_DIR/$TIMER_NAME"
    echo "  [installed] $DEST_DIR/$TIMER_NAME"
fi

# Copy the service, rewriting the ExecStart line to use the resolved `af`
# path. We use a literal sed pattern rather than a regex to avoid mangling.
if "$DRY_RUN"; then
    echo "  [dry-run] cp + rewrite ExecStart= → $AF_PATH log review"
else
    sed "s|^ExecStart=.*|ExecStart=$AF_PATH log review|" \
        "$SRC_DIR/$SERVICE_NAME" > "$DEST_DIR/$SERVICE_NAME"
    echo "  [installed] $DEST_DIR/$SERVICE_NAME (ExecStart rewritten)"
fi

# Reload, enable, start.
run systemctl --user daemon-reload
run systemctl --user enable --now "$TIMER_NAME"

echo
echo "  Next scheduled run:"
if ! "$DRY_RUN"; then
    systemctl --user list-timers "$TIMER_NAME" --no-pager || true
fi

echo
echo "  Inspect logs with:"
echo "    journalctl --user -u $SERVICE_NAME"
echo "  Trigger a manual run with:"
echo "    systemctl --user start $SERVICE_NAME"
echo "  Uninstall with:"
echo "    $0 --uninstall"
