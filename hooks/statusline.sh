#!/usr/bin/env bash
# agentfiles statusline — shows cwd, git state, model, context %, 5h rate limit,
# and active caveman level. Installed into ~/.claude/settings.json by install-hooks.sh.

input=$(cat)

# Parse JSON using jq if available, else fall back to python3
if command -v jq >/dev/null 2>&1; then
  model=$(printf '%s' "$input" | jq -r '.model.display_name // .model.id // "Unknown"')
  cwd=$(printf '%s' "$input" | jq -r '.cwd // .workspace.current_dir // ""')
  used=$(printf '%s' "$input" | jq -r 'if .context_window.used_percentage != null then .context_window.used_percentage else "" end')
  session_pct=$(printf '%s' "$input" | jq -r '.rate_limits.five_hour.used_percentage // ""')
elif command -v python3 >/dev/null 2>&1; then
  model=$(printf '%s' "$input" | python3 -c "
import sys, json
d = json.load(sys.stdin)
m = d.get('model', {})
print(m.get('display_name') or m.get('id') or 'Unknown')
")
  cwd=$(printf '%s' "$input" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('cwd') or d.get('workspace', {}).get('current_dir') or '')
")
  used=$(printf '%s' "$input" | python3 -c "
import sys, json
d = json.load(sys.stdin)
v = d.get('context_window', {}).get('used_percentage')
print('' if v is None else v)
")
  session_pct=$(printf '%s' "$input" | python3 -c "
import sys, json
d = json.load(sys.stdin)
v = d.get('rate_limits', {}).get('five_hour', {}).get('used_percentage')
print('' if v is None else v)
")
else
  model="Unknown"
  cwd=""
  used=""
  session_pct=""
fi

# Shorten cwd: replace $HOME with ~
home="$HOME"
if [ -n "$cwd" ] && [ "${cwd#$home}" != "$cwd" ]; then
  short_cwd="~${cwd#$home}"
else
  short_cwd="$cwd"
fi
[ -z "$short_cwd" ] && short_cwd="~"

# Git info: branch and clean/dirty status
git_display=""
if git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git_branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null || git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
  if git -C "$cwd" status --no-optional-locks --porcelain 2>/dev/null | grep -q .; then
    git_indicator="*"
  else
    git_indicator="✓"
  fi
  git_display="${git_branch} ${git_indicator}"
fi

# Caveman mode indicator — read state file if hook is enabled
caveman_display=""
CAVEMAN_STATE="$HOME/.claude/caveman-mode"
if [ -f "$CAVEMAN_STATE" ]; then
  caveman_level=$(tr -d '[:space:]' < "$CAVEMAN_STATE")
  [ -z "$caveman_level" ] && caveman_level="full"
  case "$caveman_level" in
    lite)           caveman_tag="cv:lite" ;;
    full)           caveman_tag="cv:full" ;;
    actual-caveman) caveman_tag="cv:actual" ;;
    *)              caveman_tag="cv:$caveman_level" ;;
  esac
  caveman_display="$caveman_tag"
fi

# Build context progress bar (20 chars wide)
FILLED_CHAR=$(printf '\xe2\x96\x88')
EMPTY_CHAR=$(printf '\xe2\x96\x91')

bar=""
if [ -n "$used" ] && [ "$used" != "null" ]; then
  used_int=$(printf "%.0f" "$used")
  filled=$(( used_int * 20 / 100 ))
  empty=$(( 20 - filled ))
  i=0
  while [ $i -lt $filled ]; do bar="${bar}${FILLED_CHAR}"; i=$(( i + 1 )); done
  i=0
  while [ $i -lt $empty ]; do bar="${bar}${EMPTY_CHAR}"; i=$(( i + 1 )); done
  ctx_display="Context: [${bar}] ${used_int}%"
else
  ctx_display="Context: [$(printf '%0.s'"$EMPTY_CHAR" {1..20})] --%"
fi

# 5-hour rate limit
if [ -n "$session_pct" ] && [ "$session_pct" != "null" ]; then
  session_int=$(printf "%.0f" "$session_pct")
  usage_display="Usage: ${session_int}% of session limit"
else
  usage_display="Usage: --% of session limit"
fi

# ANSI colors
COL_CWD='\033[0;36m'       # cyan
COL_GIT='\033[0;34m'       # blue
COL_MODEL='\033[0;33m'     # yellow
COL_CTX='\033[0;32m'       # green
COL_USAGE='\033[0;35m'     # magenta
COL_CAVEMAN='\033[0;31m'   # red — flag that a persistent mode is active
RESET='\033[0m'

# Compose
parts="${COL_CWD}${short_cwd}${RESET}"
[ -n "$git_display" ] && parts="${parts}  ${COL_GIT}(${git_display})${RESET}"
parts="${parts}  ${COL_MODEL}${model}${RESET}"
[ -n "$caveman_display" ] && parts="${parts}  ${COL_CAVEMAN}[${caveman_display}]${RESET}"
parts="${parts}  ${COL_CTX}${ctx_display}${RESET}  ${COL_USAGE}${usage_display}${RESET}"

printf "%b\n" "$parts"
