"""af zen — high-level Zen browser automation with per-action feedback.

Connects to a running Zen browser via Marionette (--connect-existing).
Every command returns what it did + what's visible now.

Requires: zen-browser running with --marionette --remote-debugging-port=9222
"""

import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Zen browser automation with feedback.")

MARIONETTE_PORT = 2828
SNAP_DIR = Path("/tmp")


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def _get_driver():
    """Connect to running Zen via geckodriver --connect-existing."""
    try:
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.service import Service
    except ImportError:
        typer.echo("selenium not installed. Run: uv pip install selenium", err=True)
        raise typer.Exit(1)

    opts = Options()
    # geckodriver needs --connect-existing and --marionette-port as SERVICE args
    service = Service(
        service_args=[
            "--connect-existing",
            "--marionette-port", str(MARIONETTE_PORT),
        ],
    )

    try:
        driver = webdriver.Firefox(options=opts, service=service)
    except Exception as e:
        typer.echo(f"✗ can't connect to Zen on port {MARIONETTE_PORT}", err=True)
        typer.echo(f"  is Zen running with --marionette?", err=True)
        typer.echo(f"  error: {e}", err=True)
        raise typer.Exit(1)

    return driver


def _close(driver):
    """Quit the WebDriver session without closing the browser."""
    try:
        driver.quit()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Element finding — by visible text, placeholder, aria-label, role
# ---------------------------------------------------------------------------

def _find_element_by_text(driver, text: str, role: Optional[str] = None, tag: Optional[str] = None):
    """Find an element by visible text, placeholder, or aria-label."""
    from selenium.webdriver.common.by import By

    # Build candidate XPaths in priority order
    xpaths = []

    if role:
        # Role-specific searches
        xpaths.append(f"//*[@role='{role}'][contains(., '{text}')]")
        xpaths.append(f"//*[@role='{role}'][@aria-label[contains(., '{text}')]]")
        xpaths.append(f"//*[@role='{role}'][@placeholder[contains(., '{text}')]]")
    else:
        # Inputs by placeholder or label
        xpaths.append(f"//input[@placeholder[contains(., '{text}')]]")
        xpaths.append(f"//textarea[@placeholder[contains(., '{text}')]]")
        xpaths.append(f"//*[@aria-label[contains(., '{text}')]]")
        # Buttons/links by text
        xpaths.append(f"//button[contains(., '{text}')]")
        xpaths.append(f"//a[contains(., '{text}')]")
        # Any element by text content
        xpaths.append(f"//*[contains(text(), '{text}')]")

    if tag:
        xpaths.insert(0, f"//{tag}[contains(., '{text}')]")

    for xpath in xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            # Filter to visible elements
            visible = [e for e in elements if e.is_displayed()]
            if visible:
                return visible[0]
        except Exception:
            continue

    return None


def _describe_element(el) -> str:
    """Short description of an element."""
    tag = el.tag_name
    text = (el.text or "")[:60]
    role = el.get_attribute("role") or ""
    label = el.get_attribute("aria-label") or ""
    placeholder = el.get_attribute("placeholder") or ""

    parts = [f"<{tag}>"]
    if role:
        parts.append(f'role="{role}"')
    if label:
        parts.append(f'label="{label}"')
    elif placeholder:
        parts.append(f'placeholder="{placeholder}"')
    elif text:
        parts.append(f'"{text}"')

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Page reading — extract visible text summary
# ---------------------------------------------------------------------------

def _read_page(driver, selector: Optional[str] = None, max_chars: int = 2000) -> str:
    """Extract visible text from the page or a scoped element."""
    from selenium.webdriver.common.by import By

    if selector:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            text = el.text
        except Exception:
            return f"(selector '{selector}' not found)"
    else:
        text = driver.find_element(By.TAG_NAME, "body").text

    if not text:
        return "(no visible text)"

    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    result = "\n".join(lines)

    if len(result) > max_chars:
        result = result[:max_chars] + "\n... [truncated]"

    return result


def _feedback(driver, action_msg: str, selector: Optional[str] = None):
    """Print action result + current page state."""
    typer.echo(action_msg)
    typer.echo(f"→ url: {driver.current_url}")
    typer.echo(f"→ title: {driver.title}")

    text = _read_page(driver, selector, max_chars=800)
    if text and text != "(no visible text)":
        typer.echo(f"→ visible:")
        for line in text.splitlines()[:15]:
            typer.echo(f"  {line}")
        line_count = len(text.splitlines())
        if line_count > 15:
            typer.echo(f"  ... (+{line_count - 15} more lines)")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command()
