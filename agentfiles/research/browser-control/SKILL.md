---
name: browser-control
description: >
  Use when automating a browser — navigating pages, clicking, filling forms,
  selecting dropdowns, scrolling, screenshots, extracting content, or
  downloading files. Primary tool: foxpilot MCP (connects to user's running Zen
  browser with existing sessions/cookies, or runs headless Firefox). Fallback:
  Playwright (file downloads, network interception, complex SPAs).
---

Two tools. Pick the right one.

## Tool decision

| Situation | Use |
|-----------|-----|
| Control user's Zen browser (with logins/cookies) | `foxpilot` MCP, `mode="zen"` |
| Independent web research (no existing session needed) | `foxpilot` MCP, `mode="headless"` |
| File download via click | Playwright (`expect_download`) |
| Network interception / mocking | Playwright |

**Default: `foxpilot` MCP** — connects to the user's running Zen browser or launches
headless Firefox. All cookies, logins, and tabs are preserved in zen mode.

---

## foxpilot MCP — Primary Tool

Wraps geckodriver + Selenium with high-level text-based tools. Every action tool
returns what it did + current URL, title, and visible page content — no snapshot
round-trip needed.

### Requirements

- **Zen mode**: Zen must be running with `--marionette --remote-debugging-port=9222`
  (configured in `~/.local/share/applications/zen.desktop`).
- **Headless mode**: geckodriver must be installed (`sudo pacman -S geckodriver`).
- `foxpilot` binary installed via `uv tool install /home/eastill/projects/foxpilot`.

### Core workflow

```
# Web research (headless — default)
search(query="python mcp server") → go(url) → read()

# Zen browser (user's session with cookies/logins)
tabs()                              → see all open tabs
tab_switch(target="1")              → activate tab by index
go(url, mode="zen")                 → navigate
click("Sign in", mode="zen")        → click by visible text
fill("Email", "user@...", mode="zen") → fill input by label
```

### Available MCP tools

| Tool | Key parameters | Description |
|------|---------------|-------------|
| `tabs` | — | List all Zen tabs (port 9222) |
| `tab_switch` | `target` | Switch tab by index or URL/title |
| `read` | `selector?, mode?` | Extract main page content |
| `screenshot` | `path?, selector?, mode?` | Screenshot → disk (Read path to view) |
| `url` | `mode?` | Current URL + title |
| `find` | `text, mode?` | Find visible elements by text |
| `go` | `url, mode?` | Navigate to URL |
| `search` | `query, mode?` | DuckDuckGo search, structured results |
| `click` | `description, role?, tag?, mode?` | Click by text/label |
| `fill` | `description, value, submit?, mode?` | Fill input by label/placeholder |
| `select` | `description, value, mode?` | Select dropdown option |
| `scroll` | `y?, to?, mode?` | Scroll page |
| `back` | `mode?` | Navigate back |
| `forward` | `mode?` | Navigate forward |
| `key` | `name, focus?, mode?` | Press key (enter, tab, escape, etc.) |
| `new_tab` | `url?, mode?` | Open new tab |
| `close_tab` | `index?, mode?` | Close tab |
| `js` | `expression, mode?` | Evaluate JavaScript |
| `html` | `selector?, mode?` | Extract raw HTML |
| `css_click` | `selector, mode?` | Click by CSS selector (escape hatch) |
| `css_fill` | `selector, value, mode?` | Fill by CSS selector (escape hatch) |

`mode` defaults to `"headless"`. Pass `mode="zen"` to operate on user's browser.

### Key patterns

```
# Always check the page after acting — feedback is included automatically
click("Log in", mode="zen")
# → returns: clicked <button> "Log in"
#            url: https://example.com/dashboard
#            title: Dashboard
#            visible: Welcome back! ...

# Screenshot to disk (avoid base64 in context)
screenshot(path="/tmp/page.png", mode="zen")
# → then: Read /tmp/page.png

# Scoped content extraction
read(selector="article", mode="zen")

# Search the web without touching user's browser
search("python asyncio tutorial")
go("https://docs.python.org/3/library/asyncio.html")
read()
```

### Limitations

- **Tab listing** (`tabs`): Uses port 9222 — requires Zen with `--remote-debugging-port=9222`.
- **Bot detection**: `navigator.webdriver` is suppressed on connect but some sites may still detect automation. For sensitive interactions, observe first (read/screenshot) before acting.
- **geckodriver `--connect-existing`**: Only exposes the single window geckodriver attaches to for action commands. Use `tab_switch` to activate the desired tab in the UI first, then use action commands.
- **File downloads**: Use Playwright `expect_download` context manager.
- **No network interception**: Use Playwright.

### CLI equivalent (foxpilot binary)

Same commands available as a CLI for manual testing:

```bash
foxpilot search "python websockets"
foxpilot --zen tabs
foxpilot --zen read
foxpilot --zen click "Sign in"
foxpilot --zen screenshot /tmp/snap.png
```

---

## Playwright — Fallback

Use when foxpilot fails (SPAs with complex JS loading, file downloads, network interception).

```bash
uv run --with playwright python3 script.py
```

**Available browsers:**
- `~/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`
- `~/.cache/ms-playwright/firefox-1509/firefox/firefox`

### Common patterns

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")

    page.click("button.submit")
    page.fill("input[name=q]", "query")
    page.press("input[name=q]", "Enter")
    page.wait_for_selector(".results")
    text = page.inner_text("article")

    # File download
    with page.expect_download() as dl:
        page.click("a.download-btn")
    dl.value.save_as("/tmp/file.pdf")

    browser.close()
```

---

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Using action tools without knowing current page state | Call `read()` or `url()` first |
| Text match fails | Try `find(text)` to see what's actually visible, then use `css_click` escape hatch |
| geckodriver not found | `sudo pacman -S geckodriver` |
| Zen not listening on marionette | Relaunch Zen — desktop entry should add `--marionette` automatically |
| Bot detection on site | Observe first (read/screenshot), then act; avoid rapid repeated actions |
| File download needed | Switch to Playwright |
