"""cf screenshot — capture a browser screenshot Claude can read visually.

Requires playwright (installed automatically on first run):
    playwright install chromium

The screenshot is saved as a PNG. Use the Read tool on the output path
to view it — Claude sees the actual rendered layout, spacing, and colours.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Capture a browser screenshot for visual verification.")


def _ensure_playwright() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        pass
    typer.echo("[screenshot] installing playwright...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "playwright"],
            check=True, capture_output=True,
        )
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        typer.echo(f"[screenshot] ERROR: failed to install playwright: {e}", err=True)
        typer.echo("  Run manually: pip install playwright && playwright install chromium", err=True)
        return False


@app.callback(invoke_without_command=True)
def main(
    url: str = typer.Argument("http://localhost:3000",
        help="URL to screenshot"),
    out: str = typer.Option("/tmp/ui-screenshot.png", "--out", "-o",
        help="Output PNG path"),
    width: int = typer.Option(1280, "--width", "-W",
        help="Viewport width in px"),
    height: int = typer.Option(800, "--height", "-H",
        help="Viewport height in px"),
    full_page: bool = typer.Option(False, "--full-page",
        help="Capture full scrollable page"),
    wait: int = typer.Option(0, "--wait",
        help="Extra wait in ms after page load (for animations)"),
    mobile: bool = typer.Option(False, "--mobile",
        help="Use iPhone 12 dimensions (390x844)"),
):
    """Screenshot a URL and save as PNG. Claude reads it with the Read tool."""
    if mobile:
        width, height = 390, 844

    if not _ensure_playwright():
        raise typer.Exit(1)

    from playwright.sync_api import sync_playwright

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    typer.echo(f"[screenshot] loading {url} ...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(url, wait_until="networkidle", timeout=30_000)
            if wait > 0:
                typer.echo(f"[screenshot] waiting {wait}ms...")
                time.sleep(wait / 1000)
            page.screenshot(path=str(out_path), full_page=full_page)
            browser.close()
    except Exception as e:
        typer.echo(f"[screenshot] ERROR: {e}", err=True)
        if "ERR_CONNECTION_REFUSED" in str(e):
            typer.echo(f"  Is the server running at {url}?", err=True)
        raise typer.Exit(1)

    size_kb = out_path.stat().st_size // 1024
    typer.echo(f"[screenshot] saved : {out_path} ({size_kb} KB)")
    typer.echo(f"[screenshot] read  : use Read tool on {out_path}")
