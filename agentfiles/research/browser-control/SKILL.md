---
name: browser-control
description: >
  Use when driving a real browser session. Trigger phrases: "open this in my
  browser", "log into X", "click the button", "fill out the form", "screenshot
  this page", "scrape the JS-rendered site", "it needs my cookies", "use my
  logged-in session", "navigate to and then", "check the page after login",
  "the data only loads after JavaScript runs". Uses foxpilot CLI exclusively via
  Bash — headless for stateless recon, --zen for the user's authenticated Zen
  session. Do NOT use for pure-HTTP scraping where JS is not required (use
  web-scraper) or for converting a file already on disk to markdown (use
  file-converter).
---

Use the **foxpilot CLI** (`Bash` tool) for all browser interaction. No MCP tools.

## Modes

| Flag | Behaviour |
|------|-----------|
| *(none)* | **Headless** — ephemeral Firefox, no existing session, fully stateless |
| `--zen` / `-z` | **Zen** — connects to user's running Zen browser with all cookies/logins |

---

## Critical: headless is stateless

Each foxpilot command in headless mode **starts and kills its own Firefox process**. Navigation state is NOT shared between separate Bash calls.

```bash
# BROKEN — 'read' opens a fresh browser, gets about:blank
foxpilot go https://example.com
foxpilot read                        # ✗ different browser instance

# RIGHT — 'go' already returns page content in its output
foxpilot go https://example.com      # ✓ output includes title, url, visible text

# RIGHT — chain with && for stateful headless flow
foxpilot go https://example.com && foxpilot read  # ✗ still two processes
```

**In headless: use `go` output directly.** It calls `feedback()` which returns action + URL + title + visible page text. No need to call `read` separately.

For zen mode, each command connects to the existing Zen session, so `read` after `go` works fine.

---

## Zen auto-launch behaviour

foxpilot handles Zen state automatically:
- **Zen not running** → launches `zen-browser --marionette` automatically
- **Zen running without `--marionette`** → kills zen-bin and relaunches with `--marionette` (session/tabs restored by Zen on restart)
- **Zen running with `--marionette`** → connects directly

No manual restart needed in most cases.

---

## Command reference

### Observation

```bash
foxpilot --zen tabs                          # list all open tabs (zen only)
foxpilot --zen url                           # current URL + title
foxpilot --zen read                          # extract page text (connects to current Zen page)
foxpilot --zen read "article.main"          # scoped to CSS selector
foxpilot --zen read --tab github --full     # specific tab, no truncation (default: 3000 chars)
foxpilot --zen find "Sign in"              # find visible elements by text/aria-label/placeholder
foxpilot --zen screenshot /tmp/page.png    # viewport screenshot
foxpilot --zen screenshot --el "#header"   # element screenshot by CSS selector
foxpilot --zen fullpage /tmp/full.png      # full scroll-height screenshot
foxpilot --zen html                         # raw HTML body (truncated to 8000 chars)
foxpilot --zen html ".sidebar"             # scoped element HTML
foxpilot --zen styles                       # computed styles + CSS vars + color palette (body)
foxpilot --zen styles ":root"              # design tokens from :root CSS custom properties
foxpilot --zen styles "header"             # element-level styles
foxpilot --zen assets                       # images (with dims), fonts, stylesheets, favicon, bg images
```

### Navigation

```bash
foxpilot go https://example.com             # headless — output includes visible page content
foxpilot --zen go https://github.com        # zen — navigate + return page state
foxpilot search "python asyncio"            # DuckDuckGo structured results (headless)
foxpilot --zen back
foxpilot --zen forward
```

### Interaction (all return URL + title + visible text after action)

```bash
foxpilot --zen click "Sign in"
foxpilot --zen click "Submit" --role button
foxpilot --zen click "New issue" --tag a
foxpilot --zen fill "Search" "foxpilot"
foxpilot --zen fill "Password" "secret" --submit    # press Enter after filling
foxpilot --zen select "Country" "United Kingdom"
foxpilot --zen scroll --y 1200
foxpilot --zen scroll --y -600
foxpilot --zen scroll --to "#footer"
foxpilot --zen key enter
foxpilot --zen key escape --focus "#modal-close"
# supported keys: enter, tab, escape, space, backspace, delete,
#                 arrowup, arrowdown, arrowleft, arrowright,
#                 home, end, pageup, pagedown
```

### Tab management (zen only)

```bash
foxpilot --zen tab 2                         # switch to tab by index
foxpilot --zen tab github                    # switch by URL/title substring
foxpilot --zen new-tab https://example.com
foxpilot --zen close-tab 3
```

### Escape hatches

```bash
foxpilot --zen js "document.title"
foxpilot --zen css-click "#submit-btn"
foxpilot --zen css-fill "input[name=email]" "alice@example.com"
```

---

## Key patterns

```bash
# Headless web research — use go output, not read
foxpilot search "python mcp server"
foxpilot go https://docs.python.org/3/library/asyncio.html
# → output already has title + url + visible text

# Zen — act on user's browser
foxpilot --zen tabs
foxpilot --zen tab 0
foxpilot --zen click "Sign in"
foxpilot --zen fill "Email" "user@example.com" --submit
foxpilot --zen read                   # read current state

# Screenshot → Read tool to view
foxpilot --zen fullpage /tmp/page.png
# → Read /tmp/page.png

# Design inspection
foxpilot --zen fullpage /tmp/reference-full.png
foxpilot --zen styles ":root"
foxpilot --zen assets
```

---

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Calling `read` after `go` in headless | Use `go` output directly — it includes page content |
| Acting without knowing page state | Run `foxpilot --zen read` or `foxpilot --zen url` first |
| Text match fails | Use `foxpilot --zen find "text"` to see what's visible, then `css-click` |
| Zen not responding | foxpilot auto-restarts Zen with `--marionette` — just retry |
| geckodriver not found | `sudo pacman -S geckodriver` |
