---
name: tui-expert
description: >
  Use for designing, specifying, or reviewing a terminal user interface
  (TUI) — what it looks like and how it behaves, before code is written.
  Trigger phrases: "design a TUI for this", "which TUI framework should
  I use", "Ratatui vs Textual vs Ink vs Bubbletea", "lay out this
  dashboard in the terminal", "keyboard shortcuts for this TUI", "what
  widget do I use for X", "terminal color palette for this", "pick a
  TUI component for a form", "spec out the TUI screens", "review this
  TUI UX". Knows the widget catalogs of Textual, Ratatui, Ink, and
  Bubbletea so specs reference real component names, then hands off to
  python-expert / rust-expert / typescript-expert for implementation
  (or storm-tui if the project uses @orchetron/storm). Do NOT use for
  writing the actual implementation code (use the language expert) or
  for web/React UI design (use ui-expert).
---

# TUI Expert

Design intelligence for terminal user interfaces. Specifies what the TUI should
look like and how it should behave, then hands off to the appropriate language
expert for implementation. Knows the major frameworks so specs name real widgets.

## Framework Selection

| Framework | Language | Layout model | State model | Notable apps |
|-----------|----------|-------------|-------------|-------------|
| **Ratatui** | Rust | Constraint-based (Length, Min, Max, %) | Immediate-mode, app struct owns state | yazi, gitui, lazygit, bottom |
| **Ink** | TypeScript | Flexbox (yoga-layout) | React hooks (useState, useEffect) | Claude Code, Pastel |
| **Textual** | Python | CSS-like (grid, horizontal, vertical) | Message/event system, reactive attrs | Harlequin, Trogon, Posting |
| **Bubbletea** | Go | Manual string building + lipgloss | Elm MVU (Model/Update/View) | charm tools, soft-serve, glow |

**Default choice:** Match the project's language. If greenfield, Ratatui for
performance-critical apps, Textual for rapid prototyping, Ink if the team
knows React, Bubbletea for Go shops.

---

## Design Intelligence

### Terminal Color — Three Tiers

```
ANSI 16    →  Universal. User-themeable. Design with these as the base.
               black red green yellow blue magenta cyan white
               + bright variants of each (bright black = gray)

256-color  →  Consistent but limited. 16-231 color cube, 232-255 grayscale.
               Use for subtle highlights where ANSI 16 is too coarse.

Truecolor  →  RGB. Not supported everywhere (linux console, old tmux, some SSH).
               Use only for decoration (gradients, accents). Never rely on it.
```

**Graceful degradation rule:** Design the base UI with ANSI 16 (respects user
themes). Layer 256/truecolor for polish. Check `$COLORTERM` for capability.
Ratatui's `Color::Red` = ANSI, `Color::Rgb()` = truecolor. Lipgloss degrades
automatically. Textual handles it internally.

**Color in specs:** Use semantic names that map to ANSI roles:
- `fg` / `bg` — primary text and background (terminal default)
- `accent` — the one bright color for highlights (specify which ANSI color)
- `dim` — secondary text (DIM modifier or bright-black/gray)
- `error` — red, `success` — green, `warning` — yellow
- `selected` — reverse video (swap fg/bg) — the universal TUI highlight
- `border-focused` — bright variant of accent, `border-unfocused` — dim/gray

### Layout — Character Grid Patterns

Everything is rows x columns. One character cell = one "pixel". CJK/emoji
take 2 columns — always use unicode-width measurement, never string length.

**Common layouts:**

```
Miller columns (yazi/ranger)     List + Detail (email-style)
┌──────┬───────────┬──────────┐  ┌────────────┬─────────────────┐
│parent│ current   │ preview  │  │ items      │ detail          │
│ 20%  │   40%     │   40%    │  │   30%      │     70%         │
└──────┴───────────┴──────────┘  └────────────┴─────────────────┘

Dashboard                        Full-screen editor
┌─────────────────────────────┐  ┌─────────────────────────────┐
│ header / status bar         │  │ status bar                  │
├────────┬────────────────────┤  ├─────────────────────────────┤
│sidebar │ main content       │  │                             │
│        │                    │  │ content area                │
├────────┴────────────────────┤  │                             │
│ footer / keybinding help    │  ├─────────────────────────────┤
└─────────────────────────────┘  │ command line / footer       │
                                 └─────────────────────────────┘
```

**Box-drawing characters:**
- Single: `┌─┐│└─┘├┤┬┴┼`
- Double: `╔═╗║╚═╝╠╣╦╩╬`
- Rounded: `╭─╮╰─╯`
- Heavy: `┏━┓┃┗━┛`
- Most frameworks abstract these (Ratatui `BorderType::Rounded`, Textual
  `border: round`, Ink `borderStyle="round"`)

**Layout must handle odd terminal sizes.** Always handle resize events.
Fill empty space with spaces to prevent artifacts from prior frames.

### Keyboard Interaction Design

**Universal conventions:**

