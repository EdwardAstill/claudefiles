---
name: web-scraper
description: >
  Use for pure-HTTP scraping when data is reachable without a real browser.
  Trigger phrases: "scrape this site", "pull data from X", "crawl this listing",
  "extract all the articles from Y", "build a dataset from this website", "hit
  their API", "download everything under this URL", "paginate through these
  pages", "parse the JSON-LD", "grab the sitemap and fetch each page". Runs via
  the standalone `webscraper` CLI (external repo EdwardAstill/webscraper):
  framework fingerprinting, API endpoint discovery, robots.txt, rate-limited
  fetching, JSONL/CSV/SQLite output. Do NOT use for JS-rendered pages that
  only populate after client-side execution (use browser-control) or for
  converting HTML/PDF files already on disk (use file-converter).
---

# web-scraper

Pure-HTTP scraping. Goal: get the minimum viable request that returns the
data, parse it cheaply, repeat politely.

The CLI used by this skill, `webscraper`, lives in a standalone repo:
[`EdwardAstill/webscraper`](https://github.com/EdwardAstill/webscraper).
Install with:

```bash
uv pip install -e ~/projects/webscraper    # if cloned locally
# or once published:
# pipx install webscraper
```

## When to use this skill

**Use** when the user wants data from a website and it's present in the raw
HTML, an embedded JSON blob, a JSON-LD script, a declared RSS/Atom feed, a
sitemap, or a discoverable JSON API endpoint.

**Do not use** when:
- The page only renders data after client-side JS runs and no API backs it →
  `browser-control` (foxpilot) instead.
- The user already has the HTML/PDF on disk and just needs markdown →
  `file-converter`.
- The user wants to drive a full browser session → `browser-control`.

## Fast path — `webscraper`

Standalone CLI. **Always start here.** Three subcommands cover 90% of scraping work.

```bash
webscraper inspect <url>          # Recon. Cached 1h. Recommends --mode.
webscraper scaffold <url>         # Generates scrape_<host>.py.
                                   # Auto-picks mode from cached inspect.
webscraper fetch <url>            # One-off GET with real browser headers.
```

### What `inspect` reports

- HTTP: status, redirects, content-type, HTTP/2 vs 1.1, response size + timing
- `robots.txt`: allowed/disallowed verdict, `Crawl-delay`, and `Sitemap:` lines
- Sitemaps: probed from robots.txt (or `/sitemap.xml` fallback), URL counts per partition
- Feeds: `<link rel="alternate">` RSS / Atom / JSON Feed
- Framework fingerprints: Next.js (pages + app), Nuxt, Gatsby, SvelteKit, Remix, Astro, Hugo, Jekyll, Eleventy, Shopify, WordPress, WooCommerce, Wix, Squarespace, Webflow, Ghost, Substack, Medium, Apollo GraphQL, Redux
- Embedded JSON: `__NEXT_DATA__`, `__INITIAL_STATE__`, `__NUXT__`, `__APOLLO_STATE__`, `__PRELOADED_STATE__` with top-level keys
- **Next.js buildId → `/_next/data/<buildId>/<path>.json` endpoint** (often the cleanest scrape target)
- JSON-LD: block count + all `@type` values
- Suspected API/XHR endpoints (regex sniff of `fetch()` / `axios.get()` calls)
- DOM structure counts (article, table, form, image, nav, rel=next)
- Anti-bot signals: Cloudflare, DataDome, PerimeterX, Akamai, Incapsula, reCAPTCHA, hCaptcha
- Recommended `--mode` for scaffold, with reasoning

### What `scaffold` does

Generates `scrape_<host>.py` — a PEP 723 `uv run` script with inline deps.
Pre-fills from the cached inspect:

| Mode       | What gets pre-filled                                               |
|------------|--------------------------------------------------------------------|
| `html`     | `DELAY_MIN/MAX` set from `robots.txt` crawl-delay                  |
| `nextdata` | top-level keys from `__NEXT_DATA__` listed as a hint in `pluck()`  |
| `jsonld`   | `KEEP_TYPES = {...}` populated from detected `@type` values        |
| `api`      | `API_URL` set to Next.js `/_next/data/.../index.json` or sniffed `/api/...` endpoint; other endpoints listed as comments |
| `article`  | URL only (trafilatura does the heavy lifting)                      |

Scaffold auto-runs `inspect` if no cache exists. Modes: `html`, `nextdata`,
`jsonld`, `article`, `api`. Omit `--mode` to auto-pick from cached recommendation.

### Worked example

```bash
$ webscraper inspect https://stripe.com
...
## Sitemaps
- index   https://stripe.com/sitemap/sitemap.xml
    → https://stripe.com/sitemap/partition-0.xml
## Embedded JSON state
- __NEXT_DATA__  (229,447 bytes) — top keys: ['buildId', 'props', ...]
- Next.js buildId: m0ZbeGYPrzF...
  → data endpoint: https://stripe.com/_next/data/m0ZbeGYPrzF.../au.json
## JSON-LD (schema.org)
- @types: Organization, WebSite
## Suggested approach
→ `webscraper scaffold https://stripe.com --mode api`
  reason: Direct JSON endpoint available — hit it, skip HTML entirely.

$ webscraper scaffold https://stripe.com            # reuses cache
[webscraper] auto-picked mode: api
[webscraper] wrote scrape_stripe_com.py  (mode=api)

$ head -15 scrape_stripe_com.py
...
API_URL = "https://stripe.com/_next/data/m0ZbeGYPrzF.../au.json"
...
```

Agent job: edit the TODOs (selectors, response path, output file), run it.

### Cache

- Location: `$XDG_CACHE_HOME/webscraper/<sha256>.json` (default `~/.cache/webscraper/`)
- TTL: 1 hour
- Management: `webscraper cache show|clear|path <url>`
- `scaffold --fresh` forces a re-inspect
- `inspect --no-cache` inspects without writing to cache

### When to drop down to hand-written code

Skip the scaffold and write the script yourself if:
- GraphQL with signed queries, or a non-trivial custom cursor format.
- Multi-step auth (login form → session cookie → protected pages).
- Async concurrency needed (hundreds of URLs in parallel).
- Scraping dozens of related but distinct URL patterns — one script, not N.

## Stack reference

| Lib | Role | Why |
|-----|------|-----|
| `httpx[http2]` | HTTP client, HTTP/2, cookies, sessions | `requests` is in maintenance mode — no HTTP/2, no async |
| `selectolax` | HTML → nodes via CSS selectors | 10–30× faster than BeautifulSoup (lexbor-backed) |
| `trafilatura` | Article / main-content extraction | Benchmark-leading prose extraction |
| `tenacity` | Retry with exponential backoff + jitter | One decorator, done |
| `curl_cffi` | TLS/JA3 browser fingerprint bypass | Only install when httpx gets 403'd |

CLI helpers already on system: `curl`, `jq`.

## Pitfalls

- **Brotli trap.** Do not advertise `Accept-Encoding: br` unless the `brotli`
  package is installed — httpx can't decode it and you get binary garbage in
  `r.text`. Stick to `gzip, deflate`.
- **Writing the scraper before inspecting.** Half the time an API endpoint
  or JSON-LD block saves 200 lines of parsing. Always run `inspect` first.
- **Default User-Agent.** Sites block `python-httpx/…` UAs within seconds.
  Use a real browser UA.
- **Ignoring HTTP/2.** Some sites refuse HTTP/1.1. Always `http2=True`.
- **No inter-request delay.** Fastest way to get IP-banned.
- **Brittle selectors.** Prefer `data-*` attributes, `itemprop`, ARIA roles
  over auto-generated class names like `.sc-a8f92b_3`.
- **Re-fetching while iterating.** Save one page to disk, develop selectors
  against the local copy, then run the real crawl.
- **Scraping prose when JSON-LD exists.** Products, articles, recipes, events
  often ship clean `application/ld+json` blocks. Always check `@types` in
  inspect output first.
- **`r.content.decode()` manually.** Trust `r.text` — httpx decodes charset
  from headers already.

## Anti-bot ladder (escalate only when needed)

Stop as soon as a rung works.

1. Real browser `User-Agent` + `Accept-Language` (default in scaffold).
2. HTTP/2 (default in scaffold).
3. Keep a single `httpx.Client` alive — cookies + connection reuse matter.
4. Random 0.8–2.5 s delay (or honor `robots.txt` crawl-delay).
5. `Referer` header pointing to the site's own homepage.
6. **`curl_cffi` TLS impersonation** — one line swap:
   ```python
   from curl_cffi import requests
   r = requests.get(url, impersonate="firefox128")
   ```
   `webscraper fetch <url> --impersonate firefox128` uses this.
   Cloudflare, Akamai, DataDome often fall to this alone.
7. If still blocked, the data almost certainly needs JS → switch to
   `browser-control`.

Skip: residential-proxy rotation (usually a sign the approach is wrong or
the scraping violates ToS).

## Etiquette

- Respect `robots.txt` `Disallow` rules for your UA.
- Obey `Crawl-delay` (scaffold's `html` mode already does).
- Check the site's Terms of Service for scraping prohibitions.
- Identify yourself in UA where reasonable (`MyBot/1.0 (+contact)`).
- Cache locally during development — don't re-hit the server while iterating.

## Handoff chain

- HTML or PDF needs conversion to markdown → `file-converter`.
- Page needs JS execution before scraping → `browser-control` (foxpilot).
- Summarise scraped prose → `note-taker` or `knowledge-base`.
- Answer a question set from scraped corpus → `test-taker`.

## Source

The `webscraper` CLI is maintained in its own repo:
[`EdwardAstill/webscraper`](https://github.com/EdwardAstill/webscraper).
Report bugs or request features there.
