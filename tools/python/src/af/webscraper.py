"""af webscraper — pure-HTTP web scraping helpers.

Subcommands:
  inspect   Recon a URL — status, framework, embedded JSON, JSON-LD, XHR
            endpoints, robots.txt + sitemaps, RSS/Atom feeds, Next.js
            buildId → JSON endpoint, anti-bot signals. Results cached for
            1 hour.
  fetch     One-shot HTTP GET with real browser headers, HTTP/2, retries.
            Optional --impersonate swaps in curl_cffi for TLS fingerprinting.
  scaffold  Write a ready-to-edit `uv run` scraper script. Pre-fills
            KEEP_TYPES, API_URL, crawl-delay, and Next.js data paths from
            the latest `inspect` for this URL (auto-runs inspect if needed).

Runtime deps:
  httpx[http2]   Primary HTTP client (installed with af).
  selectolax     Fast HTML5 parser with CSS selectors (installed with af).
  curl_cffi      Lazy-installed only when --impersonate is used.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import typer

app = typer.Typer(help="Web scraping recon, fetch, and scaffold helpers.")


# ── Dependency bootstrap ──────────────────────────────────────────────────────

def _ensure(*packages: str) -> None:
    """Install optional packages into the running Python env on first use.
    Hard deps are in pyproject — this is only for curl_cffi / brotli extras."""
    missing: list[str] = []
    for pkg in packages:
        import_name = pkg.split("[")[0].replace("-", "_")
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return

    typer.echo(f"[webscraper] installing {', '.join(missing)}...", err=True)
    attempts = [
        [sys.executable, "-m", "pip", "install", *missing],
        ["uv", "pip", "install", "--python", sys.executable, *missing],
    ]
    for cmd in attempts:
        try:
            subprocess.run(cmd, check=True)
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    typer.echo(
        f"[webscraper] ERROR: could not install {' '.join(missing)}.\n"
        f"  Install manually: uv pip install --python {sys.executable} {' '.join(missing)}",
        err=True,
    )
    raise typer.Exit(1)


# ── Browser-ish defaults ──────────────────────────────────────────────────────

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) "
    "Gecko/20100101 Firefox/128.0"
)

_HEADERS = {
    "User-Agent": _UA,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",  # no br — httpx can't decode without brotli pkg
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}


# ── Report dataclass ─────────────────────────────────────────────────────────

@dataclass
class InspectReport:
    url: str
    final_url: str
    status: int
    http_version: str
    content_type: str
    bytes_downloaded: int
    elapsed_ms: int
    redirect_chain: list[str] = field(default_factory=list)
    robots_allowed: Optional[bool] = None
    robots_crawl_delay: Optional[float] = None
    sitemaps: list[dict[str, Any]] = field(default_factory=list)
    feeds: list[dict[str, str]] = field(default_factory=list)
    framework: list[str] = field(default_factory=list)
    embedded_json: list[dict[str, Any]] = field(default_factory=list)
    jsonld_types: list[str] = field(default_factory=list)
    jsonld_blocks: int = 0
    nextjs_build_id: Optional[str] = None
    nextjs_data_endpoint: Optional[str] = None
    suspected_api_endpoints: list[str] = field(default_factory=list)
    structure: dict[str, int] = field(default_factory=dict)
    anti_bot_signals: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    inspected_at: float = 0.0


# ── Fingerprint tables ───────────────────────────────────────────────────────

_FRAMEWORK_FINGERPRINTS: list[tuple[str, re.Pattern[str]]] = [
    ("Next.js (pages)", re.compile(r'<script id="__NEXT_DATA__"')),
    ("Next.js (app)", re.compile(r'/_next/static/chunks/|self\.__next_f')),
    ("Nuxt", re.compile(r'window\.__NUXT__|__NUXT_DATA__|/_nuxt/')),
    ("Gatsby", re.compile(r'___gatsby|/page-data/')),
    ("SvelteKit", re.compile(r'__sveltekit_|svelte-announcer')),
    ("Remix", re.compile(r'window\.__remixContext')),
    ("Astro", re.compile(r'astro-island|data-astro-')),
    ("Hugo", re.compile(r'<meta name="generator"[^>]*Hugo', re.I)),
    ("Jekyll", re.compile(r'<meta name="generator"[^>]*Jekyll', re.I)),
    ("Eleventy", re.compile(r'<meta name="generator"[^>]*Eleventy', re.I)),
    ("React (Vite)", re.compile(r'/@react-refresh|__vite_plugin_react')),
    ("Shopify", re.compile(r'Shopify\.theme|Shopify\.shop|shopify\.com/s/files')),
    ("WooCommerce", re.compile(r'woocommerce|wc-blocks')),
    ("WordPress", re.compile(r'<meta name="generator"[^>]*WordPress', re.I)),
    ("Wix", re.compile(r'static\.wixstatic\.com|wix-code')),
    ("Squarespace", re.compile(r'static1\.squarespace\.com')),
    ("Webflow", re.compile(r'Webflow\.require')),
    ("Ghost", re.compile(r'<meta name="generator"[^>]*Ghost', re.I)),
    ("Substack", re.compile(r'substackcdn\.com|substack-post')),
    ("Medium", re.compile(r'medium\.com/_/batch|PRELOADED_STATE.*medium', re.I)),
    ("Drupal", re.compile(r'<meta name="generator"[^>]*Drupal', re.I)),
    ("Apollo GraphQL", re.compile(r'__APOLLO_STATE__')),
    ("Redux", re.compile(r'__PRELOADED_STATE__|__INITIAL_STATE__')),
]

_ANTIBOT_FINGERPRINTS: list[tuple[str, re.Pattern[str]]] = [
    ("Cloudflare", re.compile(r'cf-ray|__cf_bm|cf_clearance|cf-chl-bypass|cdn-cgi/challenge-platform', re.I)),
    ("DataDome", re.compile(r'datadome|dd_cookie_test', re.I)),
    ("PerimeterX / HUMAN", re.compile(r'perimeterx|_px\d?|px-captcha', re.I)),
    ("Akamai Bot Manager", re.compile(r'_abck|ak_bmsc', re.I)),
    ("Incapsula / Imperva", re.compile(r'incap_ses|visid_incap', re.I)),
    ("reCAPTCHA", re.compile(r'recaptcha|grecaptcha', re.I)),
    ("hCaptcha", re.compile(r'hcaptcha\.com')),
    ("Generic challenge", re.compile(r'<title>[^<]*(?:challenge|just a moment|access denied)', re.I)),
]

_EMBEDDED_JSON_TARGETS: list[tuple[str, re.Pattern[str]]] = [
    ("__NEXT_DATA__", re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', re.DOTALL)),
    ("window.__INITIAL_STATE__", re.compile(r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\});?\s*</script>', re.DOTALL)),
    ("window.__NUXT__", re.compile(r'window\.__NUXT__\s*=\s*(\{.+?\});?\s*</script>', re.DOTALL)),
    ("window.__APOLLO_STATE__", re.compile(r'window\.__APOLLO_STATE__\s*=\s*(\{.+?\});?\s*</script>', re.DOTALL)),
    ("window.__PRELOADED_STATE__", re.compile(r'window\.__PRELOADED_STATE__\s*=\s*(\{.+?\});?\s*</script>', re.DOTALL)),
]

_API_ENDPOINT = re.compile(
    r'''(?:fetch|axios(?:\.get|\.post)?)\(\s*["']([^"']+)["']'''
    r'''|["'](?:/api/|/graphql|/v\d+/)[^\s"'<>\\]{0,200}["']''',
)


# ── Sitemap / robots helpers ─────────────────────────────────────────────────

def _parse_robots(text: str, ua: str, url: str) -> tuple[Optional[bool], Optional[float], list[str]]:
    """Return (allowed, crawl_delay, sitemap_urls). Uses stdlib + line-scan."""
    from urllib.robotparser import RobotFileParser
    rp = RobotFileParser()
    rp.parse(text.splitlines())
    try:
        allowed = rp.can_fetch(ua, url)
    except Exception:
        allowed = None
    try:
        delay_raw = rp.crawl_delay(ua)
        delay = float(delay_raw) if delay_raw is not None else None
    except Exception:
        delay = None
    sitemaps = [
        line.split(":", 1)[1].strip()
        for line in text.splitlines()
        if line.lower().startswith("sitemap:") and ":" in line
    ]
    return allowed, delay, sitemaps


def _probe_sitemap(client: Any, sitemap_url: str) -> Optional[dict[str, Any]]:
    """HEAD/GET a sitemap URL; return {url, kind, urls, children}."""
    try:
        r = client.get(sitemap_url, timeout=15.0)
    except Exception:
        return None
    if r.status_code != 200:
        return None
    text = r.text[:200_000]  # cap read
    kind = "index" if "<sitemapindex" in text.lower() else "urlset"
    children: list[str] = []
    if kind == "index":
        children = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)
    url_count = len(re.findall(r"<url[\s>]", text))
    return {
        "url": sitemap_url,
        "kind": kind,
        "urls": url_count,
        "children_preview": children[:5],
        "truncated": len(r.text) > 200_000,
    }


def _detect_feeds(tree: Any, base_url: str) -> list[dict[str, str]]:
    """Find RSS/Atom/JSON feeds declared in <head>."""
    feeds: list[dict[str, str]] = []
    seen: set[str] = set()
    for node in tree.css('link[rel="alternate"]'):
        attrs = node.attributes or {}
        t = (attrs.get("type") or "").lower()
        href = attrs.get("href")
        if not href:
            continue
        if t in ("application/rss+xml", "application/atom+xml", "application/json", "application/feed+json"):
            abs_url = urljoin(base_url, href)
            if abs_url in seen:
                continue
            seen.add(abs_url)
            feeds.append({
                "kind": {"application/rss+xml": "rss",
                         "application/atom+xml": "atom",
                         "application/json": "json-feed",
                         "application/feed+json": "json-feed"}[t],
                "title": (attrs.get("title") or "").strip(),
                "url": abs_url,
            })
    return feeds


def _extract_nextjs_data(html: str, final_url: str) -> tuple[Optional[str], Optional[str]]:
    """Extract buildId from __NEXT_DATA__ and construct /_next/data/<buildId>/<path>.json.

    Only pages-router sites expose buildId in __NEXT_DATA__. App router does not.
    """
    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
        html, re.DOTALL,
    )
    if not m:
        return None, None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None, None

    build_id = data.get("buildId") if isinstance(data, dict) else None
    if not isinstance(build_id, str) or not build_id:
        return None, None

    parsed = urlparse(final_url)
    path = parsed.path or "/"
    # /_next/data/<buildId>/<path>.json  (index = /index.json)
    if path.endswith("/"):
        path = path + "index"
    if not path.endswith(".json"):
        path = path + ".json"
    endpoint = f"{parsed.scheme}://{parsed.netloc}/_next/data/{build_id}{path}"
    return build_id, endpoint


# ── Cache ────────────────────────────────────────────────────────────────────

_CACHE_TTL_S = 3600


def _cache_dir() -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    d = base / "af" / "webscraper"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_path(url: str) -> Path:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return _cache_dir() / f"{h}.json"


def _cache_read(url: str, max_age_s: int = _CACHE_TTL_S) -> Optional[InspectReport]:
    path = _cache_path(url)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    inspected_at = float(data.get("inspected_at") or 0.0)
    if time.time() - inspected_at > max_age_s:
        return None
    try:
        return InspectReport(**data)
    except TypeError:
        return None


def _cache_write(report: InspectReport) -> Path:
    path = _cache_path(report.url)
    path.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


# ── Inspect core ─────────────────────────────────────────────────────────────

def _inspect_url(url: str, probe_sitemaps: bool = True) -> InspectReport:
    import httpx  # type: ignore
    from selectolax.parser import HTMLParser  # type: ignore

    report = InspectReport(
        url=url, final_url=url, status=0,
        http_version="", content_type="",
        bytes_downloaded=0, elapsed_ms=0,
        inspected_at=time.time(),
    )

    with httpx.Client(
        http2=True,
        headers=_HEADERS,
        follow_redirects=True,
        timeout=30.0,
    ) as c:
        # robots.txt
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        sitemap_urls: list[str] = []
        try:
            rr = c.get(robots_url, timeout=10.0)
            if rr.status_code == 200:
                allowed, delay, sitemap_urls = _parse_robots(rr.text, _UA, url)
                report.robots_allowed = allowed
                report.robots_crawl_delay = delay
        except Exception:
            pass

        # main fetch
        try:
            r = c.get(url)
        except Exception as e:
            report.notes.append(f"fetch failed: {type(e).__name__}: {e}")
            return report

        report.final_url = str(r.url)
        report.status = r.status_code
        report.http_version = r.http_version
        report.content_type = r.headers.get("content-type", "")
        report.bytes_downloaded = len(r.content)
        report.elapsed_ms = int(r.elapsed.total_seconds() * 1000)
        report.redirect_chain = [str(h.url) for h in r.history]

        cookie_blob = "; ".join(f"{k}={v}" for k, v in r.cookies.items())
        header_blob = "\n".join(f"{k}: {v}" for k, v in r.headers.items())
        meta_blob = cookie_blob + "\n" + header_blob

        for name, pat in _ANTIBOT_FINGERPRINTS:
            if pat.search(meta_blob) and name not in report.anti_bot_signals:
                report.anti_bot_signals.append(name)

        if "text/html" not in report.content_type and "xml" not in report.content_type:
            report.notes.append(
                f"response is not HTML ({report.content_type}) — nothing more to parse"
            )
            # still probe sitemaps if they were in robots.txt
            if probe_sitemaps and sitemap_urls:
                _attach_sitemaps(c, sitemap_urls, report)
            return report

        html = r.text

        # Framework detection
        for name, pat in _FRAMEWORK_FINGERPRINTS:
            if pat.search(html):
                report.framework.append(name)

        # Anti-bot signals in body
        for name, pat in _ANTIBOT_FINGERPRINTS:
            if pat.search(html) and name not in report.anti_bot_signals:
                report.anti_bot_signals.append(name)

        # Embedded JSON
        for label, pat in _EMBEDDED_JSON_TARGETS:
            m = pat.search(html)
            if m:
                raw = m.group(1)
                entry = {"name": label, "size_bytes": len(raw)}
                try:
                    parsed_json = json.loads(raw)
                    if isinstance(parsed_json, dict):
                        entry["top_level_keys"] = sorted(list(parsed_json.keys()))[:15]
                except json.JSONDecodeError:
                    entry["parse_error"] = True
                report.embedded_json.append(entry)

        # Next.js buildId → data endpoint
        build_id, data_ep = _extract_nextjs_data(html, report.final_url)
        report.nextjs_build_id = build_id
        report.nextjs_data_endpoint = data_ep

        # Parse HTML for feeds + structure + jsonld
        try:
            tree = HTMLParser(html)
        except Exception as e:
            report.notes.append(f"selectolax parse failed: {e}")
            if probe_sitemaps and sitemap_urls:
                _attach_sitemaps(c, sitemap_urls, report)
            return report

        # Feeds
        report.feeds = _detect_feeds(tree, report.final_url)

        # JSON-LD
        jsonld_nodes = tree.css('script[type="application/ld+json"]')
        report.jsonld_blocks = len(jsonld_nodes)
        seen_types: set[str] = set()
        for n in jsonld_nodes:
            text = n.text()
            if not text:
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            entries = data if isinstance(data, list) else [data]
            extra: list[Any] = []
            for e in entries:
                if isinstance(e, dict) and isinstance(e.get("@graph"), list):
                    extra.extend(e["@graph"])
            entries = entries + extra
            for entry in entries:
                if isinstance(entry, dict):
                    t = entry.get("@type")
                    if isinstance(t, str):
                        seen_types.add(t)
                    elif isinstance(t, list):
                        seen_types.update(x for x in t if isinstance(x, str))
        report.jsonld_types = sorted(seen_types)

        # Structure counts
        report.structure = {
            "article": len(tree.css("article")),
            "table": len(tree.css("table")),
            "rel_next": len(tree.css('a[rel="next"], link[rel="next"]')),
            "forms": len(tree.css("form")),
            "images": len(tree.css("img")),
            "nav_links": len(tree.css("nav a")),
        }

        # API endpoints
        endpoints: set[str] = set()
        for m in _API_ENDPOINT.finditer(html):
            hit = m.group(1) or m.group(0)
            hit = hit.strip('"\' \t\n\\').rstrip("\\")
            if 4 < len(hit) < 200 and ("api" in hit or "graphql" in hit or "/v1/" in hit or "/v2/" in hit):
                endpoints.add(hit)
        report.suspected_api_endpoints = sorted(endpoints)[:15]

        # Sitemaps — from robots.txt, or probe common paths
        if probe_sitemaps:
            candidates = sitemap_urls[:]
            if not candidates:
                for guess in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"):
                    candidates.append(f"{parsed.scheme}://{parsed.netloc}{guess}")
                candidates = candidates[:1]  # only probe /sitemap.xml if robots.txt had none
            _attach_sitemaps(c, candidates, report)

    return report


def _attach_sitemaps(client: Any, urls: list[str], report: InspectReport) -> None:
    seen: set[str] = set()
    for u in urls[:5]:
        if u in seen:
            continue
        seen.add(u)
        info = _probe_sitemap(client, u)
        if info:
            report.sitemaps.append(info)


# ── Recommendation ───────────────────────────────────────────────────────────

def _recommend_mode(r: InspectReport) -> str:
    if r.nextjs_data_endpoint:
        return "api"
    if any(e["name"] == "__NEXT_DATA__" and not e.get("parse_error") for e in r.embedded_json):
        return "nextdata"
    if r.jsonld_blocks and r.jsonld_types:
        return "jsonld"
    if r.suspected_api_endpoints:
        return "api"
    if 1 <= r.structure.get("article", 0) <= 3:
        return "article"
    return "html"


def _recommend_reason(r: InspectReport, mode: str) -> str:
    reasons = {
        "nextdata": "Next.js page with clean __NEXT_DATA__ JSON — parse it, skip the DOM.",
        "jsonld":   f"JSON-LD present ({', '.join(r.jsonld_types[:3])}) — structured data for free.",
        "api":      "Direct JSON endpoint available — hit it, skip HTML entirely.",
        "article":  "Single-article layout — trafilatura will extract the body cleanly.",
        "html":     "No shortcuts; write CSS selectors against the rendered DOM.",
    }
    return reasons.get(mode, "fallback")


# ── Report rendering ─────────────────────────────────────────────────────────

def _render_report(r: InspectReport) -> str:
    yes = lambda x: "✓" if x else "✗"  # noqa: E731
    lines: list[str] = []
    L = lines.append

    L(f"# webscraper inspect — {r.url}")
    L("")
    L("## Request")
    L(f"- final URL     : {r.final_url}")
    L(f"- status        : {r.status}  ({r.http_version})")
    L(f"- content-type  : {r.content_type}")
    L(f"- size          : {r.bytes_downloaded:,} bytes  in {r.elapsed_ms} ms")
    if r.redirect_chain:
        L(f"- redirects     : {len(r.redirect_chain)}")
        for hop in r.redirect_chain:
            L(f"    → {hop}")

    L("")
    L("## robots.txt")
    if r.robots_allowed is None:
        L("- unreachable / missing")
    else:
        L(f"- allowed for our UA : {yes(r.robots_allowed)}")
        if r.robots_crawl_delay is not None:
            L(f"- crawl-delay       : {r.robots_crawl_delay}s")

    L("")
    L("## Sitemaps")
    if r.sitemaps:
        for sm in r.sitemaps:
            tail = f" ({sm['urls']} <url> entries)" if sm.get("urls") else ""
            trunc = "  [truncated at 200KB]" if sm.get("truncated") else ""
            L(f"- {sm['kind']:<7} {sm['url']}{tail}{trunc}")
            for c in sm.get("children_preview", []):
                L(f"    → {c}")
    else:
        L("- none found")

    L("")
    L("## Feeds (RSS / Atom / JSON Feed)")
    if r.feeds:
        for f in r.feeds:
            title = f" — {f['title']}" if f.get("title") else ""
            L(f"- {f['kind']:<9} {f['url']}{title}")
    else:
        L("- none declared")

    L("")
    L("## Framework / build")
    if r.framework:
        for fw in r.framework:
            L(f"- {fw}")
    else:
        L("- none detected (plain HTML, or unknown stack)")

    L("")
    L("## Embedded JSON state")
    if r.embedded_json:
        for e in r.embedded_json:
            keys = e.get("top_level_keys")
            tail = f" — top keys: {keys}" if keys else ""
            err = "  [parse FAILED]" if e.get("parse_error") else ""
            L(f"- {e['name']}  ({e['size_bytes']:,} bytes){tail}{err}")
        if r.nextjs_build_id:
            L(f"- Next.js buildId: {r.nextjs_build_id}")
            L(f"  → data endpoint: {r.nextjs_data_endpoint}")
    else:
        L("- none")

    L("")
    L("## JSON-LD (schema.org)")
    if r.jsonld_blocks:
        L(f"- {r.jsonld_blocks} block(s)")
        if r.jsonld_types:
            L(f"- @types: {', '.join(r.jsonld_types)}")
    else:
        L("- none")

    L("")
    L("## DOM structure")
    for k, v in r.structure.items():
        L(f"- {k:<12}: {v}")

    L("")
    L("## Suspected API / XHR endpoints")
    if r.suspected_api_endpoints:
        for ep in r.suspected_api_endpoints:
            L(f"- {ep}")
    else:
        L("- none obvious")

    L("")
    L("## Anti-bot signals")
    if r.anti_bot_signals:
        for s in r.anti_bot_signals:
            L(f"- {s}")
        L("")
        L("> If fetch fails: try `af webscraper fetch <url> --impersonate firefox128`")
    else:
        L("- none detected")

    if r.notes:
        L("")
        L("## Notes")
        for n in r.notes:
            L(f"- {n}")

    mode = _recommend_mode(r)
    L("")
    L("## Suggested approach")
    L(f"→ `af webscraper scaffold {r.url} --mode {mode}`")
    L(f"  reason: {_recommend_reason(r, mode)}")
    L("  (scaffold will reuse this inspect's findings automatically)")

    return "\n".join(lines) + "\n"


# ── CLI: inspect ─────────────────────────────────────────────────────────────

@app.command()
def inspect(
    url: str = typer.Argument(..., help="URL to recon"),
    json_out: bool = typer.Option(
        False, "--json", help="Emit raw JSON instead of a markdown report"
    ),
    out: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Write output to path instead of stdout"
    ),
    no_sitemap: bool = typer.Option(
        False, "--no-sitemap", help="Skip sitemap probing (faster, less info)"
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Don't write cache (don't poison subsequent scaffold calls)"
    ),
):
    """Recon a URL before writing a scraper.

    Reports: status, redirects, robots.txt verdict + crawl delay, sitemaps
    + URL counts, RSS/Atom/JSON feeds, framework fingerprints, embedded
    JSON blobs with top-level keys, Next.js buildId → data endpoint,
    JSON-LD @types, suspected API/XHR endpoints, DOM structure counts,
    anti-bot signals. Results cached 1h for reuse by `scaffold`.
    """
    report = _inspect_url(url, probe_sitemaps=not no_sitemap)
    if not no_cache:
        _cache_write(report)

    if json_out:
        text = json.dumps(asdict(report), indent=2, ensure_ascii=False) + "\n"
    else:
        text = _render_report(report)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        typer.echo(f"[webscraper] wrote {out}", err=True)
    else:
        sys.stdout.write(text)


# ── CLI: fetch ───────────────────────────────────────────────────────────────

@app.command()
def fetch(
    url: str = typer.Argument(..., help="URL to GET"),
    out: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Save response body to this path"
    ),
    impersonate: Optional[str] = typer.Option(
        None, "--impersonate",
        help="Use curl_cffi with browser TLS fingerprint (e.g. firefox128, chrome124)",
    ),
    headers: bool = typer.Option(
        False, "--headers", help="Print response headers to stderr"
    ),
    status: bool = typer.Option(
        False, "--status", help="Print only status + final URL"
    ),
):
    """One-shot HTTP GET with real browser headers, HTTP/2, retries.
    Use --impersonate when plain httpx gets blocked."""
    if impersonate:
        _ensure("curl_cffi")
        from curl_cffi import requests as cr  # type: ignore
        try:
            r = cr.get(url, impersonate=impersonate, timeout=30, allow_redirects=True)
        except Exception as e:
            typer.echo(f"[webscraper] curl_cffi error: {e}", err=True)
            raise typer.Exit(1)
        final_url = getattr(r, "url", url)
        code = r.status_code
        hdrs = dict(r.headers)
        body = r.content
    else:
        import httpx  # type: ignore
        try:
            with httpx.Client(http2=True, headers=_HEADERS, follow_redirects=True, timeout=30.0) as c:
                r = c.get(url)
        except Exception as e:
            typer.echo(f"[webscraper] httpx error: {e}", err=True)
            raise typer.Exit(1)
        final_url = str(r.url)
        code = r.status_code
        hdrs = dict(r.headers)
        body = r.content

    if status:
        typer.echo(f"{code}  {final_url}")
        raise typer.Exit(0 if 200 <= code < 400 else 1)

    if headers:
        for k, v in hdrs.items():
            typer.echo(f"{k}: {v}", err=True)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)
        typer.echo(f"[webscraper] {code}  {len(body):,} bytes  -> {out}", err=True)
    else:
        sys.stdout.buffer.write(body)


# ── Scaffold templates ───────────────────────────────────────────────────────

_TPL_HTML = '''\
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx[http2]", "selectolax", "tenacity"]
# ///
"""Scrape {url} — plain HTML mode.