def tabs():
    """List all open tabs with titles and URLs."""
    driver = _get_driver()
    try:
        current = driver.current_window_handle
        handles = driver.window_handles
        for i, handle in enumerate(handles):
            driver.switch_to.window(handle)
            marker = ">" if handle == current else " "
            typer.echo(f"{marker}[{i}] {driver.title}")
            typer.echo(f"     {driver.current_url}")
        # Switch back to original
        driver.switch_to.window(current)
    finally:
        _close(driver)


@app.command()
def tab(
    target: str = typer.Argument(..., help="Tab index (number) or URL/title substring."),
):
    """Switch to a tab by index or substring match."""
    driver = _get_driver()
    try:
        handles = driver.window_handles

        # Try as index first
        try:
            idx = int(target)
            if 0 <= idx < len(handles):
                driver.switch_to.window(handles[idx])
                _feedback(driver, f"✓ switched to tab [{idx}]")
                return
        except ValueError:
            pass

        # Search by title/URL substring
        target_lower = target.lower()
        for i, handle in enumerate(handles):
            driver.switch_to.window(handle)
            if target_lower in driver.title.lower() or target_lower in driver.current_url.lower():
                _feedback(driver, f"✓ switched to tab [{i}] (matched '{target}')")
                return

        typer.echo(f"✗ no tab matching '{target}'")
    finally:
        _close(driver)


@app.command()
def go(
    url: str = typer.Argument(..., help="URL to navigate to."),
):
    """Navigate current tab to URL."""
    driver = _get_driver()
    try:
        driver.get(url)
        time.sleep(1)  # Let page settle
        _feedback(driver, f"✓ navigated to {url}")
    finally:
        _close(driver)


@app.command()
def look(
    selector: Optional[str] = typer.Argument(None, help="CSS selector to scope to."),
    full: bool = typer.Option(False, "--full", help="Show all text (no truncation)."),
):
    """Read visible text from current page."""
    driver = _get_driver()
    try:
        max_chars = 50000 if full else 2000
        text = _read_page(driver, selector, max_chars)
        typer.echo(f"[{driver.title}] {driver.current_url}")
        typer.echo("-" * 60)
        typer.echo(text)
    finally:
        _close(driver)


@app.command()
def click(
    text: str = typer.Argument(..., help="Visible text, label, or placeholder to find."),
    role: Optional[str] = typer.Option(None, "--role", "-r", help="Filter by ARIA role."),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by HTML tag."),
):
    """Click an element by visible text."""
    driver = _get_driver()
    try:
        el = _find_element_by_text(driver, text, role=role, tag=tag)
        if not el:
            typer.echo(f"✗ no element found matching '{text}'")
            raise typer.Exit(1)

        desc = _describe_element(el)
        el.click()
        time.sleep(1)
        _feedback(driver, f"✓ clicked {desc}")
    finally:
        _close(driver)


@app.command()
def fill(
    target: str = typer.Argument(..., help="Input label, placeholder, or text to find."),
    value: str = typer.Argument(..., help="Text to type."),
    submit: bool = typer.Option(False, "--submit", "-s", help="Press Enter after filling."),
):
    """Fill a text input found by label/placeholder."""
    driver = _get_driver()
    try:
        from selenium.webdriver.common.keys import Keys

        el = _find_element_by_text(driver, target)
        if not el:
            # Fallback: try finding any visible input/textarea
            from selenium.webdriver.common.by import By
            inputs = driver.find_elements(By.CSS_SELECTOR, "input:not([type=hidden]), textarea")
            visible = [e for e in inputs if e.is_displayed()]
            if visible:
                el = visible[0]
            else:
                typer.echo(f"✗ no input found matching '{target}'")
                raise typer.Exit(1)

        desc = _describe_element(el)
        el.clear()
        el.send_keys(value)

        if submit:
            el.send_keys(Keys.RETURN)
            time.sleep(1)
            _feedback(driver, f"✓ filled {desc} with '{value}' + submitted")
        else:
            _feedback(driver, f"✓ filled {desc} with '{value}'")
    finally:
        _close(driver)


