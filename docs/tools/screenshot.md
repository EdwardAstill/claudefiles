# af screenshot

Capture a browser screenshot for visual verification.

**Source:** `tools/python/src/af/screenshot.py`

## Usage

```bash
af screenshot [URL]                                     # default: http://localhost:3000
af screenshot http://localhost:3000 --out /tmp/shot.png
af screenshot http://localhost:3000 --mobile            # 390x844 (iPhone 12)
af screenshot http://localhost:3000 --full-page          # full scrollable height
af screenshot http://localhost:3000 --wait 500           # extra ms after load
af screenshot http://localhost:3000 --width 1440 --height 900
```

## Arguments

| Argument | Description |
|----------|-------------|
| `url` | URL to screenshot (default: `http://localhost:3000`) |

## Options

| Flag | Description |
|------|-------------|
| `--out <path>`, `-o` | Output PNG path (default: `/tmp/ui-screenshot.png`) |
| `--width <px>`, `-W` | Viewport width (default: 1280) |
| `--height <px>`, `-H` | Viewport height (default: 800) |
| `--full-page` | Capture full scrollable page |
| `--wait <ms>` | Extra wait after load (milliseconds) |
| `--mobile` | iPhone 12 dimensions (390x844) |

## Dependencies

Uses Playwright with headless Firefox. Auto-installs on first run (`playwright install firefox`).
