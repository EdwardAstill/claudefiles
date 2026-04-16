---
name: browser-control
description: >
  Use when automating a browser — navigating pages, clicking, filling forms,
  selecting dropdowns, scrolling, screenshots, extracting content, or
  downloading files. Primary tool: firefox-devtools MCP (connects to user's
  running Zen browser with existing sessions/cookies). Fallbacks: af browser
  (CDP/Chrome), Playwright (complex SPAs).
---

Three tools. Pick the right one.

## Tool decision

| Situation | Use |
|-----------|-----|
| Control user's Zen browser (with logins/cookies) | `firefox-devtools` MCP |
| Chrome automation (no existing session needed) | `af browser` |
| SPA where elements won't settle / complex waiting | Playwright |
| File download via click | Playwright (`expect_download`) |
| Network interception / mocking | Playwright |

**Default: `firefox-devtools` MCP** — connects to the user's running Zen browser
via `--connect-existing`. All cookies, logins, and tabs are preserved.

---

## firefox-devtools MCP — Primary Tool

Connects to the user's running Zen browser (Firefox fork) via Marionette + BiDi.
No sign-in required — uses the real browser session.

### Requirements

Zen must be running with: `zen-browser --marionette --remote-debugging-port=9222`
(already configured in user's desktop entry at `~/.local/share/applications/zen.desktop`).

### Core workflow

1. **List tabs** → `list_pages` — see all open tabs, find the one you need
2. **Select tab** → `select_page` — by index, URL substring, or title
3. **Snapshot DOM** → `take_snapshot` — get UIDs for all interactive elements
4. **Act** → `click_by_uid`, `fill_by_uid`, `hover_by_uid` — use UIDs from snapshot
5. **Re-snapshot** → after any navigation or interaction, take a fresh snapshot

### Available tools (via MCP)

| Tool | Purpose |
|------|---------|
| `list_pages` | List all open tabs |
| `select_page` | Switch to tab by index/URL/title |
| `new_page` | Open new tab |
| `close_page` | Close current tab |
| `navigate_page` | Go to URL |
| `navigate_history` | Back/forward |
| `take_snapshot` | DOM snapshot with stable UIDs |
| `click_by_uid` | Click element by UID |
| `fill_by_uid` | Type into input by UID |
| `fill_form_by_uid` | Fill multiple form fields |
| `hover_by_uid` | Hover element |
| `drag_by_uid_to_uid` | Drag and drop |
| `upload_file_by_uid` | Upload file to input |
| `screenshot_page` | Full page screenshot (use `saveTo` to save to disk) |
| `screenshot_by_uid` | Element screenshot |
| `list_network_requests` | Network activity |
| `get_network_request` | Request details |
| `list_console_messages` | Console output |
| `accept_dialog` / `dismiss_dialog` | Handle alerts/confirms |
| `set_viewport_size` | Resize viewport |

### Key patterns

```
# Find and switch to a tab
list_pages → select_page(url="pinterest")

# Interact with elements (always snapshot first)
take_snapshot → click_by_uid(uid="1_30") → take_snapshot (refresh UIDs)

# Screenshot to disk (avoids base64 in context)
screenshot_page(saveTo="/tmp/page.png") → Read /tmp/page.png

# Scoped snapshot (reduce noise)
take_snapshot(selector="#main-content", maxLines=50)
```

### Limitations in --connect-existing mode

- BiDi-dependent features (console events, network events) may be limited
- All other features work normally
- Cannot launch browser — must already be running with --marionette

---

## af browser — Full Reference

Session persists. Browser stays open between commands.

### Lifecycle

```bash
af browser start                     # headless Puppeteer Chrome (port 9222)
af browser start --headed            # visible window
af browser start --firefox           # Firefox (CDP limited — prefer Chrome)
af browser start --port 9223         # custom port
af browser start --url https://...   # open URL on launch
af browser stop
af browser status                    # pid, port, tabs, active tab
```

Connect to already-running browser on 9222:
```bash
af browser start  # auto-detects existing session
```

### Navigation

```bash
af browser go https://example.com
af browser tabs                      # list all tabs with URLs
af browser tab 1                     # switch to tab by index
af browser new-tab https://...       # open new tab (becomes active)
af browser close-tab                 # close active tab
af browser close-tab 2               # close tab by index
```

### Content extraction

```bash
af browser read                      # full page text
af browser read "article.content"    # CSS selector → text
af browser html                      # full page HTML
af browser html "#main"              # element HTML
af browser eval "document.title"
af browser eval "window.location.href"
af browser eval "document.readyState"          # 'complete' = fully loaded
af browser eval "!!document.querySelector('.app')"  # check element exists
af browser eval "document.querySelector('a.dl')?.href"  # get attribute
```

### Interaction

```bash
af browser click "button.submit"
af browser click "a[href*='download']"
af browser hover ".menu-item"               # trigger :hover / mouseover
af browser fill "input[name=q]" "query"
af browser fill "input[type=email]" "user@example.com"
af browser select "select#country" "United Kingdom"   # by value or text
af browser select "select[name=size]" "Large"
af browser wait ".results"                  # poll until selector appears
af browser wait ".loaded" --timeout 30000  # 30s timeout
af browser type "hello"                    # keyboard into focused element
```

### Keyboard

```bash
af browser key enter                 # submit form
af browser key tab                   # move focus
af browser key escape
af browser key arrowdown
af browser key space
af browser key enter --focus "input[name=q]"  # focus selector then press key
```

Supported keys: `enter`, `tab`, `escape`, `space`, `backspace`, `delete`,
`arrowup`, `arrowdown`, `arrowleft`, `arrowright`, `home`, `end`,
`pageup`, `pagedown`, `f1`–`f12`

### Scrolling

```bash
af browser scroll                    # scroll down 300px (default)
af browser scroll --y 600            # scroll down 600px
af browser scroll --y -300           # scroll up
af browser scroll --x 200            # scroll right
af browser scroll ".results"         # scroll element into view
```

### Screenshots

```bash
af browser snap                              # viewport → /tmp/browser-snap.png
af browser snap "#content"                  # element only
af browser snap --full-page --out /tmp/p.png
# After snap: Read tool on the PNG path to view it
```

### Debugging

```bash
# Console
af browser console                         # collect 2s of messages
af browser console --duration 5            # longer window
af browser console --watch                 # stream continuously (Ctrl+C)
af browser console --watch --level error   # errors only

# Network — CDP-based (real status codes, MIME types, timings)
af browser network                         # requests from last 1.5s
af browser network --filter "api"          # filter by URL pattern/regex
af browser network --errors                # 4xx/5xx only
af browser network --watch                 # stream in real time (Ctrl+C)
af browser network --watch --filter "api"  # stream + filter

# URL matching
af browser wait-for-url "dashboard"        # wait for redirect (OAuth, login)
af browser wait-for-url "/callback" --timeout 60000

# Accessibility
af browser a11y
```

---

## Common workflows

### Search form
```bash
af browser start
af browser go https://site.com
af browser fill "input[name=q]" "query"
af browser key enter --focus "input[name=q]"
af browser wait ".results"
af browser read ".results"
```

### Dropdown + submit
```bash
af browser go https://site.com/form
af browser select "select#category" "Technology"
af browser fill "input[name=title]" "My Title"
af browser click "button[type=submit]"
af browser wait ".success-message"
```

### Infinite scroll / pagination
```bash
af browser go https://site.com/feed
af browser read ".items"
af browser scroll --y 2000
af browser wait ".items:nth-child(20)"   # wait for more items
af browser read ".items"
```

### OAuth / redirect flow
```bash
af browser start --headed
af browser go https://site.com/login
af browser fill "input[name=email]" "user@example.com"
af browser fill "input[type=password]" "password"
af browser click "button[type=submit]"
af browser wait-for-url "dashboard" --timeout 15000   # wait for redirect
af browser eval "document.cookie"                      # grab session cookie if needed
```

### Debug API calls while navigating
```bash
af browser network --watch --filter "api" &   # background stream
af browser go https://app.example.com
# watch requests appear in terminal
```

### Extract href/src before curl
```bash
af browser go "https://sci-hub.st/10.1038/nature12345"
af browser eval "document.querySelector('iframe#pdf')?.src || document.querySelector('embed')?.src"
# then curl that URL
```

### Screenshot check
```bash
af browser go https://localhost:3000
af browser snap --out /tmp/check.png
# Read /tmp/check.png
```

---

## Playwright — Python via uv

Use when `af browser wait` keeps failing on JS-heavy SPAs, or for file downloads.
Playwright auto-waits for elements to be visible + stable.

```bash
uv run --with playwright python3 script.py
```

**Available browsers:**
- `~/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`
- `~/.cache/ms-playwright/firefox-1509/firefox/firefox`
- `~/.cache/ms-playwright/webkit-2248/pw_run.sh`

### Common patterns

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("https://example.com")

    # Auto-wait — visible + stable before action
    page.click("button.submit")
    page.fill("input[name=q]", "query")
    page.press("input[name=q]", "Enter")
    page.select_option("select#size", "Large")

    # Explicit waits
    page.wait_for_load_state("networkidle")
    page.wait_for_selector(".results")

    # Extract
    text = page.inner_text("article")
    href = page.get_attribute("a.download", "href")

    # Screenshot
    page.screenshot(path="/tmp/snap.png", full_page=True)

    # File download
    with page.expect_download() as dl:
        page.click("a.download-btn")
    dl.value.save_as("/tmp/file.pdf")

    browser.close()
```

### Network interception

```python
page.route("**/*.jpg", lambda r: r.abort())              # block images
page.route("**/api/**", lambda r: r.fulfill(body='{}'))  # mock endpoint
```

---

## Common mistakes

| Mistake | Fix |
|---------|-----|
| `wait` fails on SPA | Switch to Playwright — better auto-wait |
| Firefox with `af browser` — missing features | CDP support limited; use Chrome |
| Reading before JS renders | `af browser wait ".selector"` first |
| No `af browser start` | Check `af browser status` first |
| Static page → browser overhead | `curl` is faster and cheaper |
| Playwright not found | `uv run --with playwright python3 ...` — no install needed |
| Download via browser click | Use Playwright `expect_download` context manager |
| Waiting for redirect/OAuth | `af browser wait-for-url "pattern"` — don't sleep |
| Network shows no requests | Use `--watch` — one-shot only catches 1.5s window |
