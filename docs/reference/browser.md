# Browser Automation

The `af browser` command provides a lightweight Chrome DevTools Protocol (CDP) client for browser automation. Unlike `af screenshot` which uses Playwright, `af browser` talks directly to the browser via WebSockets, allowing for persistent sessions and fine-grained control.

---

## Why use `af browser`?

- **Persistent Sessions:** The browser stays running between command invocations. You can start a browser, navigate, click, fill forms, and take screenshots in separate steps.
- **No Heavy Dependencies:** It doesn't require Playwright or Puppeteer to be installed in your project (though it can use them to find a browser binary).
- **Cross-Browser:** Supports Chrome, Chromium, and Firefox (via remote debugging).
- **CDP Power:** Access to the full Chrome DevTools Protocol, including accessibility trees, console logs, and network events.

---

## Getting Started

### 1. Start a browser

By default, it starts a headless Chrome/Chromium.

```bash
af browser start
af browser start --headed        # See the browser window
af browser start --firefox       # Use Firefox instead
af browser start --port 9222     # Use a specific port
```

If you already have a browser running with remote debugging enabled (e.g., `google-chrome --remote-debugging-port=9222`), `af browser` will automatically connect to it.

### 2. Basic Navigation and Interaction

```bash
af browser go https://google.com
af browser fill "input[name='q']" "agentfiles github"
af browser click "input[name='btnK']"
af browser wait ".v7W49e"        # Wait for search results
```

### 3. Extraction and Inspection

```bash
af browser read                  # Get page text
af browser html "h3"             # Get HTML of an element
af browser a11y                  # Dump accessibility tree
af browser console               # Dump recent console logs
af browser network               # List network requests
```

### 4. Visualization

```bash
af browser snap                  # Take a screenshot of the viewport
af browser snap --full-page       # Capture the entire scrollable page
af browser snap "selector"       # Capture a specific element
```

Screenshots are saved to `/tmp/browser-snap.png` by default.

---

## Session Management

`af browser` tracks the active session in `~/.claude/data/browser-session.json`.

```bash
af browser status                # Show PID, port, and open tabs
af browser tabs                  # List all open tabs/pages
af browser tab 2                 # Switch to the third tab
af browser stop                  # Close the browser and clear session
```

---

## Tool Comparison

| Feature | `af browser` | `af screenshot` |
|---------|--------------|-----------------|
| **Backend** | Direct CDP (WebSockets) | Playwright (High-level API) |
| **Session** | Persistent | One-off (starts/stops every time) |
| **Dependencies** | None (standard library + `websocket-client`) | Playwright + Browser binaries |
| **Speed** | Fast (persistent) | Slower (startup overhead) |
| **Use Case** | Complex automation, multi-step flows | Quick visual verification of a URL |
