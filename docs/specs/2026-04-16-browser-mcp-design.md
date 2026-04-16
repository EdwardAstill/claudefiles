# Browser MCP — Design Spec

Standalone project. A CLI tool + MCP server for browser automation, designed around how an AI agent actually wants to use a browser.

Replaces `af browser` (CDP/Chrome) and `af zen` (Selenium/Marionette) with a single tool that speaks Firefox-native protocols and works in two modes: connected to the user's Zen browser, or running its own headless Firefox.

## Project name

`foxpilot` — working name, standalone repo.

## The problem

Existing tools are too low-level for agent use:

- **firefox-devtools MCP**: snapshot-then-act-by-UID model. Every interaction requires a snapshot round-trip. No search. No "read this page and tell me what you see."
- **af browser**: CSS selectors, one command at a time, CDP-based (Chrome-first, Firefox support is weak).
- **af zen**: closer to right (text-based element finding, feedback after every action) but Selenium is heavy, geckodriver is flaky with `--connect-existing`, and it's buried inside the agentfiles CLI.

What I want as an agent: hand me a URL and I'll read it. Tell me to search something and I will. Point me at your browser and I'll see what you see or do what you need done. I shouldn't need to think about selectors, UIDs, or protocol details.

## Two modes

### Zen mode — "your browser"

Connect to the user's running Zen browser. Sees their tabs, cookies, logins, history. Two use cases:

1. **Observe**: read tabs, summarize pages, see what the user is working on
2. **Act**: click, fill, navigate, search — do things in the user's session

Connection: Marionette protocol via geckodriver `--connect-existing` on port 2828. Zen must be running with `--marionette`. The desktop entry at `/usr/share/applications/zen.desktop` should be patched to include `--marionette` in the Exec line (or the user launches Zen with the flag).

### Headless mode — "my browser"

Launch a private headless Firefox instance for independent work. Ephemeral — starts, does the job, shuts down. No state persists between invocations.

Used when: the agent needs to research something, fetch a page, or search the web without touching the user's browser.

Connection: launch Firefox with `--headless --marionette`, connect via geckodriver, tear down when done.

### Mode selection

- CLI: `foxpilot --zen <command>` vs `foxpilot <command>` (headless is default)
- MCP: each tool has a `mode` parameter: `"zen"` or `"headless"` (default `"headless"`)
- Agent decides which mode based on context: if operating on user's session, zen. If doing independent research, headless.

## CLI commands

The CLI is the source of truth. The MCP wraps these commands as tools with the same names and semantics.

### Observing (read-only)

```
foxpilot tabs                              # list all open tabs (zen only)
foxpilot read [--tab <index|substring>]    # extract page text (main content)
foxpilot screenshot [--tab <index|substr>] # viewport screenshot to /tmp/
foxpilot find <text>                       # find visible elements matching text
foxpilot url                               # current page URL + title
foxpilot console                           # recent console messages
foxpilot network [--filter <pattern>]      # recent network requests
```

### Acting

```
foxpilot go <url>                          # navigate to URL
foxpilot search <query>                    # web search, return results
foxpilot click <description>               # click element by visible text/label
foxpilot fill <description> <value>        # fill input by label/placeholder
foxpilot select <description> <value>      # select dropdown option
foxpilot scroll [--to <selector>] [--y N]  # scroll page
foxpilot back                              # navigate back
foxpilot forward                           # navigate forward
foxpilot key <name>                        # press a key (enter, tab, escape...)
foxpilot tab <index|substring>             # switch to tab (zen only)
foxpilot new-tab [url]                     # open new tab
foxpilot close-tab [index]                 # close a tab
```

### Escape hatches

```
foxpilot js <expression>                   # evaluate JavaScript
foxpilot html [selector]                   # raw HTML extraction
foxpilot css-click <selector>              # click by CSS selector
foxpilot css-fill <selector> <value>       # fill by CSS selector
```

### Key design decisions in the CLI

**1. Text-based element finding (not selectors, not UIDs)**

`click "Sign in"` not `click "#btn-auth-submit"` or `click_by_uid "3_42"`. The tool finds elements by visible text, aria-label, placeholder, title — the same things a human would use to describe what to click. Falls back to CSS selector via the `css-*` escape hatches when text matching fails.

Implementation: XPath search across text content, aria-label, placeholder, title attributes. Filter to visible elements. Priority order: exact match > contains match. Prefer interactive elements (button, a, input) over generic containers.

**2. Feedback after every action**

Every mutating command prints what it did, then what's visible now:

