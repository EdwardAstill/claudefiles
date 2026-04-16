"""af browser — lightweight CDP client for browser automation.

Talks Chrome DevTools Protocol directly over WebSocket. No Playwright dependency.
Browser stays running between invocations via session persistence.

Supports Chrome, Chromium, and Firefox (via --remote-debugging-port).
"""

import base64
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Browser automation via Chrome DevTools Protocol.")

SESSION_FILE = Path.home() / ".claude" / "data" / "browser-session.json"

_CHROME_CANDIDATES = [
    "google-chrome-stable",
    "google-chrome",
    "chromium-browser",
    "chromium",
    "chrome",
]

_FIREFOX_CANDIDATES = [
    "firefox",
    "firefox-esr",
]


# ---------------------------------------------------------------------------
# Chrome / Firefox discovery
# ---------------------------------------------------------------------------

def _find_puppeteer_chrome() -> Optional[str]:
    """Find Chrome installed by Puppeteer in ~/.cache/puppeteer/."""
    cache_dir = Path.home() / ".cache" / "puppeteer" / "chrome"
    if not cache_dir.exists():
        return None
    # Find newest version
    versions = sorted(cache_dir.iterdir(), reverse=True)
    for v in versions:
        candidates = list(v.glob("**/chrome"))
        if candidates:
            chrome = candidates[0]
            if chrome.is_file() and os.access(chrome, os.X_OK):
                return str(chrome)
    return None


def _install_chrome() -> Optional[str]:
    """Install Chrome via npx puppeteer if not found."""
    typer.echo("[browser] no Chrome/Chromium found — installing via puppeteer...", err=True)
    try:
        result = subprocess.run(
            ["npx", "puppeteer", "browsers", "install", "chrome@stable"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            # Parse the output for the chrome path
            for line in result.stdout.splitlines():
                if "/chrome" in line and "chrome-linux" in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith("/") and "chrome" in part:
                            if Path(part).is_file():
                                return part
            # Fallback: search the cache dir
            return _find_puppeteer_chrome()
        typer.echo(f"[browser] install failed: {result.stderr[:200]}", err=True)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        typer.echo(f"[browser] install failed: {e}", err=True)
    return None


def _find_browser(prefer_firefox: bool = False) -> tuple[str, str]:
    """Find a browser binary. Returns (path, kind) where kind is 'chrome' or 'firefox'.

    Priority (default): system Chrome → Puppeteer Chrome → auto-install Chrome → Firefox.
    With --firefox: Firefox first, then Chrome fallbacks.
    """
    if prefer_firefox:
        for name in _FIREFOX_CANDIDATES:
            path = shutil.which(name)
            if path:
                return path, "firefox"

    # System Chrome/Chromium
    for name in _CHROME_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path, "chrome"

    # macOS app bundles
    mac_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if Path(mac_chrome).exists():
        return mac_chrome, "chrome"

    # Puppeteer-managed Chrome
    pup_chrome = _find_puppeteer_chrome()
    if pup_chrome:
        return pup_chrome, "chrome"

    # Auto-install Chrome via puppeteer
    if shutil.which("npx"):
        installed = _install_chrome()
        if installed:
            return installed, "chrome"

    # Last resort: Firefox (even without --firefox flag)
    if not prefer_firefox:
        for name in _FIREFOX_CANDIDATES:
            path = shutil.which(name)
            if path:
                typer.echo("[browser] WARNING: only Firefox found — BiDi support is limited", err=True)
                typer.echo("  For full CDP support: npx puppeteer browsers install chrome@stable", err=True)
                return path, "firefox"

    typer.echo("[browser] ERROR: no Chrome or Chromium found", err=True)
    typer.echo("  Install: npx puppeteer browsers install chrome@stable", err=True)
    typer.echo("  Or: pacman -S chromium / apt install chromium-browser", err=True)
    raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def _load_session() -> Optional[dict]:
    if not SESSION_FILE.exists():
        return None
    try:
        data = json.loads(SESSION_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    pid = data.get("pid")
    if pid:
        try:
            os.kill(pid, 0)
        except OSError:
            _clear_session()
            return None
    return data


def _save_session(data: dict) -> None:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data, indent=2) + "\n")


def _clear_session() -> None:
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def _require_session() -> dict:
    session = _load_session()
    if not session:
        typer.echo("[browser] ERROR: no browser running", err=True)
        typer.echo("  Start one with: af browser start", err=True)
        raise typer.Exit(1)
    return session


# ---------------------------------------------------------------------------
# CDP HTTP helpers (stdlib only)
# ---------------------------------------------------------------------------

def _get_targets(port: int) -> list[dict]:
    url = f"http://127.0.0.1:{port}/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError):
        return []


def _get_version(port: int) -> Optional[dict]:
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError):
        return None


