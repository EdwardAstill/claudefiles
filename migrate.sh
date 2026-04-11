#!/usr/bin/env bash
# migrate.sh — one-time repo migration from old structure to new
# Run from repo root. Stages all changes but does not commit.
set -euo pipefail

echo "Step 1: Rename claudefiles/ → skills/"
git mv claudefiles/ skills/

echo "Step 2: Move bin/ → tools/scripts/"
mkdir -p tools
git mv bin/ tools/scripts/

echo "Step 3: Update skill file references: cf-X → cf X"
find skills/ -name "SKILL.md" -exec sed -i \
  -e 's/`cf-check`/`cf check`/g' \
  -e 's/`cf-agents`/`cf agents`/g' \
  -e 's/`cf-context`/`cf context`/g' \
  -e 's/`cf-status`/`cf status`/g' \
  -e 's/`cf-versions`/`cf versions`/g' \
  -e 's/`cf-routes`/`cf routes`/g' \
  -e 's/`cf-note`/`cf note`/g' \
  -e 's/`cf-read`/`cf read`/g' \
  -e 's/`cf-init`/`cf init`/g' \
  -e 's/`cf-worktree`/`cf worktree`/g' \
  -e 's/`cf-setup`/`cf setup`/g' \
  -e 's/`cf-brief`/`cf brief`/g' \
  {} +

echo "Step 4: Check for lib/ references in skills/ (manual review needed)"
grep -r "lib/common.sh\|lib/port-finder.sh" skills/ || echo "  (none found)"

echo "Step 5: Update CLAUDE.md path references"
sed -i \
  -e 's|claudefiles/|skills/|g' \
  -e 's|bin/|tools/scripts/|g' \
  CLAUDE.md

echo "Step 6: Remove [cli.*] and [bin] from manifest.toml"
python3 - <<'PYEOF'
import re
with open("manifest.toml") as f:
    content = f.read()
content = re.sub(r'\[bin\].*?(?=\n\[|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'\[cli\.[^\]]+\].*?(?=\n\[|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'# ── CLI tool registry.*?(?=\n\[|\Z)', '', content, flags=re.DOTALL)
with open("manifest.toml", "w") as f:
    f.write(content.strip() + "\n")
PYEOF

echo ""
echo "Migration complete. Review changes with: git diff --cached"
echo "Commit with: git commit -m 'chore: migrate repo structure (claudefiles→skills, bin→tools/scripts)'"
