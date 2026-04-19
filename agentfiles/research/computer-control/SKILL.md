---
name: computer-control
description: >
  Use when driving the user's Linux/Hyprland desktop directly — not a browser,
  not a terminal scrollback. Trigger phrases: "take a screenshot", "screenshot
  the active window", "grab a region of the screen", "click on the screen",
  "move the cursor to X", "type into the focused window", "switch workspaces",
  "focus Firefox", "close this window", "what windows are open", "read the
  active window title", "copy X to my clipboard", "paste the clipboard",
  "enumerate the windows on workspace 2", "send alt+tab". Uses hyprctl + grim +
  slurp + dotool + wl-clipboard via Bash. Hyprland-only (Wayland). Do NOT use
  for web automation (use browser-control). Do NOT use for reading terminal
  scrollback output (use terminal-read).
---

# computer-control

Drive the user's Hyprland desktop directly: query/manipulate windows, take
screenshots, read/write the clipboard, and — as a last resort — synthesize
keyboard and mouse input.

This is pure Wayland. `xdotool` and friends do not work here. Everything
goes through Hyprland IPC, Wayland screencopy, or `dotool` (uinput).

---

## When to use

| User says | Tool |
|-----------|------|
| "What windows are open?" | `hyprctl -j clients` |
| "Focus Firefox" | `hyprctl dispatch focuswindow` |
| "Switch to workspace 3" | `hyprctl dispatch workspace 3` |
| "Close this window" | `hyprctl dispatch killactive` |
| "Take a screenshot" | `grim` |
| "Let me pick a region" | `grim -g "$(slurp)"` |
| "Copy X to clipboard" | `wl-copy` |
| "What's on my clipboard?" | `wl-paste` |
| "Type 'hello' into the focused window" | `dotool` |
| "Click at the centre of the screen" | `dotool` |
| "Press Alt+Tab" | `dotool` (or better: `hyprctl dispatch cyclenext`) |

**Not for:** browser automation (use `browser-control`), reading the
user's shell scrollback (use `terminal-read`), running headless commands
(use the Bash tool directly).

---

## Tool precedence

Prefer querying and dispatching over synthetic input. In order of
preference:

1. **`hyprctl`** — structured IPC. Lossless, scriptable, does not depend on
   which window has focus. First choice for any window-management or
   workspace action.
2. **`grim` / `slurp`** — Wayland-native screenshot. No focus change, no
   side effects beyond writing an image.
3. **`wl-copy` / `wl-paste`** — clipboard. Also side-effect-free beyond
   the clipboard itself.
4. **`dotool`** — synthetic keyboard/mouse via `/dev/uinput`. Changes
   desktop state in ways Hyprland sees as real user input. Use only when
   no IPC path exists (e.g. typing into an arbitrary focused app, or
   clicking a pixel in a screenshot).

Rule of thumb: if you can express the action as a hyprctl dispatch, do
that instead of synthesizing a keychord.

---

## Daemon requirement (one-time)

`dotool` reads commands from stdin and writes to `/dev/uinput` via the
`dotoold` user service. Without the daemon running, `dotool` will appear
to hang or silently do nothing.

One-time setup for the user:

```bash
systemctl --user enable --now dotoold
systemctl --user is-active dotoold   # → active
```

The user is already in the `input` group, so no root is needed once the
daemon is up. If `is-active` returns `inactive`, run the `enable --now`
command above before using any `dotool` recipe below.

`grim`, `slurp`, `wl-copy`, and `hyprctl` do not depend on this daemon.

---

## Recipes

### Screenshot — full screen / active window / region

```bash
# Full screen (all outputs)
grim /tmp/shot.png

# Just the active monitor
grim -o "$(hyprctl -j activeworkspace | jq -r '.monitor')" /tmp/shot.png

# Just the active window (use its geometry from hyprctl)
geom=$(hyprctl -j activewindow | jq -r '"\(.at[0]),\(.at[1]) \(.size[0])x\(.size[1])"')
grim -g "$geom" /tmp/win.png

# Interactive region pick (user drags a rectangle)
grim -g "$(slurp)" /tmp/region.png
```

Then `Read /tmp/shot.png` to view the image.

### Enumerate windows

```bash
# All clients as JSON
hyprctl -j clients | jq '.[] | {class, title, workspace: .workspace.id, address}'

# Just titles on the current workspace
ws=$(hyprctl -j activeworkspace | jq -r '.id')
hyprctl -j clients | jq -r --argjson ws "$ws" '.[] | select(.workspace.id == $ws) | .title'

# Active window title
hyprctl -j activewindow | jq -r '.title'
```

