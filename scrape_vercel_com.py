#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx[http2]", "selectolax"]
# ///
"""Scrape https://vercel.com — JSON-LD (schema.org) mode.

Pulls every <script type="application/ld+json"> block, decodes it, and
flattens @graph if present. KEEP_TYPES pre-filled from inspect.
"""
from __future__ import annotations
import httpx, json, sys, pathlib
from selectolax.parser import HTMLParser

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

# Pre-filled from `af webscraper inspect`. Empty set means "keep everything".
KEEP_TYPES: set[str] = {"SoftwareApplication"}

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
    with httpx.Client(http2=True, headers={"User-Agent": UA}, follow_redirects=True) as c:
        r = c.get(url, timeout=30.0); r.raise_for_status()
    rows = extract(r.text)
    with pathlib.Path(out_path).open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} row(s) to {out_path}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "https://vercel.com",
         sys.argv[2] if len(sys.argv) > 2 else "out.jsonl")
