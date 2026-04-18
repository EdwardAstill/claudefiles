"""Regression tests for af.webscraper — pure-unit, no network."""
from __future__ import annotations

import ast
import json
import time
from dataclasses import asdict
from pathlib import Path

import pytest

from af import webscraper as ws
from af.webscraper import (
    InspectReport,
    _API_ENDPOINT,
    _ANTIBOT_FINGERPRINTS,
    _EMBEDDED_JSON_TARGETS,
    _FRAMEWORK_FINGERPRINTS,
    _cache_path,
    _cache_read,
    _cache_write,
    _detect_feeds,
    _extract_nextjs_data,
    _parse_robots,
    _recommend_mode,
    _render_scaffold,
    _SCAFFOLD_MODES,
)


# ── Framework fingerprints ───────────────────────────────────────────────────

@pytest.mark.parametrize("html,expected", [
    ('<script id="__NEXT_DATA__" type="application/json">{"x":1}</script>', "Next.js (pages)"),
    ('<script>self.__next_f=[]</script><link href="/_next/static/chunks/abc.js">', "Next.js (app)"),
    ('<div>window.__NUXT__ = {}</div>', "Nuxt"),
    ('<body><div id="___gatsby"></div></body>', "Gatsby"),
    ('<html><body>Shopify.theme = {}</body></html>', "Shopify"),
    ('<head><meta name="generator" content="WordPress 6.4"></head>', "WordPress"),
    ('<script>window.__APOLLO_STATE__ = {"x":1}</script>', "Apollo GraphQL"),
    ('<meta name="generator" content="Hugo 0.120">', "Hugo"),
    ('<astro-island component-url="/x.js"></astro-island>', "Astro"),
    ('<body>substackcdn.com/image/abc</body>', "Substack"),
])
def test_framework_detection(html: str, expected: str):
    matches = [name for name, pat in _FRAMEWORK_FINGERPRINTS if pat.search(html)]
    assert expected in matches, f"expected {expected} in {matches}"


# ── Anti-bot fingerprints ────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("cf-ray: abc123", "Cloudflare"),
    ("Set-Cookie: __cf_bm=xyz", "Cloudflare"),
    ("datadome=abc", "DataDome"),
    ("<script src='recaptcha/api.js'></script>", "reCAPTCHA"),
    ("<script src='hcaptcha.com/1/api.js'></script>", "hCaptcha"),
    ("<title>Just a moment...</title>", "Generic challenge"),
    ("_abck cookie", "Akamai Bot Manager"),
    ("incap_ses=abc", "Incapsula / Imperva"),
])
def test_antibot_detection(text: str, expected: str):
    matches = [name for name, pat in _ANTIBOT_FINGERPRINTS if pat.search(text)]
    assert expected in matches, f"expected {expected} in {matches}"


# ── __NEXT_DATA__ buildId extraction ─────────────────────────────────────────

def test_nextjs_buildid_and_endpoint():
    html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"buildId":"XyZ123","page":"/products/[slug]","props":{}}'
        '</script></body></html>'
    )
    build_id, endpoint = _extract_nextjs_data(html, "https://shop.example.com/products/cool-shirt")
    assert build_id == "XyZ123"
    assert endpoint == "https://shop.example.com/_next/data/XyZ123/products/cool-shirt.json"


def test_nextjs_buildid_root_url():
    html = '<script id="__NEXT_DATA__" type="application/json">{"buildId":"b1"}</script>'
    _, endpoint = _extract_nextjs_data(html, "https://x.com/")
    assert endpoint == "https://x.com/_next/data/b1/index.json"


def test_nextjs_buildid_missing_returns_none():
    assert _extract_nextjs_data("<html>no next here</html>", "https://x.com/") == (None, None)


def test_nextjs_buildid_unparseable_json():
    html = '<script id="__NEXT_DATA__" type="application/json">{broken</script>'
    assert _extract_nextjs_data(html, "https://x.com/") == (None, None)


# ── __NEXT_DATA__ blob regex + top-level keys ────────────────────────────────

def test_embedded_json_next_data_extracts_keys():
    raw = json.dumps({"buildId": "b", "props": {}, "page": "/", "query": {}})
    html = f'<script id="__NEXT_DATA__" type="application/json">{raw}</script>'
    _, pat = next(e for e in _EMBEDDED_JSON_TARGETS if e[0] == "__NEXT_DATA__")
    m = pat.search(html)
    assert m
    data = json.loads(m.group(1))
    assert set(data.keys()) == {"buildId", "props", "page", "query"}


