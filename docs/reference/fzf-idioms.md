# fzf idioms for `af`

`fzf` turns flat listings into interactive pickers with zero plumbing. Most
`af` subcommands emit newline-delimited rows — pipe them through `fzf` and
chain the pick into the next command.

## Install

```bash
# arch
sudo pacman -S fzf
# mac
brew install fzf
# once installed, your shell gets <ctrl-t> / <ctrl-r> history integration for free
```

## Knowledge pages

```bash
# Pick a knowledge page, show it:
af ak list | awk '{print $1}' | fzf | xargs af ak show

# Or pick by heading, which is usually more memorable:
af ak list | fzf --with-nth=2.. --delimiter='\s{2,}' | awk '{print $1}' | xargs af ak show
```

## Archetypes

```bash
# Pick an archetype to start from:
af archetype list | fzf | awk '{print $1}' | xargs af archetype show
```

## Skill usage — pick a busy skill and inspect sessions

```bash
af skill-usage rank | fzf | awk '{print $2}' | xargs af skill-usage sessions
```

## Session logs

```bash
# Pick a recent session to analyze:
ls -t ~/.claude/logs/sessions/ | fzf | xargs -I{} af log session {}
```

## Git branches (general-purpose)

```bash
# Switch to a branch interactively:
git branch --all | fzf | sed 's|remotes/origin/||' | xargs git switch
```

## Useful flags

- `--preview '<cmd> {}'` — show a preview pane driven by the selected row.
  E.g., `af ak list | fzf --preview 'af ak show {1}'` gives live-preview page
  contents while you pick.
- `--height 40% --reverse` — non-fullscreen overlay; common default.
- `--multi` — select multiple rows with tab; `xargs` iterates.

## When fzf is NOT the right tool

- **Non-interactive scripts / hooks** — use `grep`/`awk` directly; fzf wants
  a TTY.
- **Very long lists (>10k rows)** — fzf is fast but you usually want
  pre-filtering (`grep`, `fzf --query`).
- **Structured selection over fields** — if you need typed parsing, `jq` or
  `miller` before `fzf` keeps the pipeline honest.
