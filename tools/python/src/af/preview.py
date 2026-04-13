"""af preview — serve HTML design mockups for visual comparison.

Watches a directory for HTML files and serves the newest one at /.
Auto-refreshes the browser via SSE when new files appear. User clicks
are recorded to events.jsonl so Agent can read the chosen design.

Write any .html file to the directory to display it. Name files
descriptively: option-a.html, sidebar-nav.html, dark-theme.html, etc.
"""

import json
import os
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Serve HTML design mockups for visual comparison.")

# ---------------------------------------------------------------------------
# HTML wrappers
# ---------------------------------------------------------------------------

_FULL_DOC_INJECT = """<script>
  const _es=new EventSource('/events');
  _es.onmessage=e=>{if(e.data==='reload')location.reload();};
  function recordChoice(n){fetch('/choice',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({choice:n,type:'select'})});}
</script>"""

_FRAGMENT_WRAPPER = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Preview — {filename}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
  {content}
  <script>
    const _es=new EventSource('/events');
    _es.onmessage=e=>{{if(e.data==='reload')location.reload();}};
  </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Server state
# ---------------------------------------------------------------------------

class _State:
    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.events_file = directory / "events.jsonl"
        self.sse_clients: list = []
        self.lock = threading.Lock()
        self._last_name: Optional[str] = None
        self._last_mtime: float = 0.0

    def newest_html(self) -> Optional[Path]:
        files = sorted(
            self.directory.glob("*.html"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return files[0] if files else None

    def record_choice(self, data: dict):
        data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        with open(self.events_file, "a") as f:
            f.write(json.dumps(data) + "\n")
        typer.echo(f"[preview] choice: {data['choice']}")

    def broadcast(self):
        with self.lock:
            dead = []
            for client in self.sse_clients:
                try:
                    client.wfile.write(b"data: reload\n\n")
                    client.wfile.flush()
                except Exception:
                    dead.append(client)
            for d in dead:
                self.sse_clients.remove(d)

    def watch(self):
        while True:
            newest = self.newest_html()
            if newest:
                mtime = newest.stat().st_mtime
                if newest.name != self._last_name or mtime != self._last_mtime:
                    if self._last_name is not None:
                        typer.echo(f"[preview] updated: {newest.name}")
                        self.broadcast()
                    self._last_name = newest.name
                    self._last_mtime = mtime
            time.sleep(0.5)


_state: Optional[_State] = None


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/events":
            self._sse()
        elif self.path in ("/", "/index.html"):
            self._serve()
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path == "/choice":
            n = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(n))
                _state.record_choice(data)
            except Exception:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        else:
            self.send_response(404); self.end_headers()

    def _sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        with _state.lock:
            _state.sse_clients.append(self)
        try:
            while True:
                time.sleep(1)
        except Exception:
            pass

    def _serve(self):
        path = _state.newest_html()
        if not path:
            body = b"<h1>Waiting for HTML files...</h1><p>Write .html files to the preview directory.</p>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

        content = path.read_text(encoding="utf-8")
        is_full = content.lstrip().lower().startswith(("<!doctype", "<html"))

        if is_full:
            html = content.replace("</body>", _FULL_DOC_INJECT + "</body>") \
                   if "</body>" in content else content + _FULL_DOC_INJECT
        else:
            html = _FRAGMENT_WRAPPER.format(filename=path.name, content=content)

        encoded = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------

@app.callback(invoke_without_command=True)
def main(
    directory: str = typer.Argument("/tmp/ui-preview",
        help="Directory to watch for HTML files"),
    port: int = typer.Option(0, help="Port (0 = random available)"),
    no_open: bool = typer.Option(False, "--no-open", help="Don't open browser"),
):
    """Serve HTML design mockups. Write .html files to the directory to show them."""
    global _state
    _state = _State(Path(directory))

    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    actual_port = server.server_address[1]
    url = f"http://localhost:{actual_port}"

    typer.echo(f"[preview] watching : {_state.directory}")
    typer.echo(f"[preview] server   : {url}")
    typer.echo(f"[preview] choices  : {_state.events_file}")
    typer.echo(f"[preview] write .html files to show them — browser auto-refreshes")
    typer.echo(f"[preview] Ctrl+C to stop")

    threading.Thread(target=_state.watch, daemon=True).start()

    if not no_open:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        typer.echo("\n[preview] stopped")