# ── API endpoint regex ──────────────────────────────────────────────────────

def test_api_endpoint_regex_picks_up_api_paths():
    html = '''
      <script>
        fetch("/api/products?page=1")
        axios.get("/api/v2/users")
        "/graphql"
        const url = "/public/static.js"  /* should NOT match */
      </script>
    '''
    hits = set()
    for m in _API_ENDPOINT.finditer(html):
        hit = (m.group(1) or m.group(0)).strip('"\' \t\n\\')
        if "api" in hit or "graphql" in hit:
            hits.add(hit)
    assert "/api/products?page=1" in hits
    assert "/api/v2/users" in hits
    assert any("graphql" in h for h in hits)
    assert not any("static.js" in h for h in hits)


def test_api_endpoint_regex_no_false_positive_on_ordinary_strings():
    html = '<a href="/about">About</a><img src="/logo.png">'
    hits = list(_API_ENDPOINT.finditer(html))
    assert hits == []


# ── Mode recommendation priority ────────────────────────────────────────────

def test_recommend_prefers_nextjs_data_endpoint_over_nextdata_blob():
    r = InspectReport(
        url="x", final_url="x", status=200, http_version="HTTP/2",
        content_type="text/html", bytes_downloaded=0, elapsed_ms=0,
    )
    r.embedded_json = [{"name": "__NEXT_DATA__", "size_bytes": 100, "top_level_keys": ["buildId"]}]
    r.nextjs_data_endpoint = "https://x/_next/data/b/page.json"
    assert _recommend_mode(r) == "api"


def test_recommend_nextdata_when_blob_but_no_endpoint():
    r = InspectReport(
        url="x", final_url="x", status=200, http_version="HTTP/2",
        content_type="text/html", bytes_downloaded=0, elapsed_ms=0,
    )
    r.embedded_json = [{"name": "__NEXT_DATA__", "size_bytes": 100}]
    assert _recommend_mode(r) == "nextdata"


def test_recommend_jsonld_when_types_present():
    r = InspectReport(
        url="x", final_url="x", status=200, http_version="HTTP/2",
        content_type="text/html", bytes_downloaded=0, elapsed_ms=0,
    )
    r.jsonld_blocks = 2
    r.jsonld_types = ["Product", "BreadcrumbList"]
    assert _recommend_mode(r) == "jsonld"


def test_recommend_article_when_single_article_tag():
    r = InspectReport(
        url="x", final_url="x", status=200, http_version="HTTP/2",
        content_type="text/html", bytes_downloaded=0, elapsed_ms=0,
    )
    r.structure = {"article": 1}
    assert _recommend_mode(r) == "article"


def test_recommend_html_fallback():
    r = InspectReport(
        url="x", final_url="x", status=200, http_version="HTTP/2",
        content_type="text/html", bytes_downloaded=0, elapsed_ms=0,
    )
    assert _recommend_mode(r) == "html"


# ── Scaffold template validity ──────────────────────────────────────────────

def _make_report(**overrides) -> InspectReport:
    r = InspectReport(
        url="https://example.com/thing",
        final_url="https://example.com/thing",
        status=200, http_version="HTTP/2",
        content_type="text/html", bytes_downloaded=1234, elapsed_ms=100,
    )
    for k, v in overrides.items():
        setattr(r, k, v)
    return r


@pytest.mark.parametrize("mode", _SCAFFOLD_MODES)
def test_scaffold_every_mode_is_valid_python(mode: str):
    src = _render_scaffold(mode, "https://example.com/thing", None)
    ast.parse(src)


@pytest.mark.parametrize("mode", _SCAFFOLD_MODES)
def test_scaffold_every_mode_with_report_is_valid_python(mode: str):
    r = _make_report(
        jsonld_types=["Product", "BreadcrumbList"],
        robots_crawl_delay=5.0,
        suspected_api_endpoints=["/api/v2/products", "/api/v2/reviews"],
        nextjs_build_id="abc",
        nextjs_data_endpoint="https://example.com/_next/data/abc/thing.json",
        embedded_json=[{"name": "__NEXT_DATA__", "size_bytes": 500, "top_level_keys": ["buildId", "props"]}],
    )
    src = _render_scaffold(mode, r.url, r)
    ast.parse(src)