| Key | Action | Notes |
|-----|--------|-------|
| `q` / `Ctrl+C` | Quit | `Ctrl+C` always works |
| `j/k` or `↑/↓` | Vertical nav | Arrows must always work — vim keys are supplementary |
| `h/l` or `←/→` | Horizontal/hierarchy nav | |
| `Tab` / `Shift+Tab` | Cycle focus between panels | |
| `Enter` | Confirm / select | |
| `Escape` | Cancel / back / exit input mode | |
| `/` or `Ctrl+F` | Search / filter | |
| `?` | Help overlay | |
| `g` / `G` | Jump to top / bottom | |
| `Ctrl+D` / `Ctrl+U` | Half-page scroll | |
| `:` | Command mode (vim-style apps) | |

**Design rules:**
1. Arrow keys always work — vim keys supplement, never replace
2. Show available keys in a footer bar or help overlay
3. Single-key shortcuts only in normal mode. When a text input has focus, all
   keys go to input — `Escape` exits input mode
4. `Ctrl+` combos for destructive actions — never bare single keys for delete
5. Discoverable: if users must learn keybindings before using the app, the
   design has failed

### State Matrix — Every TUI Widget

| State | Rendering | Notes |
|-------|-----------|-------|
| Default/unfocused | Normal text, dim or no border | |
| Focused | Bright/colored border, or reverse on active row | TUI "focus ring" |
| Selected | Reverse video (swap fg/bg) | Universal TUI highlight |
| Disabled | DIM modifier, gray text, removed from focus cycle | Not just "no handler" |
| Loading | Spinner in place of content, or placeholder text | |
| Error | Red border + red status text (not just color — add border/icon) | Color-blind safe |
| Empty | Placeholder text ("No items" / "Press N to create") | Never blank |
| Read-only | Visible but no cursor/selection affordance | |

**Focus management:** Terminals have no native focus system. Textual has a built-in
focus chain. Ink uses `useFocus`/`useFocusManager`. Ratatui and Bubbletea have no
built-in focus — manage it as an enum or index in your state struct, render
borders/styles conditionally.

---

## Framework Reference

### Textual (Python)

**Widget catalog:** Button, Checkbox, Collapsible, ContentSwitcher, DataTable,
Digits, DirectoryTree, Footer, Header, Input, Label, Link, ListView,
LoadingIndicator, Log, Markdown, MarkdownViewer, MaskedInput, OptionList,
Placeholder, Pretty, ProgressBar, RadioButton, RadioSet, RichLog, Rule, Select,
SelectionList, Sparkline, Static, Switch, Tabs, TabbedContent, TextArea, Tree.

**Styling:** TCSS files (`.tcss`) or inline `DEFAULT_CSS`. Supports `:hover`,
`:focus`, `:disabled`. Layout: `layout: grid | horizontal | vertical`. No style
inheritance from parent — each widget starts fresh.

**Events:** Widgets post `Message` subclasses (`Button.Pressed`, `Input.Changed`).
Handlers: `on_<widget>_<message>()` or `@on(Widget.Message)`. Messages bubble up.

**Key bindings:** `BINDINGS` list on App/Screen/Widget. `Binding("key", "action_name",
"Description")`. Actions are `action_<name>()` methods. Focused widget's bindings
take priority, then bubble up. `show=False` hides from Footer.

**Gotchas:**
- `compose()` builds widget tree (called once) — not `render()` (for leaf renderables)
- `call_after_refresh()` when mounting then immediately scrolling
- Use Workers (`run_worker`) for async I/O — don't block the event loop

### Ratatui (Rust)

**Widget catalog:** Block, Paragraph, List/ListItem, Table/Row/Cell, Tabs,
BarChart/Bar/BarGroup, Chart/Dataset/Axis, Gauge, LineGauge, Sparkline,
Scrollbar, Canvas, Calendar. Stateful widgets have companion `*State` structs
(ListState, TableState, ScrollbarState).

**Layout:**
```rust
Layout::default()
    .direction(Direction::Vertical)
    .constraints([Percentage(10), Min(5), Fill(1)])
    .split(area)
```
Constraint types: `Percentage`, `Length`, `Min`, `Max`, `Ratio`, `Fill`.
Nest layouts for complex grids. Shorthand: `Layout::horizontal([...]).areas(area)`.

**Style:** `Style::default().fg(Color::Red).bg(Color::Black).add_modifier(Modifier::BOLD)`.
Colors: `Color::Red` (ANSI), `Color::Indexed(n)` (256), `Color::Rgb(r,g,b)` (truecolor).
Modifiers: BOLD, DIM, ITALIC, UNDERLINED, REVERSED, CROSSED_OUT.

**Rendering model:** Immediate mode — redraw every frame. `terminal.draw(|frame| { ... })`.
Frame diffing handled by crossterm — only changed cells are written. Never store layout
results — recompute each frame. Stateful widgets: `frame.render_stateful_widget(w, area, &mut state)`.

### Ink (TypeScript)

