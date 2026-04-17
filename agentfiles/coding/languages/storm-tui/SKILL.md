---
name: storm-tui
description: Use when building TUI apps with @orchetron/storm — a React-based compositor-driven terminal UI framework. Covers setup, rendering model, components, hooks, AI widgets, DevTools, and performance patterns.
---

# Storm TUI

React-based terminal UI framework. Cell-level diff renderer — only changed cells
written per frame. Dual-speed: React for structure, `requestRender()` for 60fps animation.

## Setup

```bash
npm install @orchetron/storm react typescript @types/react @types/node
```

`tsconfig.json` must target ESM:

```json
{ "compilerOptions": { "target": "ES2022", "module": "Node16",
  "moduleResolution": "Node16", "jsx": "react-jsx", "strict": true } }
```

```tsx
import { render, Box, Text, useApp, useInput } from "@orchetron/storm";

function App() {
  const { exit } = useApp();
  useInput((e) => { if (e.ctrl && e.key === "c") exit(); });
  return <Box borderStyle="round" padding={1}><Text bold color="#82AAFF">Hello</Text></Box>;
}

render(<App />).waitUntilExit();
// Run: npx tsx app.tsx
```

---

## Rendering Model

```
React commit → FrameScheduler → RenderPipeline.fullPaint() → DiffRenderer → TTY
                                   React → Layout → Buffer → Diff → TTY
requestRender()  ────────────────────────────────► Buffer → Diff → TTY  (0.5ms)
```

- `fullPaint`: structural changes — reconciles React tree, recomputes layout
- `requestRender()`: visual updates — skips React+Layout entirely, 10-20x faster
- WASM diff (33KB Rust module) auto-selected when ≤30% rows changed → 3.4x faster

---

## The Three Golden Rules

### Rule 1 — `useRef` + `requestRender()` for animation and live data

```tsx
// WRONG — full React reconciliation every tick
const [frame, setFrame] = useState(0);

// RIGHT — imperative repaint, 10-20x faster
const frameRef = useRef(0);
const { requestRender } = useTui();
useTick(100, () => { frameRef.current++; requestRender(); });
```

Storm warns you automatically if >10 React reconciliations/second occur.

### Rule 2 — `useCleanup()` not `useEffect` cleanup

```tsx
// WRONG — cleanup return NEVER fires in Storm's reconciler
useEffect(() => { const t = setInterval(tick, 1000); return () => clearInterval(t); }, []);

// RIGHT
const timerRef = useRef<ReturnType<typeof setInterval>>();
if (!timerRef.current) timerRef.current = setInterval(tick, 1000);
useCleanup(() => clearInterval(timerRef.current!));
```

### Rule 3 — `ScrollView` needs a height constraint

```tsx
// WRONG — expands forever, never scrolls
<ScrollView>{children}</ScrollView>

// RIGHT
<ScrollView flex={1}>{children}</ScrollView>
// or: <ScrollView height={20}>{children}</ScrollView>
```

---

## Core Hooks

| Hook | Use for |
|------|---------|
| `useApp()` | Quick access: `{ exit, rerender, clear }` |
| `useTui()` | Full context: `requestRender, exit, input, flushSync, clear, commitText` |
| `useInput(handler, opts?)` | Keyboard events. `opts.isActive`, `opts.priority` |
| `useTerminal()` | Reactive `{ width, height }` — auto-updates on resize |
| `useCleanup(fn)` | Cleanup on unmount (replaces `useEffect` return) |
| `useTick(ms, fn, opts?)` | Periodic updates. `opts.reactive=false` → imperative repaint |
| `useHotkey({ hotkeys })` | Declarative shortcuts with labels for help display |
| `useFocus(opts?)` | Make component focusable. Returns `{ isFocused, focus }` |
| `useMouse(handler)` | Mouse clicks, scroll, motion |

**`useInput` event shape:** `{ key: string, char: string, ctrl: boolean, shift: boolean, meta: boolean }`

**`useTick` modes:**
```tsx
// Reactive (triggers React re-render)
useTick(500, () => { tickRef.current++; });

// Imperative (cell-level repaint only, zero React overhead)
useTick(80, (tick) => { textRef.current.text = FRAMES[tick % FRAMES.length]; }, { reactive: false });
```

---

## Layout Components