def _page_targets(port: int) -> list[dict]:
    targets = _get_targets(port)
    return [t for t in targets if t.get("type") == "page"
            and not t.get("url", "").startswith(("chrome://", "chrome-extension://",
                                                  "devtools://"))]


# ---------------------------------------------------------------------------
# CDP WebSocket client
# ---------------------------------------------------------------------------

class CDPClient:
    def __init__(self, ws_url: str):
        import websocket
        self._ws = websocket.create_connection(ws_url, timeout=30)
        self._id = 0
        self._events: list[dict] = []

    def send(self, method: str, params: Optional[dict] = None, timeout: float = 30) -> dict:
        self._id += 1
        msg_id = self._id
        msg = {"id": msg_id, "method": method}
        if params:
            msg["params"] = params
        self._ws.send(json.dumps(msg))
        return self._recv_until(msg_id, timeout)

    def _recv_until(self, msg_id: int, timeout: float) -> dict:
        deadline = time.time() + timeout
        self._ws.settimeout(timeout)
        while time.time() < deadline:
            try:
                raw = self._ws.recv()
            except Exception:
                break
            if not raw:
                break
            data = json.loads(raw)
            if data.get("id") == msg_id:
                return data
            # Buffer events
            if "method" in data:
                self._events.append(data)
        return {"error": {"message": "timeout waiting for CDP response"}}

    def collect_events(self, seconds: float = 2.0) -> list[dict]:
        """Collect all incoming events for a duration."""
        collected = list(self._events)
        self._events.clear()
        deadline = time.time() + seconds
        self._ws.settimeout(0.2)
        while time.time() < deadline:
            try:
                raw = self._ws.recv()
                if raw:
                    data = json.loads(raw)
                    if "method" in data:
                        collected.append(data)
            except Exception:
                pass
        return collected

    def close(self):
        try:
            self._ws.close()
        except Exception:
            pass


def _connect(session: Optional[dict] = None) -> CDPClient:
    """Connect to the active page target. Returns a CDPClient."""
    if session is None:
        session = _require_session()
    port = session["port"]

    # Find the active target
    active_id = session.get("active_target")
    pages = _page_targets(port)
    if not pages:
        typer.echo("[browser] ERROR: no page targets found", err=True)
        raise typer.Exit(1)

    target = None
    if active_id:
        target = next((p for p in pages if p["id"] == active_id), None)
    if not target:
        target = pages[0]
        # Update session with actual target
        session["active_target"] = target["id"]
        _save_session(session)

    ws_url = target.get("webSocketDebuggerUrl")
    if not ws_url:
        typer.echo("[browser] ERROR: target has no WebSocket URL", err=True)
        raise typer.Exit(1)

    try:
        return CDPClient(ws_url)
    except Exception as e:
        typer.echo(f"[browser] ERROR: WebSocket connection failed: {e}", err=True)
        typer.echo("  Try: af browser stop && af browser start", err=True)
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# JS helpers for Runtime.evaluate
# ---------------------------------------------------------------------------

def _eval_js(cdp: CDPClient, expression: str, return_by_value: bool = True) -> dict:
    result = cdp.send("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": return_by_value,
        "awaitPromise": True,
    })
    if "error" in result:
        return result
    r = result.get("result", {})
    if r.get("exceptionDetails"):
        exc = r["exceptionDetails"]
        text = exc.get("text", "")
        if exc.get("exception", {}).get("description"):
            text = exc["exception"]["description"]
        return {"error": {"message": text}}
    return r.get("result", {})


# ---------------------------------------------------------------------------
# Commands: start / stop / status
# ---------------------------------------------------------------------------

