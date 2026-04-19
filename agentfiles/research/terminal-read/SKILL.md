---
name: terminal-read
description: >
  Use when the user references output that happened in their shell outside
  the conversation and hasn't pasted it in. Trigger phrases: "look at what
  setup.fish just printed", "see the error I got", "check the output of that
  command", "what did the test say", "I just ran X, now fix it", "read my
  terminal", "grab my scrollback", "look at the last thing that happened in
  my shell", "the install failed, look at the log in my terminal", "I ran the
  build — what went wrong". Runs the external `termread` CLI to dump tmux /
  screen / piped-stdin scrollback to a file which the agent then Reads. Do
  NOT use to execute commands (use the Bash tool directly) or to read a log
  file the user already has on disk (use Read).
---

# terminal-read

The agent cannot see the user's actual terminal. When they say "look at what
just happened", use the `termread` CLI to dump the current shell's
scrollback into a file, then Read that file.

Source lives in its own repo:
[EdwardAstill/termread](https://github.com/EdwardAstill/termread).
Install once with:

```bash
uv pip install -e ~/projects/termread      # from local checkout
# once published:
# pipx install termread
```

If `termread` is not on `$PATH`, ask the user to install it (one of the two
commands above) before proceeding.

## CLI

```
termread [--lines N] [--out FILE] [--stdin]
```

| Flag | Purpose |
|------|--------|
| `--lines N` | How many recent lines to grab (0 = full buffer, default 500) |
| `--out FILE` | Write to file (preferred — survives Claude Code tool-output truncation) |
| `--stdin` | Read from stdin instead of capturing; use when piping a live command |

Detection order: `$TMUX` → tmux pane; `$STY` → screen hardcopy; else error
with three fallback instructions for the user.

---

## When to use

| User says | Action |
|-----------|--------|
| "Look at what setup.fish printed" | `termread --out /tmp/term.log` → Read it |
| "Check that last error" | Same |
| "What did the test output say?" | Same |
| "I ran X, now…" + no paste | Same |
| User pastes the output in-chat | Do NOT run this; just use the paste |

---

## Workflow

```
1. termread --out /tmp/term.log       # or --lines 200 for a smaller grab
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

If `termread` fails with the env-var error, ask the user to pick one:

| Situation | Fix |
|-----------|-----|
| Wants scrollback for an already-finished command | Re-run the command piped into a file: `<cmd> 2>&1 | tee /tmp/out.log` then Read that |
| Wants live capture of a command they are about to run | `<cmd> 2>&1 | termread --stdin --out /tmp/out.log` |
| Wants a full session recorded | `script -q /tmp/session.log` → run stuff → `exit` → Read the log |
| Working regularly with agents | Suggest they start tmux: `tmux new -s work` — future captures become trivial |

---

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `could not capture scrollback` | Not in tmux / screen, no `--stdin` | Pick a fallback (see table above) |
| `termread: command not found` | CLI not installed | Install from `~/projects/termread` (see top of skill) |
| Output has ANSI escape codes / garbled colour | Terminal colour output preserved verbatim | Usually fine for the agent; if not, `sed 's/\x1b\[[0-9;]*m//g'` to strip |
| Missing the first lines of a long run | tmux history buffer exceeded | Re-run with `script` for a full session log |
| `--lines 0` returns tons of unrelated history | Capture too wide | Tighten with `--lines 200` |

---

## Do not

- Do not run `termread` when the user has already pasted the output into chat — you already have the text.
- Do not pipe the captured log through additional tools without first Reading it — ANSI and line wrapping can mislead grep.
- Do not leave `/tmp/term.log` around across sessions — overwrite or delete when done.
- Do not use this as a substitute for running commands yourself; if *you* need to run something, use the Bash tool directly — its output is already visible to you.