```tsx
// Box — flex container (flexDirection defaults to "column")
<Box flexDirection="row" padding={1} borderStyle="round" borderColor="#82AAFF">
  <Box flex={1}>left</Box>
  <Box width={20}>right</Box>
</Box>

// Text — styled output
<Text bold dim color="#34D399" underline>content</Text>

// ScrollView — scrollable region (MUST have height constraint)
<ScrollView flex={1} stickToBottom>   {/* stickToBottom for chat */}
  {items.map(i => <Text key={i.id}>{i.text}</Text>)}
</ScrollView>

// StatusLine — bottom-anchored bar
<StatusLine items={[{ text: "q quit", color: "dim" }, { text: "/ search" }]} />
```

**borderStyle values:** `"single"` | `"double"` | `"round"` | `"bold"` | `"classic"`

---

## Common Components

`Box`, `Text`, `ScrollView`, `TextInput`, `Spinner` (14 types), `Tabs`, `Modal`,
`Table`, `DataGrid`, `Tree`, `Form`, `Select`, `CommandPalette`, `TextArea`,
`Markdown`, `DatePicker`, `DiffView`, `Calendar`, `Divider`, `StatusLine`

Full catalog: [docs/components.md](https://github.com/orchetron/storm/blob/main/docs/components.md)

---

## AI Widgets (15 total)

Purpose-built for agent terminal UIs. Import from `@orchetron/storm`.

```tsx
// OperationTree — animates via imperative cell mutation (no React churn)
<OperationTree nodes={[
  { id: "1", label: "Reading auth.ts", status: "completed", durationMs: 120 },
  { id: "2", label: "Editing code", status: "running" },
  { id: "3", label: "Running tests", status: "pending" },
]} />

// MessageBubble — chat message with role styling
<MessageBubble role="assistant">I'll fix the bug in auth.ts.</MessageBubble>
<MessageBubble role="user">Please check line 42.</MessageBubble>

// ApprovalPrompt — tool approval dialog with risk coloring
<ApprovalPrompt
  tool="execute_shell"
  risk="high"                       // "high" → red, "medium" → amber
  params={{ command: "rm -rf /tmp" }}
  timeout={30000}                   // auto-deny after 30s
  onSelect={(key) => {
    if (key === "y") run(); else if (key === "a") alwaysAllow(); else deny();
  }}
/>

// StreamingText — imperative streaming, no React re-renders per token
<StreamingText ref={textRef} />

// SyntaxHighlight — code with syntax coloring
<SyntaxHighlight language="typescript" code={src} />

// CostTracker — token/cost display
<CostTracker inputTokens={1200} outputTokens={340} model="claude-opus-4-7" />
```

All AI widgets: `OperationTree`, `MessageBubble`, `ApprovalPrompt`, `StreamingText`,
`SyntaxHighlight`, `TokenStream`, `ContextWindow`, `CostTracker`, `BlinkDot`,
`CommandBlock`, `CommandDropdown`, `ModelBadge`, `PerformanceHUD`, `ShimmerText`, `StatusLine`

Full reference: [docs/widgets.md](https://github.com/orchetron/storm/blob/main/docs/widgets.md)

---

## DevTools

```tsx
import { render, enableDevTools } from "@orchetron/storm";
const app = render(<App />);
enableDevTools(app);  // press 1/2/3/4 in terminal
```

| Key | Panel |
|-----|-------|
| `1` | Render heatmap — see what's repainting unnecessarily |
| `2` | Accessibility audit — live WCAG 4.5:1 contrast check |
| `3` | Time-travel — freeze + scrub 120 frames |
| `4` | Inspector — component tree, computed styles, FPS, events |

Non-blocking render middleware — app keeps running.

---

## Patterns

### Full-screen AI agent app

```tsx
function AgentApp() {
  const { width, height } = useTerminal();
  const { exit } = useApp();
  useInput((e) => { if (e.ctrl && e.key === "c") exit(); });

  return (
    <Box flexDirection="column" width={width} height={height}>
      <ScrollView flex={1} stickToBottom>
        <MessageBubble role="assistant">Working on it...</MessageBubble>
      </ScrollView>
      <OperationTree nodes={ops} />
      {showApproval && <ApprovalPrompt tool={tool} risk="medium" onSelect={handleApproval} />}
      <StatusLine items={[{ text: "Ctrl+C quit" }]} />
    </Box>
  );
}
```

### Dashboard with tabs

```tsx
const [active, setActive] = useState("overview");
useHotkey({ hotkeys: [
  { key: "1", label: "Overview", action: () => setActive("overview") },
  { key: "2", label: "Logs", action: () => setActive("logs") },
] });

return (
  <Box flexDirection="column" height="100%">
    <Tabs tabs={[{ key: "overview", label: "Overview" }, { key: "logs", label: "Logs" }]}
          activeKey={active} onChange={setActive} />
    <Box flex={1}>{active === "overview" ? <Overview /> : <Logs />}</Box>
    <StatusLine items={[{ text: "1/2 tabs" }, { text: "q quit" }]} />
  </Box>
);
```

**Warning:** The built-in `<Tabs>` registers its own `useInput` handler for arrow
keys. In multi-pane apps where arrows should only affect the *focused* pane, it
will intercept keys regardless of which pane has focus. Replace with a custom
display-only tab bar in that case:

```tsx
<Box flexDirection="row" gap={1}>
  {tabs.map((t, i) => (
    <Text
      key={t.key}
      bold={activeTab === t.key}
      dim={activeTab !== t.key}
      backgroundColor={activeTab === t.key ? "#2E2E32" : undefined}
    >{` ${i + 1} ${t.label} `}</Text>
  ))}
</Box>
// Then route tab cycling through your own useInput
```

### High-frequency animation (imperative)

```tsx
const FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"];
const spinnerRef = useRef<TextNode>(null);

useTick(80, (tick) => {
  if (spinnerRef.current) spinnerRef.current.text = FRAMES[tick % FRAMES.length];
}, { reactive: false });

return <Text ref={spinnerRef}>{FRAMES[0]}</Text>;
```

---

## Testing

```tsx
import { renderToString, TestInputManager, fireEvent } from "@orchetron/storm/testing";

// Render without a terminal
const output = renderToString(<App />, { width: 80, height: 24 });

// SVG snapshots for visual regression
const svg = renderToSvg(<App />, { width: 80, height: 24 });

// Simulate input
const input = new TestInputManager();
fireEvent.pressKey(input, { key: "return" });
```

---

## Quick Reference — Mistakes

| Mistake | Fix |
|---------|-----|
| `useState` for scroll/animation | `useRef` + `requestRender()` |
| `useEffect` cleanup return | `useCleanup(fn)` |
| `<ScrollView>` with no height | Add `flex={1}` or `height={N}` |
| `setInterval` leaking | `useCleanup(() => clearInterval(...))` |
| Not handling resize | `const { width, height } = useTerminal()` |
| `useEffect` for timers | `useTick(ms, fn)` |
| `<Box style={{...}}>` | Not supported — use individual props (`color`, `backgroundColor`, `width`, etc.) |
| `<Box onClick={...}>`, `<Text onClick={...}>` | Not supported — handle via `useInput` + focus state |
| `<Box borderBottomStyle="single">` | Use boolean shortcuts `borderBottom`, `borderRight`, `borderLeft`, `borderTop` OR full `borderStyle` |
| `overflowY="auto"` | Not a valid value — use `<ScrollView>` for scrollable regions |
| Recursive `<TreeView>` render + flat list map | Double-renders children. Pick one: flat list with `flattenVisible()` helper OR recursive render with single root |
| Search/input `<Box>` with slash on line 1, text on line 2 | Box defaults to `flexDirection="column"` — add `flexDirection="row"` for inline inputs |
| Relying on key-up / CapsLock events | Terminals don't reliably emit these. Use a named key (`r`, `Ctrl+Space`) as toggle instead of hold-modifiers |
| `<Tabs>` swallows arrow keys in multi-pane apps | Built-in tab component has its own `useInput` — replace with custom tab bar for pane-scoped arrow routing |
| `<Modal>` renders inline below main content | Storm Modal may flow in document order — use absolute-positioned `<Box position="absolute" top={...} left={...}>` for true overlays |

---

## Multi-Pane Layouts with Focus Management

Storm has no automatic focus system for Box-based panes. Roll your own with
state, a pane-cycle key (Tab), and conditional border colors.

```tsx
type Pane = "tree" | "top" | "bottom";
const [activePane, setActivePane] = useState<Pane>("tree");

useInput((e) => {
  if (e.key === "tab") {
    setActivePane(p => p === "tree" ? "top" : p === "top" ? "bottom" : "tree");
    return;
  }
  // Route arrow keys based on active pane
  if (activePane === "tree") {
    if (e.key === "j" || e.key === "down") navigateTree("down");
    // ...
  } else if (activePane === "top") {
    if (e.key === "h" || e.key === "left") cycleTab(-1);
    // ...
  }
});

// Visual focus: bright border on active pane, dim on inactive
<Box
  borderStyle="round"
  borderColor={activePane === "tree" ? "#FFFFFF" : "#525252"}
>...</Box>
```

**Three-pane layout (tree left, top-right, bottom-right):**

```tsx
<Box flex={1} flexDirection="row">
  <Box width={treePixels} borderStyle="round" .../>  {/* Tree */}
  <Box flexDirection="column" flex={1}>
    <Box flexGrow={topHeight} flexShrink={1} flexBasis={0} ... />    {/* Top */}
    <Box flexGrow={100 - topHeight} flexShrink={1} flexBasis={0} .../> {/* Bottom */}
  </Box>
</Box>
```

Use `flexGrow` with integer ratios (`55` / `45`) and `flexShrink={1} flexBasis={0}`
to make vertical splits resize fluidly.

### Resize mode pattern

Terminals can't detect modifier-hold reliably. Use a mode toggle instead:

```tsx
const [resizeMode, setResizeMode] = useState(false);

useInput((e) => {
  if (resizeMode) {
    if (e.key === "escape" || e.key === "r") { setResizeMode(false); return; }
    // Arrows grow/shrink the active pane in arrow direction
    if (activePane === "tree") {
      if (e.key === "right") setTreeWidth(w => Math.min(75, w + 3));
      if (e.key === "left")  setTreeWidth(w => Math.max(15, w - 3));
    }
    return;
  }
  if (e.key === "r") { setResizeMode(true); return; }
  // ... normal navigation
});
```

Show resize-mode indicator in footer/status so user sees they're in a different mode.

### Hint mode (Alfred-style shortcut overlay)

```tsx
const [hintMode, setHintMode] = useState(false);
useInput((e) => {
  if (e.ctrl && (e.key === "space" || e.char === " ")) {
    setHintMode(h => !h);
    return;
  }
  // Digit keys: in hint mode jump to tree item N; otherwise to tab N
  if (e.char && /[1-9]/.test(e.char)) {
    const n = parseInt(e.char) - 1;
    if (hintMode && activePane === "tree") setFocusedId(filteredTree[n]?.node.id);
    else setActiveTab(TABS[n]);
    setHintMode(false);
  }
});

// Render hints conditionally
{hintMode && <Text bold>{` [${i + 1}] ${label} `}</Text>}
```

### Tree navigation (flatten-visible pattern)

Don't recurse in render — flatten to a linear list, then map. This keeps
navigation indexes aligned with what's on screen.

```tsx
type FlatItem = { node: TreeNode; level: number };

function flattenVisible(nodes: TreeNode[], expandedIds: Set<string>, level = 0): FlatItem[] {
  const out: FlatItem[] = [];
  for (const node of nodes) {
    out.push({ node, level });
    if (expandedIds.has(node.id) && node.children) {
      out.push(...flattenVisible(node.children, expandedIds, level + 1));
    }
  }
  return out;
}

// Render as flat list — single <TreeRow> component, no recursion
{flatTree.map(({ node, level }, i) => (
  <TreeRow
    key={node.id}
    node={node}
    level={level}
    isFocused={node.id === focusedId}
  />
))}
```

---

## Overlays & Floating Panels

Storm's `<Modal>` component may render inline in document flow rather than
as a true overlay. For reliable floating panels, use absolute-positioned Box:

```tsx
{showFloating && (
  <Box
    position="absolute"
    top={Math.floor(height / 2) - 10}
    left={Math.floor(width / 2) - 22}
    width={44}
    flexDirection="column"
    borderStyle="double"
    borderColor="#FFFFFF"
    backgroundColor="#0B0B0D"
    paddingX={2}
    paddingY={1}
  >
    <Text bold>✦ Quick Panel</Text>
    {/* ... content */}
  </Box>
)}
```

Key requirements for a proper overlay:
1. `position="absolute"` — lifts out of flow
2. Explicit `top` / `left` / `width` — compute from `useTerminal()` dimensions
3. `backgroundColor` — opaque bg hides content beneath
4. Thicker/brighter border — visual distinction from main UI
5. Render last in the tree — higher stacking order

---

## useInput Event Details

```ts
{ key: string, char: string, ctrl: boolean, shift: boolean, meta: boolean }
```

- `e.key` — named keys: `"up"`, `"down"`, `"left"`, `"right"`, `"tab"`, `"return"`, `"escape"`, `"backspace"`, `"space"`, plus letter keys (`"q"`, `"j"`, etc.)
- `e.char` — actual character typed (respects shift/layout). Use for text input and symbol keys like `[`, `]`, `<`, `>`
- `e.ctrl` / `e.shift` / `e.meta` — modifier booleans

**Common gotchas:**
- `Ctrl+Space` detection: `e.ctrl && (e.key === "space" || e.char === " ")`
- Symbol keys vary by terminal — check both `e.key` and `e.char` (`e.key === "[" || e.char === "["`)
- Shift+Arrow: `e.shift && e.key === "left"` — not all terminals distinguish this
- `Ctrl+Tab`: may be swallowed by terminal multiplexer (tmux/screen)
- No `e.type === "keyup"` — only keydown events fire

---

## Recipe: Feature-Rich Multi-Pane Explorer

Combines all patterns: tree + tabs + focus management + resize mode + hints + overlay.

```tsx
function Explorer() {
  const { width, height } = useTerminal();
  const [activePane, setActivePane] = useState<"tree" | "top" | "bottom">("tree");
  const [treeWidth, setTreeWidth] = useState(25);
  const [topHeight, setTopHeight] = useState(55);
  const [resizeMode, setResizeMode] = useState(false);
  const [hintMode, setHintMode] = useState(false);
  const [showFloat, setShowFloat] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [focusedId, setFocusedId] = useState(initialId);
  const [expandedIds, setExpandedIds] = useState(new Set<string>());

  const flatTree = useMemo(
    () => flattenVisible(TREE_DATA, expandedIds),
    [expandedIds]
  );

  useInput((e) => {
    // Modal layers first (floating, help, search) — return early
    if (showFloat) { /* handle then return */ }
    if (resizeMode) { /* handle then return */ }

    // Globals: quit, help, search, float toggle, hint toggle
    if (e.key === "q") exit();
    if (e.key === "f") setShowFloat(v => !v);
    if (e.ctrl && e.char === " ") setHintMode(h => !h);

    // Pane cycle
    if (e.key === "tab") setActivePane(p => /* cycle */);

    // Pane-specific routing
    if (activePane === "tree") navigateTree(e);
    else if (activePane === "top") cycleTab(e);
  });

  return (
    <Box flexDirection="column" width={width} height={height}>
      <Header />
      <Box flex={1} flexDirection="row">
        <TreePane width={Math.floor((width * treeWidth) / 100)} focused={activePane === "tree"} />
        <Box flexDirection="column" flex={1}>
          <TopPane flexGrow={topHeight} focused={activePane === "top"} />
          <BottomPane flexGrow={100 - topHeight} focused={activePane === "bottom"} />
        </Box>
      </Box>
      <Footer bindings={resizeMode ? resizeBindings : normalBindings} />
      {showFloat && <FloatingPane />}  {/* absolute-positioned, renders last */}
    </Box>
  );
}
```

This recipe handles: 3-focusable-panes, fluid resize, search/filter, keyboard-only
navigation, shortcut hints, and floating overlays. Drop in custom tree/tabs
components instead of Storm's built-ins if you need precise arrow-key routing.

---

## Themes & Plugins

```tsx
// 12 built-in themes: Arctic, Midnight, Ember, Voltage, Neon, High Contrast, etc.
import { ThemeProvider } from "@orchetron/storm";
<ThemeProvider theme="midnight"><App /></ThemeProvider>

// Live hot-reload: drop a .storm.css file next to your app

// Plugins
import { VimPlugin, StatusBarPlugin } from "@orchetron/storm/plugins";
render(<App />, { plugins: [new VimPlugin(), new StatusBarPlugin()] });
```

## SSH Server

```tsx
import { createSSHServer } from "@orchetron/storm/ssh";
createSSHServer({ port: 2222, app: App });  // built-in auth + rate limiting
```