### Focus a window by title or class

```bash
# By fuzzy title match — hyprctl accepts title:regex
hyprctl dispatch focuswindow 'title:Firefox'

# By class
hyprctl dispatch focuswindow 'class:firefox'

# Or resolve address first for precision
addr=$(hyprctl -j clients | jq -r '.[] | select(.class == "firefox") | .address' | head -1)
hyprctl dispatch focuswindow "address:$addr"
```

### Workspace switching / moving windows

```bash
hyprctl dispatch workspace 3                    # go to workspace 3
hyprctl dispatch movetoworkspace 2              # move active window to ws 2
hyprctl dispatch movetoworkspacesilent 2        # ...without following it
hyprctl dispatch cyclenext                      # alt-tab-style
```

### Close / kill the active window

```bash
hyprctl dispatch killactive
```

### Clipboard read / write

```bash
echo "hello world" | wl-copy                  # write
wl-copy < /tmp/file.txt                        # write file contents
wl-paste                                       # read (text)
wl-paste --list-types                          # see MIME types
wl-paste -t image/png > /tmp/clip.png          # read an image from clipboard
```

### Type into the focused window

```bash
# Plain text
printf 'type Hello, world!\n' | dotool

# With a small delay so fast apps keep up
printf 'typedelay 20\ntype Hello\n' | dotool

# Key chord — uses Linux key names (see `dotool --list-keys`)
printf 'key ctrl+c\n' | dotool
printf 'key alt+tab\n' | dotool
printf 'key super+1\n' | dotool                # prefer `hyprctl dispatch workspace 1`
```

### Click / move the cursor

```bash
# Move cursor to centre of screen (percentages 0.0–1.0) and left-click
printf 'mouseto 0.5 0.5\nclick left\n' | dotool

# Right-click at a point
printf 'mouseto 0.8 0.1\nclick right\n' | dotool

# Drag: press, move, release
printf 'mouseto 0.2 0.2\nbuttondown left\nmouseto 0.6 0.6\nbuttonup left\n' | dotool

# Scroll
printf 'wheel -5\n' | dotool                    # scroll down 5
```

`mouseto` uses percentages across the full logical layout (all outputs),
not pixels. For pixel-exact clicks in a specific monitor, compute the
percentage from `hyprctl -j monitors` geometry.

### Monitors / outputs

```bash
hyprctl -j monitors | jq '.[] | {name, width, height, x, y, scale, focused}'
```

---

## Safety

`dotool` drives the user's real keyboard and mouse. Assume the same
caution you would apply to running a destructive shell command:

- **Confirm before typing** into a window you did not just focus yourself.
  Focus can change between commands; what was active 200 ms ago may not
  be now. Re-check with `hyprctl -j activewindow` if unsure.
- **Never `type` passwords or secrets** — they will be synthesized as
  visible keystrokes and may be captured by logging or another focused
  app.
- **Prefer `hyprctl dispatch`** over key chords for window/workspace
  actions. It's atomic and does not depend on focus.
- **Large click sequences / bulk typing:** pause to confirm the plan with
  the user first. A runaway `dotool` stream is hard to interrupt.
- **Screenshots of sensitive apps:** `grim` captures whatever is on
  screen, including password managers, private messages, etc. Save to
  `/tmp/` and clean up after.

---

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `dotool` hangs or does nothing | `dotoold` not running | `systemctl --user enable --now dotoold` |
| `dotool: Permission denied /dev/uinput` | User not in `input` group | `sudo usermod -aG input $USER` + relogin |
| `grim` writes black image | Compositor denied screencopy (rare on Hyprland) | Check `hyprctl monitors` shows the expected output |
| `focuswindow` silently does nothing | Regex didn't match any client | List with `hyprctl -j clients` and refine the selector |
| `wl-paste` returns empty | Nothing text-typed on clipboard; try `--list-types` | Use `-t image/png` or the relevant MIME |
| Key chord does nothing | App didn't have focus at the moment `dotool` fired | Focus first via `hyprctl dispatch focuswindow`, then pipe to dotool |

---

## Do not

- Do not reach for `xdotool`, `ydotool`, or `wtype` — not installed, not
  the right tool for this setup. `dotool` covers the same ground.
- Do not loop `dotool` clicks without a plan and a stop condition. If
  something goes wrong the user has to physically interrupt it.
- Do not use this skill to drive a browser — `browser-control` talks to
  Firefox/Zen through Marionette and is lossless and stateful.
- Do not use this skill to read terminal output the user is referring to
  — `terminal-read` grabs tmux/screen scrollback directly.
