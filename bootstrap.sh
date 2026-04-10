#!/usr/bin/env bash
# bootstrap.sh — install the skill-manager skill and CLI tools globally
#
# This is the entry point for new machines. It installs just enough to get
# the skill-manager skill running globally. From there, start a new Claude
# Code session and ask it to install the rest of the suite.
#
# Usage — no local clone needed:
#   curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
#
# Usage — from a local clone:
#   ./bootstrap.sh
#
# What this does:
#   1. Clones (or updates) the claudefiles repo to ~/.claudefiles/
#   2. Installs the skill-manager skill to ~/.claude/skills/
#   3. Installs all bin tools (cf-agents, cf-status, etc.) to ~/.local/bin/
#
# What to do next:
#   Start a new Claude Code session and say:
#   "Install the full claudefiles suite from GitHub."
#   The skill-manager will handle the rest.

set -euo pipefail

# ── Pre-flight checks ─────────────────────────────────────────────────────────

for cmd in git bash curl; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: '$cmd' is required but not installed." >&2
        echo "Install $cmd before running bootstrap.sh." >&2
        exit 1
    fi
done

GITHUB_REPO="EdwardAstill/claudefiles"
CACHE_DIR="$HOME/.claudefiles"
SKILLS_TARGET="$HOME/.claude/skills"
BIN_TARGET="$HOME/.local/bin"

# ── Colour helpers ────────────────────────────────────────────────────────────

bold=""  dim=""  green=""  yellow=""  red=""  reset=""
if [[ -t 1 ]]; then
    bold="\033[1m"
    dim="\033[2m"
    green="\033[0;32m"
    yellow="\033[0;33m"
    red="\033[0;31m"
    reset="\033[0m"
fi

info()    { echo -e "  ${dim}→${reset}  $*"; }
ok()      { echo -e "  ${green}✓${reset}  $*"; }
warn()    { echo -e "  ${yellow}⚠${reset}  $*"; }
header()  { echo -e "\n${bold}$*${reset}"; }

# ── Step 1: Clone or update the repo ─────────────────────────────────────────

header "claudefiles bootstrap"
echo ""
info "Source : github.com/$GITHUB_REPO"
info "Cache  : $CACHE_DIR"
info "Skills : $SKILLS_TARGET"
info "Bin    : $BIN_TARGET"
echo ""

header "1 / 3  Fetching claudefiles"

if [[ -d "$CACHE_DIR/.git" ]]; then
    info "Repo already cached — pulling latest..."
    git -C "$CACHE_DIR" pull --ff-only --quiet
    ok "Up to date"
else
    info "Cloning from GitHub..."
    git clone --quiet "https://github.com/$GITHUB_REPO" "$CACHE_DIR"
    ok "Cloned to $CACHE_DIR"
fi

# ── Step 2: Install skill-manager skill ──────────────────────────────────────

header "2 / 3  Installing skill-manager skill"

# Find skill-manager by searching for SKILL.md with name: skill-manager
SKILL_DIR=""
while IFS= read -r skill_md; do
    found_name="$(awk '/^name:/ { gsub(/^name: */, ""); print; exit }' "$skill_md" 2>/dev/null)"
    if [[ "$found_name" == "skill-manager" ]]; then
        SKILL_DIR="$(dirname "$skill_md")"
        break
    fi
done < <(find "$CACHE_DIR/dev-suite" -name "SKILL.md" 2>/dev/null)

if [[ -z "$SKILL_DIR" ]]; then
    echo -e "  ${red}✗${reset}  skill-manager skill not found in $CACHE_DIR/dev-suite" >&2
    exit 1
fi

mkdir -p "$SKILLS_TARGET"

LINK="$SKILLS_TARGET/skill-manager"
if [[ -L "$LINK" ]]; then
    ok "skill-manager already linked — skipping"
elif [[ -e "$LINK" ]]; then
    warn "$LINK exists but is not a symlink — skipping (remove it manually if you want to re-link)"
else
    ln -s "$SKILL_DIR" "$LINK"
    ok "Linked: $LINK → $SKILL_DIR"
fi

# ── Step 3: Install bin tools ─────────────────────────────────────────────────

header "3 / 3  Installing bin tools"

MANIFEST="$CACHE_DIR/manifest.toml"
BIN_DIR="$CACHE_DIR/bin"

mkdir -p "$BIN_TARGET"

# Parse [bin] install = [...] from manifest.toml
while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue
    src="$BIN_DIR/$entry"
    dst="$BIN_TARGET/$entry"

    if [[ ! -f "$src" ]]; then
        warn "bin/$entry not found in repo — skipping"
        continue
    fi

    chmod +x "$src"

    if [[ -L "$dst" ]]; then
        ok "$entry already linked — skipping"
    elif [[ -e "$dst" ]]; then
        warn "$dst exists but is not a symlink — skipping"
    else
        ln -s "$src" "$dst"
        ok "Linked: $dst"
    fi
done < <(
    awk '/^\[bin\]/{found=1;next} found && /^\[/{found=0} found' "$MANIFEST" \
        | grep '^install' \
        | sed 's/.*=\s*//' \
        | tr -d '[]"' \
        | tr ',' '\n' \
        | tr -d ' \t' \
        | grep -v '^$'
)

# ── Check PATH ────────────────────────────────────────────────────────────────

echo ""
if [[ ":$PATH:" != *":$BIN_TARGET:"* ]]; then
    warn "$BIN_TARGET is not in your PATH"
    echo ""
    echo "    Add one of these to your shell config:"
    echo "      fish:  fish_add_path ~/.local/bin"
    echo "      bash:  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    echo "      zsh:   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
    echo ""
fi

# ── Done ──────────────────────────────────────────────────────────────────────

header "Done"
echo ""
echo "  skill-manager is installed globally."
echo ""
echo "  Next steps:"
echo "    1. Start a new Claude Code session in your project"
echo "    2. Say: \"Set up this project\" — the skill-manager will ask you to"
echo "       describe your project and install the right skills for it."
echo ""
