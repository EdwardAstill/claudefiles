---
name: terminal-read
description: >
  Use when the user references something that just happened in their terminal
  outside the conversation — "look at what setup.fish just printed", "see the
  error I got", "check the output of that command". Captures the live shell
  scrollback (tmux / screen / piped stdin) so the agent can Read it.
---

# terminal-read

The agent cannot see the user's actual terminal. When they say "look at what
just happened", use `af terminal` to dump the current shell's scrollback into
a file, then Read that file.

## Subcommand

```
af terminal [--lines N] [--out FILE] [--stdin]
```

| Flag | Purpose |
|------|--------|
| `--lines N` | How many recent lines to grab (0 = full buffer, default 500) |
| `--out FILE` | Write to file (preferred — survives Claude Code tool-output truncation) |
| `--stdin` | Read from stdin instead of capturing; use when piping a live command |

Detection order: `$TMUX` → tmux pane; `$STY` → screen hardcopy; else error with
three fallback instructions for the user.

---

## When to use

| User says | Action |
|-----------|--------|
| "Look at what setup.fish printed" | `af terminal --out /tmp/term.log` → Read it |
| "Check that last error" | Same |
| "What did the test output say?" | Same |
| "I ran X, now…" + no paste | Same |
| User pastes the output in-chat | Do NOT run this; just use the paste |

---

## Workflow

```
1. af terminal --out /tmp/term.log   # or --lines 200 for a smaller grab
2. Read /tmp/term.log
3. Answer from the capture
4. (optional) rm /tmp/term.log
```

**Large output:** prefer `--out` over stdout — writing to a file sidesteps
Claude Code's tool-output limits, and `Read` lets you scroll / offset.

**Scoping the grab:** pass `--lines 100` for recent tail, `--lines 0` for the
full pane buffer. Tmux default history is 2000 lines; beyond that it's gone.

---

## Fallbacks — user is not in tmux / screen

If `af terminal` fails with the env-var error, ask the user to pick one:

| Situation | Fix |
|-----------|-----|
| Wants scrollback for an already-finished command | Re-run the command piped into a file: `<cmd> 2>&1 | tee /tmp/out.log` then Read that |
| Wants live capture of a command they are about to run | `<cmd> 2>&1 | af terminal --stdin --out /tmp/out.log` |
| Wants a full session recorded | `script -q /tmp/session.log` → run stuff → `exit` → Read the log |
| Working regularly with agents | Suggest they start tmux: `tmux new -s work` — future captures become trivial |

---

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `could not capture scrollback` | Not in tmux / screen, no `--stdin` | Pick a fallback (see table above) |
| Output has ANSI escape codes / garbled colour | Terminal colour output preserved verbatim | Usually fine for the agent; if not, `sed 's/\x1b\[[0-9;]*m//g'` to strip |
| Missing the first lines of a long run | tmux history buffer exceeded | Re-run with `script` for a full session log |
| `--lines 0` returns tons of unrelated history | Capture too wide | Tighten with `--lines 200` |

---

## Do not

- Do not run `af terminal` when the user has already pasted the output into chat — you already have the text.
- Do not pipe the captured log through additional tools without first Reading it — ANSI and line wrapping can mislead grep.
- Do not leave `/tmp/term.log` around across sessions — overwrite or delete when done.
- Do not use this as a substitute for running commands yourself; if *you* need to run something, use the Bash tool directly — its output is already visible to you.