@app.command()
def start(
    headless: bool = typer.Option(True, "--headless/--headed", help="Run headless (default) or headed"),
    port: int = typer.Option(9222, "--port", "-p", help="CDP debugging port"),
    firefox: bool = typer.Option(False, "--firefox", "-f", help="Prefer Firefox over Chrome"),
    url: str = typer.Option("about:blank", "--url", help="Initial URL to open"),
):
    """Launch a browser with CDP enabled."""
    existing = _load_session()
    if existing:
        typer.echo(f"[browser] already running (pid {existing['pid']}, port {existing['port']})", err=True)
        typer.echo("  Stop first: af browser stop", err=True)
        raise typer.Exit(1)

    # Check if port is already in use (external browser)
    targets = _get_targets(port)
    if targets:
        version = _get_version(port)
        typer.echo(f"[browser] connecting to existing browser on port {port}", err=True)
        pages = _page_targets(port)
        active_id = pages[0]["id"] if pages else None
        _save_session({
            "port": port,
            "pid": None,
            "headless": False,
            "browser_kind": "external",
            "active_target": active_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "browser": version.get("Browser", "unknown") if version else "unknown",
        })
        typer.echo(f"[browser] connected — {len(pages)} tab(s)")
        return

    browser_path, browser_kind = _find_browser(prefer_firefox=firefox)
    typer.echo(f"[browser] launching {browser_kind}: {browser_path}", err=True)

    if browser_kind == "chrome":
        args = [
            browser_path,
            f"--remote-debugging-port={port}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-timer-throttling",
            "--disable-extensions",
            "--disable-sync",
            "--no-sandbox",
            "--remote-allow-origins=*",
        ]
        if headless:
            args.append("--headless=new")
        args.append(url)
    else:
        # Firefox
        args = [
            browser_path,
            "--remote-debugging-port", str(port),
            "--no-remote",
        ]
        if headless:
            args.append("--headless")
        if url != "about:blank":
            args.append(url)

    proc = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Wait for CDP to become available
    typer.echo("[browser] waiting for CDP...", err=True)
    deadline = time.time() + 10
    pages = []
    while time.time() < deadline:
        pages = _page_targets(port)
        if pages:
            break
        # Check process hasn't crashed
        if proc.poll() is not None:
            typer.echo(f"[browser] ERROR: browser exited with code {proc.returncode}", err=True)
            raise typer.Exit(1)
        time.sleep(0.3)

    if not pages:
        typer.echo("[browser] ERROR: CDP did not become available within 10s", err=True)
        proc.terminate()
        raise typer.Exit(1)

    version = _get_version(port)
    _save_session({
        "port": port,
        "pid": proc.pid,
        "headless": headless,
        "browser_kind": browser_kind,
        "active_target": pages[0]["id"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "browser": version.get("Browser", "unknown") if version else browser_kind,
    })

    typer.echo(f"[browser] ready — pid {proc.pid}, port {port}, {len(pages)} tab(s)")


@app.command()
def stop():
    """Stop the browser and clear the session."""
    session = _load_session()
    if not session:
        typer.echo("[browser] no browser running")
        return

    pid = session.get("pid")
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            typer.echo(f"[browser] stopped (pid {pid})", err=True)
        except OSError:
            typer.echo("[browser] process already gone", err=True)
    else:
        typer.echo("[browser] detached from external browser", err=True)

    _clear_session()


@app.command()
def status():
    """Show browser session status."""
    session = _load_session()
    if not session:
        typer.echo("[browser] no browser running")
        typer.echo("  Start one with: af browser start")
        return

    port = session["port"]
    pages = _page_targets(port)
    version = _get_version(port)

    typer.echo(f"Browser:  {session.get('browser', 'unknown')}")
    typer.echo(f"PID:      {session.get('pid', 'external')}")
    typer.echo(f"Port:     {port}")
    typer.echo(f"Headless: {session.get('headless', '?')}")
    typer.echo(f"Started:  {session.get('started_at', '?')}")
    typer.echo(f"Tabs:     {len(pages)}")
    if pages:
        active_id = session.get("active_target")
        for i, p in enumerate(pages):
            marker = " *" if p["id"] == active_id else ""
            typer.echo(f"  [{i}] {p.get('title', '(untitled)')} — {p.get('url', '')}{marker}")


# ---------------------------------------------------------------------------
# Commands: navigation
# ---------------------------------------------------------------------------

@app.command()
def go(
    url: str = typer.Argument(..., help="URL to navigate to"),
):
    """Navigate to a URL."""
    session = _require_session()
    cdp = _connect(session)
    try:
        result = cdp.send("Page.enable")
        result = cdp.send("Page.navigate", {"url": url})
        if result.get("error"):
            typer.echo(f"[browser] ERROR: {result['error'].get('message', result['error'])}", err=True)
            raise typer.Exit(1)

        # Wait for load
        time.sleep(0.5)
        title_result = _eval_js(cdp, "document.title")
        title = title_result.get("value", "")
        url_result = _eval_js(cdp, "window.location.href")
        final_url = url_result.get("value", url)

        typer.echo(f"[browser] navigated: {final_url}", err=True)
        if title:
            typer.echo(f"[browser] title: {title}", err=True)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: eval
# ---------------------------------------------------------------------------

@app.command("eval")
def eval_js(
    expression: str = typer.Argument(..., help="JavaScript expression to evaluate"),
):
    """Evaluate JavaScript and print the result."""
    cdp = _connect()
    try:
        result = _eval_js(cdp, expression)
        if isinstance(result, dict) and "error" in result:
            typer.echo(f"[browser] ERROR: {result['error'].get('message', result['error'])}", err=True)
            raise typer.Exit(1)
        value = result.get("value", result.get("description", str(result)))
        if isinstance(value, (dict, list)):
            typer.echo(json.dumps(value, indent=2))
        else:
            typer.echo(str(value))
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: read / html
# ---------------------------------------------------------------------------

@app.command()
def read(
    selector: Optional[str] = typer.Argument(None, help="CSS selector (default: whole page)"),
    limit: int = typer.Option(50000, "--limit", "-l", help="Max chars to output"),
):
    """Extract text content from the page or an element."""
    cdp = _connect()
    try:
        if selector:
            js = f"(document.querySelector({json.dumps(selector)}) || {{}}).innerText || ''"
        else:
            js = "document.body.innerText"
        result = _eval_js(cdp, js)
        if isinstance(result, dict) and "error" in result:
            typer.echo(f"[browser] ERROR: {result['error'].get('message', result['error'])}", err=True)
            raise typer.Exit(1)
        text = str(result.get("value", ""))
        if len(text) > limit:
            text = text[:limit] + f"\n\n[truncated at {limit} chars]"
        typer.echo(text)
    finally:
        cdp.close()


@app.command()
def html(
    selector: Optional[str] = typer.Argument(None, help="CSS selector (default: whole page)"),
    limit: int = typer.Option(100000, "--limit", "-l", help="Max chars to output"),
):
    """Extract HTML from the page or an element."""
    cdp = _connect()
    try:
        if selector:
            js = f"(document.querySelector({json.dumps(selector)}) || {{}}).outerHTML || ''"
        else:
            js = "document.documentElement.outerHTML"
        result = _eval_js(cdp, js)
        if isinstance(result, dict) and "error" in result:
            typer.echo(f"[browser] ERROR: {result['error'].get('message', result['error'])}", err=True)
            raise typer.Exit(1)
        text = str(result.get("value", ""))
        if len(text) > limit:
            text = text[:limit] + f"\n\n[truncated at {limit} chars]"
        typer.echo(text)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: click / fill / wait
# ---------------------------------------------------------------------------

@app.command()
def click(
    selector: str = typer.Argument(..., help="CSS selector to click"),
):
    """Click an element."""
    cdp = _connect()
    try:
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return {{found: false}};
            el.click();
            return {{found: true, tag: el.tagName, text: (el.innerText || '').slice(0, 80)}};
        }})()
        """
        result = _eval_js(cdp, js)
        if isinstance(result, dict) and "error" in result:
            typer.echo(f"[browser] ERROR: {result['error'].get('message', result['error'])}", err=True)
            raise typer.Exit(1)
        value = result.get("value", {})
        if not value.get("found"):
            typer.echo(f"[browser] ERROR: element not found: {selector}", err=True)
            raise typer.Exit(1)
        tag = value.get("tag", "?")
        text = value.get("text", "")
        typer.echo(f"[browser] clicked <{tag.lower()}> {text}", err=True)
    finally:
        cdp.close()


@app.command()
def fill(
    selector: str = typer.Argument(..., help="CSS selector of input"),
    text: str = typer.Argument(..., help="Text to fill"),
):
    """Fill an input field."""
    cdp = _connect()
    try:
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return {{found: false}};
            el.focus();
            el.value = {json.dumps(text)};
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            return {{found: true, tag: el.tagName}};
        }})()
        """
        result = _eval_js(cdp, js)
        if isinstance(result, dict) and "error" in result:
            typer.echo(f"[browser] ERROR: {result['error'].get('message', result['error'])}", err=True)
            raise typer.Exit(1)
        value = result.get("value", {})
        if not value.get("found"):
            typer.echo(f"[browser] ERROR: element not found: {selector}", err=True)
            raise typer.Exit(1)
        typer.echo(f"[browser] filled {selector}", err=True)
    finally:
        cdp.close()