def test_scaffold_jsonld_prefills_keep_types():
    r = _make_report(jsonld_types=["Product", "Offer"])
    src = _render_scaffold("jsonld", r.url, r)
    assert 'KEEP_TYPES: set[str] = {"Product", "Offer"}' in src


def test_scaffold_jsonld_empty_types_keeps_all():
    src = _render_scaffold("jsonld", "https://x.com", None)
    assert "KEEP_TYPES: set[str] = set()" in src


def test_scaffold_api_uses_nextjs_data_endpoint_first():
    r = _make_report(
        nextjs_data_endpoint="https://shop.example.com/_next/data/b1/p.json",
        suspected_api_endpoints=["/api/other"],
    )
    src = _render_scaffold("api", r.url, r)
    assert 'API_URL = "https://shop.example.com/_next/data/b1/p.json"' in src


def test_scaffold_api_uses_sniffed_endpoint_when_no_nextjs():
    r = _make_report(suspected_api_endpoints=["/api/v2/products"])
    src = _render_scaffold("api", "https://site.com/catalog", r)
    assert 'API_URL = "https://site.com/api/v2/products"' in src


def test_scaffold_api_falls_back_to_input_url():
    src = _render_scaffold("api", "https://x.com", None)
    assert 'API_URL = "https://x.com"' in src


def test_scaffold_html_respects_crawl_delay():
    r = _make_report(robots_crawl_delay=10.0)
    src = _render_scaffold("html", r.url, r)
    assert "DELAY_MIN, DELAY_MAX = 10.0" in src


def test_scaffold_nextdata_includes_key_hint():
    r = _make_report(
        embedded_json=[{"name": "__NEXT_DATA__", "size_bytes": 100, "top_level_keys": ["buildId", "page", "props"]}]
    )
    src = _render_scaffold("nextdata", r.url, r)
    assert "buildId" in src  # hint was injected
    assert "props.pageProps" in src


# ── Feeds detection ─────────────────────────────────────────────────────────

def test_detect_feeds():
    from selectolax.parser import HTMLParser
    html = '''
      <head>
        <link rel="alternate" type="application/rss+xml" title="Blog" href="/feed.xml">
        <link rel="alternate" type="application/atom+xml" href="https://example.com/atom.xml">
        <link rel="alternate" type="application/json" href="/feed.json" title="JSON Feed">
        <link rel="stylesheet" href="/x.css">
      </head>
    '''
    feeds = _detect_feeds(HTMLParser(html), "https://example.com/section/")
    urls = {f["url"]: f["kind"] for f in feeds}
    assert urls["https://example.com/feed.xml"] == "rss"
    assert urls["https://example.com/atom.xml"] == "atom"
    assert urls["https://example.com/feed.json"] == "json-feed"
    assert len(feeds) == 3


# ── Robots parsing ──────────────────────────────────────────────────────────

def test_parse_robots_sitemap_lines():
    text = """
User-agent: *
Disallow: /private/
Crawl-delay: 5
Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/news-sitemap.xml
"""
    allowed, delay, sitemaps = _parse_robots(text, "my-bot/1.0", "https://example.com/page")
    assert allowed is True
    assert sitemaps == [
        "https://example.com/sitemap.xml",
        "https://example.com/news-sitemap.xml",
    ]


def test_parse_robots_disallow():
    text = "User-agent: *\nDisallow: /private/"
    allowed, _, _ = _parse_robots(text, "my-bot/1.0", "https://x.com/private/secret")
    assert allowed is False


# ── Cache round-trip ────────────────────────────────────────────────────────

def test_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    r = _make_report(jsonld_types=["Article"], inspected_at=time.time())
    _cache_write(r)
    r2 = _cache_read(r.url)
    assert r2 is not None
    assert r2.url == r.url
    assert r2.jsonld_types == ["Article"]


def test_cache_read_returns_none_when_stale(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    r = _make_report(inspected_at=time.time() - 7200)  # 2h ago
    _cache_write(r)
    assert _cache_read(r.url) is None


def test_cache_read_returns_none_for_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert _cache_read("https://never-inspected.example") is None


def test_cache_path_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    p1 = _cache_path("https://x.com/a")
    p2 = _cache_path("https://x.com/a")
    p3 = _cache_path("https://x.com/b")
    assert p1 == p2
    assert p1 != p3