@app.command()
def submit():
    """Press Enter on the currently focused element."""
    driver = _get_driver()
    try:
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.by import By

        active = driver.switch_to.active_element
        if active:
            active.send_keys(Keys.RETURN)
            time.sleep(1)
            _feedback(driver, "✓ submitted (pressed Enter)")
        else:
            typer.echo("✗ no focused element")
    finally:
        _close(driver)


@app.command()
def back():
    """Navigate back."""
    driver = _get_driver()
    try:
        driver.back()
        time.sleep(1)
        _feedback(driver, "✓ navigated back")
    finally:
        _close(driver)


@app.command()
def forward():
    """Navigate forward."""
    driver = _get_driver()
    try:
        driver.forward()
        time.sleep(1)
        _feedback(driver, "✓ navigated forward")
    finally:
        _close(driver)


@app.command()
def scroll(
    amount: int = typer.Option(600, "--y", help="Pixels to scroll (negative = up)."),
    selector: Optional[str] = typer.Option(None, "--to", help="CSS selector to scroll into view."),
):
    """Scroll the page and report new content."""
    driver = _get_driver()
    try:
        if selector:
            from selenium.webdriver.common.by import By
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth'});", el)
                time.sleep(0.5)
                _feedback(driver, f"✓ scrolled to '{selector}'")
            except Exception:
                typer.echo(f"✗ selector '{selector}' not found")
        else:
            driver.execute_script(f"window.scrollBy(0, {amount});")
            time.sleep(0.5)
            pos = driver.execute_script("return window.scrollY;")
            _feedback(driver, f"✓ scrolled {amount}px (position: {pos}px)")
    finally:
        _close(driver)


@app.command()
def snap(
    path: str = typer.Argument("/tmp/zen-snap.png", help="Output path for screenshot."),
    selector: Optional[str] = typer.Option(None, "--el", help="Screenshot a specific element."),
):
    """Take a screenshot and save to disk."""
    driver = _get_driver()
    try:
        out = Path(path)
        if selector:
            from selenium.webdriver.common.by import By
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                el.screenshot(str(out))
            except Exception:
                typer.echo(f"✗ selector '{selector}' not found")
                raise typer.Exit(1)
        else:
            driver.save_screenshot(str(out))

        size_kb = out.stat().st_size / 1024
        typer.echo(f"✓ screenshot saved: {out} ({size_kb:.0f}KB)")
        typer.echo(f"  title: {driver.title}")
        typer.echo(f"  url: {driver.current_url}")
    finally:
        _close(driver)


@app.command()
def url():
    """Show current page URL and title."""
    driver = _get_driver()
    try:
        typer.echo(f"{driver.title}")
        typer.echo(f"{driver.current_url}")
    finally:
        _close(driver)


@app.command()
def js(
    expr: str = typer.Argument(..., help="JavaScript expression to evaluate."),
):
    """Evaluate JavaScript in the page context."""
    driver = _get_driver()
    try:
        result = driver.execute_script(f"return {expr};")
        typer.echo(f"✓ {result}")
    finally:
        _close(driver)


@app.command()
def find(
    text: str = typer.Argument(..., help="Text to search for in visible elements."),
    role: Optional[str] = typer.Option(None, "--role", "-r", help="Filter by ARIA role."),
):
    """Find elements matching text and list them."""
    driver = _get_driver()
    try:
        from selenium.webdriver.common.by import By

        # Search broadly
        xpaths = [
            f"//*[contains(text(), '{text}')]",
            f"//*[@aria-label[contains(., '{text}')]]",
            f"//*[@placeholder[contains(., '{text}')]]",
            f"//*[@title[contains(., '{text}')]]",
        ]

        seen = set()
        results = []
        for xpath in xpaths:
            try:
                for el in driver.find_elements(By.XPATH, xpath):
                    el_id = id(el)
                    if el_id in seen:
                        continue
                    seen.add(el_id)
                    if el.is_displayed():
                        results.append(el)
            except Exception:
                continue

        if not results:
            typer.echo(f"✗ no visible elements matching '{text}'")
        else:
            typer.echo(f"✓ {len(results)} element(s) matching '{text}':")
            for i, el in enumerate(results[:20]):
                desc = _describe_element(el)
                typer.echo(f"  [{i}] {desc}")
    finally:
        _close(driver)