@app.command()
def wait(
    selector: str = typer.Argument(..., help="CSS selector to wait for"),
    timeout: int = typer.Option(10000, "--timeout", "-t", help="Timeout in ms"),
):
    """Wait for an element to appear."""
    cdp = _connect()
    try:
        deadline = time.time() + timeout / 1000
        while time.time() < deadline:
            js = f"!!document.querySelector({json.dumps(selector)})"
            result = _eval_js(cdp, js)
            if result.get("value") is True:
                typer.echo(f"[browser] found: {selector}", err=True)
                return
            time.sleep(0.2)
        typer.echo(f"[browser] ERROR: timeout waiting for {selector} ({timeout}ms)", err=True)
        raise typer.Exit(1)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: type (keyboard input)
# ---------------------------------------------------------------------------

@app.command("type")
def type_text(
    text: str = typer.Argument(..., help="Text to type"),
):
    """Type text via keyboard events (into the currently focused element)."""
    cdp = _connect()
    try:
        for char in text:
            cdp.send("Input.dispatchKeyEvent", {
                "type": "keyDown",
                "text": char,
                "key": char,
                "unmodifiedText": char,
            })
            cdp.send("Input.dispatchKeyEvent", {
                "type": "keyUp",
                "key": char,
            })
        typer.echo(f"[browser] typed {len(text)} chars", err=True)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: key (named key press)
# ---------------------------------------------------------------------------

