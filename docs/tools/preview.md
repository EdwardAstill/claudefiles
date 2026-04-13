# af preview

Serve HTML design mockups for visual iteration with auto-refresh.

**Source:** `tools/python/src/af/preview.py`

## Usage

```bash
af preview [DIRECTORY]                  # default: /tmp/ui-preview
af preview --port 7823 /tmp/ui-preview/
af preview --no-open /tmp/ui-preview/   # don't auto-open browser
```

## Arguments

| Argument | Description |
|----------|-------------|
| `directory` | Watch directory (default: `/tmp/ui-preview`) |

## Options

| Flag | Description |
|------|-------------|
| `--port <port>` | Server port (0 = random available) |
| `--no-open` | Don't auto-open browser |

## How It Works

1. Claude writes `.html` files to the watched directory (one per design option)
2. The browser auto-refreshes via SSE — no manual reload needed
3. User views options, then types their choice in the terminal

Files can be full HTML documents or bare fragments. If the file doesn't start with `<!DOCTYPE` or `<html`, the server wraps it in a Tailwind CDN shell automatically.

User choices are recorded to `events.jsonl` in the watch directory.