```
$ foxpilot click "Sign in"
clicked <button> "Sign in"
-> url: https://example.com/auth
-> title: Login — Example
-> visible:
  Email address
  Password
  Remember me
  Sign in
  Forgot password?
```

This gives the agent immediate context for its next action without requiring a separate read/snapshot step. This is what `af zen` does well — carry it forward.

**3. `search` is a first-class command**

```
$ foxpilot search "python websocket libraries"
[1] websockets - PyPI
    https://pypi.org/project/websockets/
    A library for building WebSocket servers and clients in Python...

[2] websocket-client - PyPI
    https://pypi.org/project/websocket-client/
    WebSocket client for Python with a low-level API...

[3] ...
```

Implementation: navigate to a search engine (DuckDuckGo — no login, no captchas, clean HTML), extract results. In zen mode, uses the user's default search engine via the address bar. In headless mode, always DuckDuckGo.

**4. `read` is smart about content extraction**

Not a raw `document.body.innerText` dump. Extracts the main content area, strips nav/footer/ads boilerplate. Uses a readability-style heuristic (largest text-dense block) or falls back to full body text.

```
$ foxpilot read
[Example Blog — How to Build a CLI Tool]
https://example.com/blog/cli-tools

How to Build a CLI Tool

Building a CLI tool in Python is straightforward...
(2,400 chars)
```

**5. `tabs` shows what matters**

```
$ foxpilot tabs
>[0] GitHub — anthropics/claude-code
     https://github.com/anthropics/claude-code
 [1] Stack Overflow — python marionette connect
     https://stackoverflow.com/questions/...
 [2] Zen Browser Docs
     https://docs.zen-browser.app/
```

Active tab marked with `>`. Title + URL, nothing else.

## MCP tool surface

The MCP server exposes each CLI command as a tool. The mapping is direct — same names, same parameters, same output.

### Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `tabs` | `mode?` | List open tabs |
| `read` | `tab?, mode?` | Extract page content |
| `screenshot` | `tab?, saveTo?, mode?` | Take screenshot |
| `find` | `text, mode?` | Find elements by visible text |
| `url` | `mode?` | Current URL + title |
| `console` | `mode?` | Console messages |
| `network` | `filter?, mode?` | Network requests |
| `go` | `url, mode?` | Navigate to URL |
| `search` | `query, mode?` | Web search |
| `click` | `description, mode?` | Click by text/label |
| `fill` | `description, value, mode?` | Fill input |
| `select` | `description, value, mode?` | Select dropdown |
| `scroll` | `to?, y?, mode?` | Scroll |
| `back` | `mode?` | Navigate back |
| `forward` | `mode?` | Navigate forward |
| `key` | `name, mode?` | Press key |
| `tab` | `target, mode?` | Switch tab |
| `new_tab` | `url?, mode?` | Open new tab |
| `close_tab` | `index?, mode?` | Close tab |
| `js` | `expression, mode?` | Evaluate JS |
| `html` | `selector?, mode?` | Extract HTML |
| `css_click` | `selector, mode?` | Click by CSS |
| `css_fill` | `selector, value, mode?` | Fill by CSS |

`mode` defaults to `"headless"`. Set to `"zen"` to operate on the user's browser.

### MCP server implementation

Python, using the `mcp` SDK. Stdio transport (Claude Code connects via stdin/stdout).

The MCP server is a thin wrapper: each tool handler calls the same core functions the CLI uses. No separate logic.

```
foxpilot/
  __init__.py
  core.py          # browser connection, element finding, page reading
  cli.py           # typer CLI — calls core
  mcp_server.py    # MCP server — calls core
  search.py        # web search extraction
  readability.py   # content extraction heuristic
```

### MCP configuration (Claude Code)

```json
{
  "mcpServers": {
    "browser": {
      "command": "foxpilot",
      "args": ["mcp"],
      "type": "stdio"
    }
  }
}
```

The MCP server starts via `foxpilot mcp` subcommand.

## Architecture

```
                    CLI user                     Claude Code (MCP client)
                       |                                |
                  foxpilot <cmd>                   MCP stdio
                       |                                |
                   cli.py                         mcp_server.py
                       \                              /
                        \                            /
                         +--- core.py (shared) -----+
                              |             |
                        zen_connect()   headless_launch()
                              |             |
                         geckodriver    geckodriver
                              |             |
                        user's Zen     ephemeral Firefox
                        (Marionette)   (Marionette)
```

### core.py — the engine

Two connection factories:

- `zen_connect()` — geckodriver `--connect-existing --marionette-port 2828`. Returns a Selenium WebDriver instance connected to the running Zen browser. Validates connection, fails fast with clear error if Zen isn't running or lacks `--marionette`.