# Map friendly names → CDP key identifiers
_KEY_MAP = {
    "enter": "Return", "return": "Return",
    "tab": "Tab", "escape": "Escape", "esc": "Escape",
    "space": "Space", "backspace": "Backspace", "delete": "Delete",
    "arrowup": "ArrowUp", "arrowdown": "ArrowDown",
    "arrowleft": "ArrowLeft", "arrowright": "ArrowRight",
    "home": "Home", "end": "End", "pageup": "PageUp", "pagedown": "PageDown",
    "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4", "f5": "F5",
    "f12": "F12",
}


@app.command()
def key(
    name: str = typer.Argument(..., help="Key name: enter, tab, escape, space, arrowdown, etc."),
    selector: Optional[str] = typer.Option(None, "--focus", "-f", help="CSS selector to focus first"),
):
    """Press a named key (Enter, Tab, Escape, ArrowDown, etc.)."""
    cdp = _connect()
    try:
        if selector:
            focus_js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return false;
                el.focus();
                return true;
            }})()
            """
            r = _eval_js(cdp, focus_js)
            if not r.get("value"):
                typer.echo(f"[browser] ERROR: element not found: {selector}", err=True)
                raise typer.Exit(1)

        canonical = _KEY_MAP.get(name.lower(), name)
        cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": canonical})
        cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": canonical})
        typer.echo(f"[browser] key: {canonical}", err=True)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: scroll
# ---------------------------------------------------------------------------

@app.command()
def scroll(
    selector: Optional[str] = typer.Argument(None, help="CSS selector to scroll into view (default: window)"),
    x: int = typer.Option(0, "--x", help="Horizontal scroll delta (px)"),
    y: int = typer.Option(300, "--y", help="Vertical scroll delta (px, positive = down)"),
):
    """Scroll the page or bring an element into view."""
    cdp = _connect()
    try:
        if selector:
            js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return false;
                el.scrollIntoView({{behavior: 'instant', block: 'center'}});
                return true;
            }})()
            """
            r = _eval_js(cdp, js)
            if not r.get("value"):
                typer.echo(f"[browser] ERROR: element not found: {selector}", err=True)
                raise typer.Exit(1)
            typer.echo(f"[browser] scrolled {selector} into view", err=True)
        else:
            js = f"window.scrollBy({x}, {y})"
            _eval_js(cdp, js)
            typer.echo(f"[browser] scrolled ({x}, {y})", err=True)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: select (dropdown)
# ---------------------------------------------------------------------------

@app.command("select")
def select_option(
    selector: str = typer.Argument(..., help="CSS selector of <select> element"),
    value: str = typer.Argument(..., help="Option value or visible text to select"),
):
    """Select an option from a <select> dropdown by value or text."""
    cdp = _connect()
    try:
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return {{found: false}};
            // Try matching by value first, then by text
            let matched = false;
            for (const opt of el.options) {{
                if (opt.value === {json.dumps(value)} || opt.text.trim() === {json.dumps(value)}) {{
                    el.value = opt.value;
                    matched = true;
                    break;
                }}
            }}
            if (!matched) return {{found: true, matched: false}};
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            return {{found: true, matched: true, selected: el.value}};
        }})()
        """
        r = _eval_js(cdp, js)
        val = r.get("value", {})
        if not val.get("found"):
            typer.echo(f"[browser] ERROR: element not found: {selector}", err=True)
            raise typer.Exit(1)
        if not val.get("matched"):
            typer.echo(f"[browser] ERROR: no option matching '{value}' in {selector}", err=True)
            raise typer.Exit(1)
        typer.echo(f"[browser] selected '{val.get('selected')}' in {selector}", err=True)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: hover
# ---------------------------------------------------------------------------

@app.command()
def hover(
    selector: str = typer.Argument(..., help="CSS selector to hover over"),
):
    """Hover over an element (triggers :hover, mouseover events)."""
    cdp = _connect()
    try:
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {{x: r.x + r.width/2, y: r.y + r.height/2, tag: el.tagName}};
        }})()
        """
        r = _eval_js(cdp, js)
        val = r.get("value")
        if not val:
            typer.echo(f"[browser] ERROR: element not found: {selector}", err=True)
            raise typer.Exit(1)

        x, y = val["x"], val["y"]
        cdp.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
        typer.echo(f"[browser] hovered <{val['tag'].lower()}> at ({x:.0f}, {y:.0f})", err=True)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: new-tab
# ---------------------------------------------------------------------------

@app.command("new-tab")
def new_tab(
    url: str = typer.Argument("about:blank", help="URL to open in new tab"),
):
    """Open a new browser tab."""
    session = _require_session()
    port = session["port"]
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/json/new?{url}",
            method="PUT",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        target_id = data.get("id")
        session["active_target"] = target_id
        _save_session(session)
        typer.echo(f"[browser] new tab: {data.get('url', url)}", err=True)
    except Exception as e:
        typer.echo(f"[browser] ERROR: could not open new tab: {e}", err=True)
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Commands: close-tab
# ---------------------------------------------------------------------------

