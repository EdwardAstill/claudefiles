# af browser

Persistent browser automation via Chrome DevTools Protocol (CDP). No Playwright dependency. Supports Chrome, Chromium, and Firefox.

**Source:** `tools/python/src/af/browser.py`

## Usage

```bash
# Lifecycle
af browser start [--headed] [--firefox] [--port 9222] [--url <URL>]
af browser stop
af browser status

# Navigation
af browser go <URL>

# Interaction
af browser click <SELECTOR>
af browser fill <SELECTOR> <TEXT>
af browser wait <SELECTOR>
af browser type <TEXT>

# Reading
af browser read [SELECTOR]          # extract text content
af browser html [SELECTOR]          # extract HTML
af browser snap [SELECTOR]          # take screenshot
af browser console                  # dump console messages
af browser network                  # list network requests
af browser a11y                     # dump accessibility tree

# Tabs
af browser tabs                     # list open tabs
af browser tab <INDEX>              # switch to tab

# JavaScript
af browser eval <EXPRESSION>        # evaluate JS expression
```

## Start Options

| Flag | Description |
|------|-------------|
| `--headless/--headed` | Run headless (default) or headed |
| `--port <port>`, `-p` | CDP port (default: 9222) |
| `--firefox`, `-f` | Prefer Firefox over Chrome |
| `--url <url>` | Initial URL (default: about:blank) |

## Browser Discovery

Searches in order: system Chrome → Puppeteer Chrome → auto-install → Firefox.

Session state stored at `~/.claude/data/browser-session.json`.

See also: [browser reference](../reference/browser.md) for multi-step automation patterns.
