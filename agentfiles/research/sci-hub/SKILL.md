---
name: sci-hub
description: >
  Use when downloading academic papers, journal articles, or research papers by
  title, DOI, or URL. Downloads via Sci-Hub (sci-hub.st) using curl, with
  browser fallback if curl is blocked.
---

Download research papers via Sci-Hub. URL pattern: `https://sci-hub.st/{DOI}`
For arXiv papers, skip Sci-Hub entirely — direct PDF download always works.

## Workflow

```
1. Find DOI  →  2. curl download  →  3. verify PDF  →  4. rename + move
```

---

## Step 1 — Find the DOI

If user provides DOI directly → skip to step 2.

DOIs always start with `10.` (e.g. `10.1038/nature12345`)

**Search CrossRef API (no auth needed):**
```bash
curl -s "https://api.crossref.org/works?query=TITLE+KEYWORDS+HERE&rows=5" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data['message']['items']:
    doi = item.get('DOI', '?')
    title = item.get('title', ['?'])[0][:80]
    year = item.get('published', {}).get('date-parts', [['']])[0][0]
    authors = [a.get('family','') for a in item.get('author',[])[:2]]
    print(f'{doi} | {year} | {\" & \".join(authors)} | {title}')
"
```

Pick correct DOI. If ambiguous, confirm with user before downloading.

---

## Step 2 — Download

### Primary: curl

```bash
DOI="10.1038/nature12345"
curl -L \
  -A "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0" \
  --retry 3 --retry-delay 2 \
  -o "/tmp/paper.pdf" \
  "https://sci-hub.st/${DOI}"
```

### If curl returns HTML (Sci-Hub shows a page instead of direct PDF)

Extract the embedded PDF URL:
```bash
PDF_URL=$(curl -s \
  -A "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0" \
  "https://sci-hub.st/${DOI}" \
  | grep -oP '(?<=src=")[^"]*\.pdf[^"]*' | head -1)

# If URL is protocol-relative (//...)
PDF_URL="https:${PDF_URL}"

curl -L -A "Mozilla/5.0 ..." --retry 3 -o "/tmp/paper.pdf" "${PDF_URL}"
```

### Browser fallback (if curl blocked / captcha)

Use foxpilot MCP:

```
go(url="https://sci-hub.st/{DOI}")
screenshot(path="/tmp/scihub.png")   # Read tool to see page state

pdf_url = js(expression="""
  document.querySelector('iframe#pdf')?.src ||
  document.querySelector('embed[type*=pdf]')?.src ||
  document.querySelector('a[href*=pdf]')?.href
""")
```

Then curl the PDF URL (prepend `https:` if protocol-relative `//...`).

---

## Step 3 — Verify download

```bash
file /tmp/paper.pdf          # must say "PDF document"
ls -lh /tmp/paper.pdf        # papers are usually 1–20MB
```

If file is tiny or HTML → Sci-Hub returned captcha/error. Try browser fallback or alternate domain.

**Alternate Sci-Hub domains** (same DOI path works on all):
- `sci-hub.st` (primary)
- `sci-hub.se`
- `sci-hub.ru`

---

## Step 4 — Rename and move

```bash
# Suggested: AuthorYear_ShortTitle.pdf
mv /tmp/paper.pdf ~/papers/LeCun2015_DeepLearning.pdf
```

Ask user for destination if not specified. Common locations:
- `~/papers/`
- `~/Documents/papers/`
- `~/research/`

```bash
mkdir -p ~/papers
mv /tmp/paper.pdf ~/papers/"${FILENAME}"
echo "Saved: ~/papers/${FILENAME}"
```

---

## arXiv (no Sci-Hub needed)

arXiv papers are always free. Direct PDF download:

```bash
# From arXiv ID (e.g. 2301.07041 or arxiv.org/abs/2301.07041)
curl -L -o "/tmp/paper.pdf" "https://arxiv.org/pdf/2301.07041"
```

---

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Got HTML not PDF | Check with `file`, extract PDF URL from iframe src |
| Wrong DOI | Verify via CrossRef before downloading |
| sci-hub.st down | Try sci-hub.se or sci-hub.ru — same path |
| Protocol-relative URL (`//cdn...`) | Prepend `https:` |
| Not renaming file | Use `AuthorYear_Title.pdf` before moving |
| arXiv paper via Sci-Hub | Use `arxiv.org/pdf/ID` directly — always works |