@app.command("close-tab")
def close_tab(
    index: Optional[int] = typer.Argument(None, help="Tab index (default: active tab)"),
):
    """Close a browser tab."""
    session = _require_session()
    port = session["port"]
    pages = _page_targets(port)

    if not pages:
        typer.echo("[browser] no tabs to close", err=True)
        return

    if index is not None:
        if index < 0 or index >= len(pages):
            typer.echo(f"[browser] ERROR: tab index {index} out of range", err=True)
            raise typer.Exit(1)
        target = pages[index]
    else:
        active_id = session.get("active_target")
        target = next((p for p in pages if p["id"] == active_id), pages[0])

    target_id = target["id"]
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/json/close/{target_id}",
            method="GET",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        typer.echo(f"[browser] ERROR: {e}", err=True)
        raise typer.Exit(1)

    # Update active target
    remaining = [p for p in pages if p["id"] != target_id]
    session["active_target"] = remaining[0]["id"] if remaining else None
    _save_session(session)
    typer.echo(f"[browser] closed: {target.get('title', target_id)}", err=True)


# ---------------------------------------------------------------------------
# Commands: snap (screenshot)
# ---------------------------------------------------------------------------

@app.command()
def snap(
    selector: Optional[str] = typer.Argument(None, help="CSS selector to capture (default: full page)"),
    out: str = typer.Option("/tmp/browser-snap.png", "--out", "-o", help="Output PNG path"),
    full_page: bool = typer.Option(False, "--full-page", help="Capture full scrollable page"),
):
    """Take a screenshot."""
    cdp = _connect()
    try:
        params: dict = {"format": "png"}

        if selector:
            # Get element bounding rect
            js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return null;
                const r = el.getBoundingClientRect();
                return {{x: r.x, y: r.y, width: r.width, height: r.height, scale: window.devicePixelRatio}};
            }})()
            """
            rect_result = _eval_js(cdp, js)
            rect = rect_result.get("value")
            if not rect:
                typer.echo(f"[browser] ERROR: element not found: {selector}", err=True)
                raise typer.Exit(1)
            params["clip"] = {
                "x": rect["x"],
                "y": rect["y"],
                "width": rect["width"],
                "height": rect["height"],
                "scale": rect.get("scale", 1),
            }

        if full_page:
            # Get full page dimensions
            js = "({width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight})"
            dims = _eval_js(cdp, js)
            dims_val = dims.get("value", {})
            if dims_val:
                params["clip"] = {
                    "x": 0, "y": 0,
                    "width": dims_val["width"],
                    "height": dims_val["height"],
                    "scale": 1,
                }
                params["captureBeyondViewport"] = True

        result = cdp.send("Page.captureScreenshot", params)
        if result.get("error"):
            typer.echo(f"[browser] ERROR: {result['error'].get('message', result['error'])}", err=True)
            raise typer.Exit(1)

        img_data = base64.b64decode(result["result"]["data"])
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(img_data)

        size_kb = len(img_data) // 1024
        typer.echo(f"[browser] saved: {out_path} ({size_kb} KB)", err=True)
        typer.echo(f"[browser] read : use Read tool on {out_path}", err=True)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: tabs / tab
# ---------------------------------------------------------------------------

@app.command()
def tabs():
    """List open browser tabs."""
    session = _require_session()
    pages = _page_targets(session["port"])
    active_id = session.get("active_target")

    if not pages:
        typer.echo("[browser] no tabs open")
        return

    for i, p in enumerate(pages):
        marker = " *" if p["id"] == active_id else ""
        title = p.get("title", "(untitled)")
        url = p.get("url", "")
        typer.echo(f"[{i}]{marker} {title}")
        typer.echo(f"     {url}")


@app.command()
def tab(
    index: int = typer.Argument(..., help="Tab index (from 'af browser tabs')"),
):
    """Switch to a tab by index."""
    session = _require_session()
    pages = _page_targets(session["port"])

    if index < 0 or index >= len(pages):
        typer.echo(f"[browser] ERROR: tab index {index} out of range (0-{len(pages)-1})", err=True)
        raise typer.Exit(1)

    target = pages[index]
    session["active_target"] = target["id"]
    _save_session(session)
    typer.echo(f"[browser] switched to [{index}] {target.get('title', '(untitled)')}", err=True)


# ---------------------------------------------------------------------------
# Commands: console
# ---------------------------------------------------------------------------

def _format_console_event(ev: dict) -> Optional[str]:
    """Format a Runtime.consoleAPICalled event into a printable line."""
    params = ev.get("params", {})
    level = params.get("type", "log")
    args = params.get("args", [])
    parts = []
    for arg in args:
        if "value" in arg:
            parts.append(str(arg["value"]))
        elif "description" in arg:
            parts.append(arg["description"])
        else:
            parts.append(str(arg))
    text = " ".join(parts)
    return f"[{level}] {text}"


@app.command()
def console(
    duration: float = typer.Option(2.0, "--duration", "-d", help="Seconds to collect (ignored with --watch)"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Stream continuously until Ctrl+C"),
    level: Optional[str] = typer.Option(None, "--level", "-l", help="Filter: log, warn, error, info, debug"),
):
    """Dump console messages. Use --watch to stream continuously."""
    cdp = _connect()
    try:
        cdp.send("Runtime.enable")

        if watch:
            typer.echo("[browser] streaming console — Ctrl+C to stop", err=True)
            cdp._ws.settimeout(0.5)
            try:
                while True:
                    try:
                        raw = cdp._ws.recv()
                        if not raw:
                            continue
                        data = json.loads(raw)
                        if data.get("method") == "Runtime.consoleAPICalled":
                            line = _format_console_event(data)
                            if line:
                                if level and not line.startswith(f"[{level}]"):
                                    continue
                                typer.echo(line)
                    except Exception:
                        pass
            except KeyboardInterrupt:
                typer.echo("\n[browser] stopped", err=True)
            return

        # One-shot mode
        events = cdp.collect_events(seconds=duration)
        console_events = [e for e in events if e.get("method") == "Runtime.consoleAPICalled"]
        if not console_events:
            typer.echo("[browser] no console messages captured")
            typer.echo(f"  (listened {duration}s — navigate first, then run this)")
            return
        for ev in console_events:
            line = _format_console_event(ev)
            if line:
                if level and not line.startswith(f"[{level}]"):
                    continue
                typer.echo(line)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: network
# ---------------------------------------------------------------------------

def _format_network_row(method: str, status: int, url: str, mime: str, size: int, ms: int) -> str:
    status_str = str(status) if status else "---"
    size_str = f"{size // 1024}KB" if size >= 1024 else f"{size}B"
    short_url = url if len(url) <= 70 else url[:67] + "..."
    return f"{method:<6} {status_str:<5} {ms:>6}ms {size_str:>8}  {mime:<22} {short_url}"


@app.command()
def network(
    filter_pattern: Optional[str] = typer.Option(None, "--filter", "-f", help="URL substring/regex filter"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Stream requests in real time until Ctrl+C"),
    errors: bool = typer.Option(False, "--errors", "-e", help="Show only failed requests (4xx/5xx)"),
):
    """List network requests via CDP. Use --watch to stream in real time."""
    cdp = _connect()
    try:
        cdp.send("Network.enable")
        pat = re.compile(filter_pattern, re.IGNORECASE) if filter_pattern else None

        if watch:
            typer.echo("[browser] streaming network — Ctrl+C to stop", err=True)
            typer.echo(f"{'Method':<6} {'St':<5} {'Time':>6}   {'Size':>8}  {'MIME':<22} URL")
            typer.echo("-" * 100)

            # Track request metadata by requestId
            pending: dict = {}
            cdp._ws.settimeout(0.5)
            try:
                while True:
                    try:
                        raw = cdp._ws.recv()
                        if not raw:
                            continue
                        data = json.loads(raw)
                        method = data.get("method", "")
                        params = data.get("params", {})

                        if method == "Network.requestWillBeSent":
                            req_id = params.get("requestId")
                            req = params.get("request", {})
                            pending[req_id] = {
                                "method": req.get("method", "GET"),
                                "url": req.get("url", ""),
                                "ts": params.get("timestamp", 0),
                            }

                        elif method == "Network.responseReceived":
                            req_id = params.get("requestId")
                            resp = params.get("response", {})
                            url = resp.get("url", "")
                            status = resp.get("status", 0)
                            mime = resp.get("mimeType", "")
                            size = resp.get("encodedDataLength", 0)
                            ts_now = params.get("timestamp", 0)
                            info = pending.pop(req_id, {})
                            http_method = info.get("method", "GET")
                            ms = int((ts_now - info.get("ts", ts_now)) * 1000)

                            if pat and not pat.search(url):
                                continue
                            if errors and status < 400:
                                continue
                            typer.echo(_format_network_row(http_method, status, url, mime, size, ms))

                        elif method == "Network.loadingFailed":
                            req_id = params.get("requestId")
                            info = pending.pop(req_id, {})
                            url = info.get("url", params.get("requestId", "?"))
                            if pat and not pat.search(url):
                                continue
                            typer.echo(f"{'FAIL':<6} {'ERR':<5} {'':>6}   {'':>8}  {'':22} {url}  ({params.get('errorText','')})")

                    except Exception:
                        pass
            except KeyboardInterrupt:
                typer.echo("\n[browser] stopped", err=True)
            return

        # One-shot: collect responses for a short window then display
        # Enable and collect events over 1s (catches requests from previous navigation)
        pending: dict = {}
        responses: list = []

        cdp._ws.settimeout(0.2)
        deadline = time.time() + 1.5
        while time.time() < deadline:
            try:
                raw = cdp._ws.recv()
                if not raw:
                    continue
                data = json.loads(raw)
                method = data.get("method", "")
                params = data.get("params", {})
                if method == "Network.requestWillBeSent":
                    rid = params.get("requestId")
                    req = params.get("request", {})
                    pending[rid] = {"method": req.get("method","GET"), "url": req.get("url",""), "ts": params.get("timestamp",0)}
                elif method == "Network.responseReceived":
                    rid = params.get("requestId")
                    resp = params.get("response", {})
                    info = pending.get(rid, {})
                    ts_now = params.get("timestamp", 0)
                    responses.append({
                        "method": info.get("method","GET"),
                        "url": resp.get("url",""),
                        "status": resp.get("status",0),
                        "mime": resp.get("mimeType",""),
                        "size": resp.get("encodedDataLength",0),
                        "ms": int((ts_now - info.get("ts", ts_now)) * 1000),
                    })
            except Exception:
                pass

        if pat:
            responses = [r for r in responses if pat.search(r["url"])]
        if errors:
            responses = [r for r in responses if r["status"] >= 400]

        if not responses:
            typer.echo("[browser] no network requests captured (try --watch after navigating)")
            return

        typer.echo(f"{'Method':<6} {'St':<5} {'Time':>6}   {'Size':>8}  {'MIME':<22} URL")
        typer.echo("-" * 100)
        for r in responses:
            typer.echo(_format_network_row(r["method"], r["status"], r["url"], r["mime"], r["size"], r["ms"]))
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: wait-for-url
# ---------------------------------------------------------------------------

@app.command("wait-for-url")
def wait_for_url(
    pattern: str = typer.Argument(..., help="URL substring or regex to match"),
    timeout: int = typer.Option(30000, "--timeout", "-t", help="Timeout in ms"),
):
    """Wait until the current page URL matches a pattern (useful for redirects, OAuth flows)."""
    cdp = _connect()
    try:
        pat = re.compile(pattern, re.IGNORECASE)
        deadline = time.time() + timeout / 1000
        while time.time() < deadline:
            result = _eval_js(cdp, "window.location.href")
            current = result.get("value", "")
            if pat.search(current):
                typer.echo(current)
                return
            time.sleep(0.3)
        typer.echo(f"[browser] ERROR: timeout waiting for URL matching '{pattern}'", err=True)
        result = _eval_js(cdp, "window.location.href")
        typer.echo(f"[browser] current URL: {result.get('value','?')}", err=True)
        raise typer.Exit(1)
    finally:
        cdp.close()


# ---------------------------------------------------------------------------
# Commands: a11y (accessibility tree)
# ---------------------------------------------------------------------------

@app.command()
def a11y():
    """Dump the accessibility tree."""
    cdp = _connect()
    try:
        result = cdp.send("Accessibility.getFullAXTree")
        if result.get("error"):
            # Fallback: use JS-based accessibility info
            typer.echo("[browser] CDP Accessibility domain not available, using JS fallback", err=True)
            js = """
            (() => {
                const walk = (el, depth) => {
                    if (!el || depth > 6) return [];
                    const lines = [];
                    const role = el.getAttribute('role') || el.tagName.toLowerCase();
                    const label = el.getAttribute('aria-label') || el.getAttribute('alt') || '';
                    const text = (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3)
                        ? el.childNodes[0].textContent.trim().slice(0, 60) : '';
                    const indent = '  '.repeat(depth);
                    let line = `${indent}${role}`;
                    if (label) line += ` "${label}"`;
                    if (text) line += ` — ${text}`;
                    lines.push(line);
                    for (const child of el.children) {
                        lines.push(...walk(child, depth + 1));
                    }
                    return lines;
                };
                return walk(document.body, 0).join('\\n');
            })()
            """
            result = _eval_js(cdp, js)
            text = result.get("value", "")
            if text:
                typer.echo(text)
            else:
                typer.echo("[browser] could not read accessibility tree")
            return

        nodes = result.get("result", {}).get("nodes", [])
        if not nodes:
            typer.echo("[browser] empty accessibility tree")
            return

        # Build tree output
        for node in nodes[:200]:  # Cap output
            props = node.get("properties", [])
            role = node.get("role", {}).get("value", "")
            name = node.get("name", {}).get("value", "")
            depth = node.get("depth", 0) if "depth" in node else 0

            # Estimate depth from backendDOMNodeId or parent chain
            indent = "  " * min(depth, 10)
            line = f"{indent}{role}"
            if name:
                line += f' "{name}"'

            # Add key properties
            for prop in props:
                pname = prop.get("name", "")
                pval = prop.get("value", {}).get("value", "")
                if pname in ("disabled", "checked", "expanded", "selected", "required") and pval:
                    line += f" [{pname}]"

            typer.echo(line)
    finally:
        cdp.close()