EDIT THE SELECTORS BELOW to match the page's actual markup.
{robots_note}"""
from __future__ import annotations
import httpx, json, random, time, pathlib, sys
from selectolax.parser import HTMLParser
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
HEADERS = {{"User-Agent": UA, "Accept-Language": "en-US,en;q=0.5"}}
DELAY_MIN, DELAY_MAX = {delay_min}, {delay_max}

@retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(initial=1, max=30))
def fetch(c, url):
    r = c.get(url, timeout=30.0); r.raise_for_status(); return r

def parse(html: str) -> list[dict]:
    tree = HTMLParser(html)
    rows = []
    # TODO: replace "article.item" + inner selectors with real ones.
    for node in tree.css("article.item"):
        rows.append({{
            "title": (node.css_first("h2") or node).text(strip=True),
            "url":   node.css_first("a").attributes.get("href") if node.css_first("a") else None,
        }})
    return rows

def main(start_url: str, out_path: str, max_pages: int = 500):
    out = pathlib.Path(out_path).open("a", encoding="utf-8")
    with httpx.Client(http2=True, headers=HEADERS, follow_redirects=True) as c:
        url = start_url
        for _ in range(max_pages):
            r = fetch(c, url)
            rows = parse(r.text)
            if not rows:
                break
            for row in rows:
                out.write(json.dumps(row, ensure_ascii=False) + "\\n")
            nxt = HTMLParser(r.text).css_first('a[rel="next"]')
            if not nxt:
                break
            url = str(httpx.URL(url).join(nxt.attributes["href"]))
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "{url}",
         sys.argv[2] if len(sys.argv) > 2 else "out.jsonl")
'''

_TPL_NEXTDATA = '''\
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx[http2]"]
# ///
"""Scrape {url} — Next.js __NEXT_DATA__ mode.