- `headless_launch()` — starts Firefox with `--headless --marionette`, connects via geckodriver, returns WebDriver instance. Caller is responsible for teardown.

Context manager pattern:

```python
with browser(mode="zen") as driver:
    driver.get("https://example.com")
    text = read_page(driver)
```

In headless mode, `__exit__` calls `driver.quit()` (kills Firefox). In zen mode, `__exit__` calls `driver.quit()` (closes geckodriver session, leaves Zen running).

### Element finding

Port `af zen`'s `_find_element_by_text` approach — XPath search across:
1. `text()` content
2. `@aria-label`
3. `@placeholder`
4. `@title`
5. `@alt`
6. `@value` (for buttons)

Priority: interactive elements (button, a, input, select, textarea) ranked above generic elements. Visible-only filter. Exact match preferred over contains.

### Content extraction (readability.py)

For `read` command. Heuristic to find the main content block:

1. Look for `<article>`, `<main>`, `[role="main"]`
2. If not found, score `<div>`/`<section>` blocks by text density (text length / child count)
3. Pick the highest-scoring block
4. Strip scripts, styles, nav, footer, aside
5. Extract text, preserving paragraph breaks

Fallback: `document.body.innerText` truncated.

### Search (search.py)

DuckDuckGo HTML search. No API key needed.

1. Navigate to `https://html.duckduckgo.com/html/?q={query}`
2. Parse results: title, URL, snippet from `.result__title`, `.result__url`, `.result__snippet`
3. Return structured list

In zen mode: optionally use the browser's address bar (navigate to search URL in a new tab), then extract results from whatever search engine the user has configured.

## Tech stack

- **Language**: Python 3.11+
- **CLI**: typer
- **MCP**: `mcp` Python SDK (stdio transport)
- **Browser automation**: selenium (WebDriver/Marionette)
- **Browser**: Firefox / Zen (Marionette protocol)
- **Dependencies**: selenium, typer, mcp, geckodriver (system package)
- **Packaging**: single `pyproject.toml`, installable via `uv pip install` or `pipx`

### Why Selenium over raw Marionette?

- geckodriver handles the Marionette wire protocol, session management, and `--connect-existing`
- Selenium's WebDriver API is stable and well-known
- `af zen` already proves the pattern works
- Raw Marionette would mean reimplementing what geckodriver gives us for free

### Why not Playwright?

- Playwright can't connect to an existing Firefox instance (it manages its own browser lifecycle)
- We need `--connect-existing` for zen mode
- Playwright's Firefox support uses a patched Firefox, not stock Firefox/Zen

### Why not CDP?

- Firefox/Zen CDP support is minimal and deprecated in favor of BiDi
- Marionette is Firefox's native protocol
- geckodriver is the official bridge

## Zen browser setup

Zen must run with `--marionette` for foxpilot to connect. Two options:

1. **Desktop entry** — patch `/usr/share/applications/zen.desktop`:
   ```
   Exec=/opt/zen-browser-bin/zen-bin --marionette %u
   ```

2. **Wrapper script** — `~/.local/bin/zen`:
   ```bash
   #!/bin/bash
   exec /opt/zen-browser-bin/zen-bin --marionette "$@"
   ```

foxpilot does NOT launch Zen. It connects to whatever's already running. If Zen isn't running with `--marionette`, zen mode fails with a clear error message telling the user how to fix it.

## What this replaces

Once foxpilot is working:

- `af browser` — fully replaced (foxpilot covers all its capabilities with Firefox-native protocols)
- `af zen` — fully replaced (foxpilot is the extracted, improved version)
- `firefox-devtools` MCP — replaced for this agent system (foxpilot's MCP is the primary browser tool)

The browser-control skill in agentfiles gets updated to point at foxpilot instead of the three separate tools.

## Out of scope (for now)

- **File downloads** — use Playwright or curl for this
- **Network interception/mocking** — use Playwright
- **Multiple headless instances** — one at a time is fine
- **Browser profiles for headless** — ephemeral, always clean
- **Cookie/session export** — not needed yet
- **Proxy support** — not needed yet

## Success criteria

1. `foxpilot search "python mcp server"` returns structured search results from headless Firefox
2. `foxpilot --zen tabs` lists my actual Zen browser tabs
3. `foxpilot --zen read` extracts main content from the active Zen tab
4. `foxpilot --zen click "Sign in"` clicks the right button and reports what happened
5. Claude Code can use the MCP server to browse the web and interact with my Zen browser
6. Total dependencies: selenium, typer, mcp SDK, geckodriver. Nothing else.