**Core components:** `Box` (flex container), `Text` (styled output), `Newline`,
`Spacer`, `Static` (render-once content for logs above interactive UI), `Transform`.

**Ink-UI components:** TextInput, EmailInput, PasswordInput, ConfirmInput, Select,
MultiSelect, Spinner, ProgressBar, Badge, StatusMessage, Alert, UnorderedList,
OrderedList.

**Layout:** `Box` supports `flexDirection`, `justifyContent`, `alignItems`,
`flexGrow`, `flexShrink`, `width`, `height`, `padding`, `margin`,
`borderStyle` ("single"|"double"|"round"|"bold"|"classic"). Yoga-layout (same
as React Native).

**Hooks:** Standard React (`useState`, `useEffect`) plus Ink-specific:
- `useInput((input, key) => ...)` — key flags: `leftArrow`, `rightArrow`,
  `upArrow`, `downArrow`, `return`, `escape`, `tab`, `backspace`, `meta`, `ctrl`
- `useApp()` — `{ exit }`
- `useFocus({ autoFocus, id })` — returns `{ isFocused }`
- `useFocusManager()` — `{ focusNext, focusPrevious, focus(id) }`

**Key differences from browser React:** No DOM, no CSS, no event bubbling, no
`onClick`. `Static` is write-once (log lines that scroll up). `useInput` replaces
all event listeners. No refs for measurement.

### Bubbletea (Go)

**Architecture (Elm MVU):** `Model` interface: `Init() Cmd`, `Update(Msg) (Model, Cmd)`,
`View() string`. `Cmd` = `func() Msg` for async side effects. `tea.Batch(cmds...)`
for concurrent commands. `tea.Quit` exits.

**Bubbles library:** list.Model (filterable, paginated), table.Model (navigable),
textinput.Model, textarea.Model, viewport.Model (scrollable pane), spinner.Model,
progress.Model (animated bar), paginator.Model, filepicker.Model, help.Model
(auto-generates key help), timer.Model, stopwatch.Model.

**Composition:** Embed bubbles in your model struct. Route messages to children in
Update: `m.list, cmd = m.list.Update(msg)`. Styling via lipgloss (separate lib).

**Gotchas:**
- `Update` returns a new model value (value semantics, not pointer)
- Always handle `tea.WindowSizeMsg` — call `SetSize()` on children or they render wrong
- `list.Model` needs a delegate for custom item rendering

---

## Workflow

```
Phase 1 — Specify    →   Phase 2 — Handoff             →   Phase 3 — Verify
Layout diagram            Load language expert:              Run the app, check:
Color palette             Skill("python-expert")   or       - Layout at different
Keybinding scheme         Skill("rust-expert")     or         terminal sizes
Widget selection          Skill("typescript-expert")        - All keybindings work
State matrix              Pass Component Spec block         - Color degradation
```

### Component Spec Template

```
## TUI COMPONENT SPEC: <AppName>

### Framework
Ratatui (Rust) / Textual (Python) / Ink (TypeScript) / Bubbletea (Go)

### Layout
[ASCII diagram with percentage splits]
Must handle resize — min terminal size: 80x24

### Color Palette
- Base tier: ANSI 16 (specify which colors for which roles)
- accent: bright cyan (ANSI 14)
- selected: reverse video
- border-focused: bright accent, border-unfocused: gray/dim
- error: red, success: green, warning: yellow
- Optional truecolor enhancement: [describe]

### Widgets (from framework catalog)
- [WidgetName] — [purpose] — [which pane]
- e.g., "DataTable — file listing — center pane, cursor_type='row'"

### Keybinding Scheme
| Key | Action | Context |
|-----|--------|---------|
| (table of all bindings, grouped by context/mode) |

### Component States
(Reference the state matrix — specify per-widget)

### Accessibility
- All actions reachable by keyboard
- Visible key help (footer bar or ? overlay)
- Color is never the only differentiator (add border/icon for errors)
- Screen reader support if framework provides it (Textual has some)
```

**tui-expert does NOT write implementation code.**
The language expert handles framework-specific code, toolchain, and testing.

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Designing only for truecolor | Base palette on ANSI 16 — it respects user themes |
| Vim-only keybindings | Arrow keys must always work — vim keys supplement |
| No resize handling | Always handle terminal resize events |
| Blank space for empty states | Show placeholder text with action hint |
| Color-only error indication | Add border change or icon — color-blind users exist |
| Fixed layout sizes | Use percentage/min/fill constraints, not absolute columns |
| No help/keybinding discovery | Footer bar or `?` overlay — discoverable first |
| `string.len()` for layout math | Use unicode-width — CJK/emoji take 2 columns |
| Writing framework code directly | Produce spec → hand off to language expert |
| No focus indication | Focused pane needs a visible border/style change |

## Outputs

- TUI Component Spec (layout diagram, color palette, keybindings, widget list, states)
- Framework recommendation with rationale
- Handoff to python-expert / rust-expert / typescript-expert for implementation