Edit `pluck()` to select the fields you want.
{next_keys_hint}"""
from __future__ import annotations
import httpx, json, re, sys, pathlib

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
NEXT_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
    re.DOTALL,
)

def next_data(html: str) -> dict:
    m = NEXT_RE.search(html)
    if not m:
        raise RuntimeError("__NEXT_DATA__ not found — page may have changed")
    return json.loads(m.group(1))

def pluck(data: dict) -> dict:
    # TODO: dive into data["props"]["pageProps"][...] to pick fields.
    return {{"top_level_keys": sorted(data.keys())}}

def main(url: str, out_path: str):
    with httpx.Client(http2=True, headers={{"User-Agent": UA}}, follow_redirects=True) as c:
        r = c.get(url, timeout=30.0); r.raise_for_status()
    data = next_data(r.text)
    row = pluck(data)
    pathlib.Path(out_path).write_text(json.dumps(row, indent=2, ensure_ascii=False))
    print(f"wrote {{out_path}}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "{url}",
         sys.argv[2] if len(sys.argv) > 2 else "out.json")
'''

_TPL_JSONLD = '''\
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx[http2]", "selectolax"]
# ///
"""Scrape {url} — JSON-LD (schema.org) mode.

Pulls every <script type="application/ld+json"> block, decodes it, and
flattens @graph if present. KEEP_TYPES pre-filled from inspect.
"""
from __future__ import annotations
import httpx, json, sys, pathlib
from selectolax.parser import HTMLParser

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

# Pre-filled from `af webscraper inspect`. Empty set means "keep everything".
KEEP_TYPES: set[str] = {keep_types}

def extract(html: str) -> list[dict]:
    tree = HTMLParser(html)
    out = []
    for node in tree.css('script[type="application/ld+json"]'):
        txt = node.text()
        if not txt: continue
        try:
            data = json.loads(txt)
        except json.JSONDecodeError:
            continue
        entries = data if isinstance(data, list) else [data]
        extra = []
        for e in entries:
            if isinstance(e, dict) and isinstance(e.get("@graph"), list):
                extra.extend(e["@graph"])
        for e in entries + extra:
            if not isinstance(e, dict): continue
            t = e.get("@type")
            if KEEP_TYPES and not (t in KEEP_TYPES or (isinstance(t, list) and set(t) & KEEP_TYPES)):
                continue
            out.append(e)
    return out

def main(url: str, out_path: str):
    with httpx.Client(http2=True, headers={{"User-Agent": UA}}, follow_redirects=True) as c:
        r = c.get(url, timeout=30.0); r.raise_for_status()
    rows = extract(r.text)
    with pathlib.Path(out_path).open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\\n")
    print(f"wrote {{len(rows)}} row(s) to {{out_path}}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "{url}",
         sys.argv[2] if len(sys.argv) > 2 else "out.jsonl")
'''

_TPL_ARTICLE = '''\
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx[http2]", "trafilatura"]
# ///
"""Scrape {url} — article / prose extraction mode.

trafilatura handles title, author, date, body, and boilerplate removal.
"""
from __future__ import annotations
import httpx, sys, pathlib
import trafilatura

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

def main(url: str, out_path: str):
    with httpx.Client(http2=True, headers={{"User-Agent": UA}}, follow_redirects=True) as c:
        r = c.get(url, timeout=30.0); r.raise_for_status()
    md = trafilatura.extract(
        r.text, url=url,
        include_links=False, include_images=False,
        output_format="markdown", with_metadata=True,
    )
    if not md:
        print("trafilatura returned nothing — page may not be an article", file=sys.stderr)
        sys.exit(1)
    pathlib.Path(out_path).write_text(md, encoding="utf-8")
    print(f"wrote {{out_path}}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "{url}",
         sys.argv[2] if len(sys.argv) > 2 else "out.md")
'''

_TPL_API = '''\
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx[http2]"]
# ///
"""Scrape {url} — direct JSON endpoint mode.

API_URL pre-filled from inspect. Refine params/path if needed.
{other_endpoints}"""
from __future__ import annotations
import httpx, json, sys, pathlib, time, random

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

API_URL = "{api_url}"

def fetch_page(c: httpx.Client, page: int) -> list[dict]:
    r = c.get(API_URL, params={{"page": page}}, timeout=30.0)
    r.raise_for_status()
    data = r.json()
    # TODO: adjust the path below based on the real response shape.
    if isinstance(data, list):
        return data
    return data.get("items") or data.get("data") or data.get("results") or [data]

def main(out_path: str, max_pages: int = 200):
    with httpx.Client(http2=True, headers={{"User-Agent": UA, "Accept": "application/json"}},
                      follow_redirects=True) as c:
        out = pathlib.Path(out_path).open("a", encoding="utf-8")
        for page in range(1, max_pages + 1):
            rows = fetch_page(c, page)
            if not rows:
                break
            for row in rows:
                out.write(json.dumps(row, ensure_ascii=False) + "\\n")
            time.sleep(random.uniform(0.3, 1.0))
    print(f"wrote to {{out_path}}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out.jsonl")
'''


_SCAFFOLD_MODES = ("html", "nextdata", "jsonld", "article", "api")


def _slugify(url: str) -> str:
    host = urlparse(url).netloc.replace("www.", "").replace(".", "_")
    return re.sub(r"[^a-zA-Z0-9_]+", "_", host) or "site"


def _render_scaffold(mode: str, url: str, report: Optional[InspectReport]) -> str:
    """Produce scaffold text for `mode`, pre-filling from cached inspect report."""
    if mode == "html":
        delay_min, delay_max = 0.8, 2.2
        robots_note = ""
        if report and report.robots_crawl_delay:
            delay_min = max(delay_min, float(report.robots_crawl_delay))
            delay_max = max(delay_max, delay_min + 1.0)
            robots_note = f"\nrobots.txt requests crawl-delay={report.robots_crawl_delay}s — DELAY_* respects it.\n"
        return _TPL_HTML.format(
            url=url, delay_min=delay_min, delay_max=delay_max, robots_note=robots_note,
        )

    if mode == "nextdata":
        hint = ""
        if report:
            for blob in report.embedded_json:
                if blob.get("name") == "__NEXT_DATA__" and blob.get("top_level_keys"):
                    hint = (
                        f"\ntop-level keys from inspect: "
                        f"{blob['top_level_keys']}\n"
                        f"props.pageProps is where the real data usually lives.\n"
                    )
                    break
        return _TPL_NEXTDATA.format(url=url, next_keys_hint=hint)

    if mode == "jsonld":
        if report and report.jsonld_types:
            keep = "{" + ", ".join(f'"{t}"' for t in report.jsonld_types) + "}"
        else:
            keep = "set()"
        return _TPL_JSONLD.format(url=url, keep_types=keep)

    if mode == "article":
        return _TPL_ARTICLE.format(url=url)

    if mode == "api":
        api_url = url
        other_endpoints = ""
        if report:
            if report.nextjs_data_endpoint:
                api_url = report.nextjs_data_endpoint
                other_endpoints = "\nSource: Next.js pages-router /_next/data/<buildId>/... endpoint.\n"
            elif report.suspected_api_endpoints:
                # pick first absolute-ish endpoint
                ep = report.suspected_api_endpoints[0]
                if ep.startswith("/"):
                    parsed = urlparse(url)
                    api_url = f"{parsed.scheme}://{parsed.netloc}{ep}"
                elif ep.startswith("http"):
                    api_url = ep
                if len(report.suspected_api_endpoints) > 1:
                    rest = "\n# Other endpoints sniffed:\n" + "\n".join(
                        f"#   {e}" for e in report.suspected_api_endpoints[1:10]
                    ) + "\n"
                    other_endpoints = rest
        return _TPL_API.format(url=url, api_url=api_url, other_endpoints=other_endpoints)

    raise ValueError(f"unknown mode: {mode}")


@app.command()
def scaffold(
    url: str = typer.Argument(..., help="Target URL"),
    mode: Optional[str] = typer.Option(
        None, "--mode", "-m",
        help=f"Data source mode: {', '.join(_SCAFFOLD_MODES)}. Auto-picks from inspect if omitted.",
    ),
    out: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Output path (default: ./scrape_<slug>.py)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file"),
    fresh: bool = typer.Option(
        False, "--fresh", help="Re-run inspect even if cache is fresh"
    ),
    no_inspect: bool = typer.Option(
        False, "--no-inspect", help="Skip inspect. Template is fully generic (and --mode is required)"
    ),
):
    """Write a ready-to-edit `uv run` scraper script for URL.

    Auto-runs `inspect` (unless --no-inspect) and pre-fills the template
    with the results: JSON-LD @types, Next.js data-endpoint URL, sniffed
    API paths, robots.txt crawl-delay, etc. Runs inspect only if cache
    is missing or stale (>1h)."""
    report: Optional[InspectReport] = None
    if not no_inspect:
        if not fresh:
            report = _cache_read(url)
        if report is None:
            typer.echo(f"[webscraper] running inspect {url}...", err=True)
            report = _inspect_url(url)
            _cache_write(report)

    if mode is None:
        if report is None:
            typer.echo(
                "[webscraper] --mode required when --no-inspect is set",
                err=True,
            )
            raise typer.Exit(1)
        mode = _recommend_mode(report)
        typer.echo(f"[webscraper] auto-picked mode: {mode}", err=True)

    if mode not in _SCAFFOLD_MODES:
        typer.echo(
            f"[webscraper] unknown --mode {mode!r}. "
            f"Choose from: {', '.join(_SCAFFOLD_MODES)}",
            err=True,
        )
        raise typer.Exit(1)

    out_path = out or Path(f"scrape_{_slugify(url)}.py")
    if out_path.exists() and not force:
        typer.echo(
            f"[webscraper] {out_path} already exists — pass --force to overwrite",
            err=True,
        )
        raise typer.Exit(1)

    content = _render_scaffold(mode, url, report)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    out_path.chmod(0o755)
    typer.echo(f"[webscraper] wrote {out_path}  (mode={mode})")
    typer.echo(f"  edit the TODOs, then run: ./{out_path.name}")


# ── CLI: cache ───────────────────────────────────────────────────────────────

cache_app = typer.Typer(help="Inspect-result cache management.")
app.add_typer(cache_app, name="cache")


@cache_app.command("path")
def cache_path_cmd(url: str = typer.Argument(..., help="URL to look up")):
    """Print the cache path for URL."""
    typer.echo(str(_cache_path(url)))


@cache_app.command("show")
def cache_show_cmd(url: str = typer.Argument(..., help="URL to look up")):
    """Print cached inspect JSON for URL, if any."""
    p = _cache_path(url)
    if not p.exists():
        typer.echo(f"[webscraper] no cache at {p}", err=True)
        raise typer.Exit(1)
    sys.stdout.write(p.read_text())


@cache_app.command("clear")
def cache_clear_cmd(
    url: Optional[str] = typer.Argument(None, help="URL to clear (all if omitted)"),
):
    """Delete cache entry for URL, or all entries."""
    if url:
        p = _cache_path(url)
        if p.exists():
            p.unlink()
            typer.echo(f"[webscraper] cleared {p}")
        else:
            typer.echo(f"[webscraper] no cache at {p}", err=True)
    else:
        d = _cache_dir()
        n = 0
        for f in d.glob("*.json"):
            f.unlink()
            n += 1
        typer.echo(f"[webscraper] cleared {n} entries from {d}")
