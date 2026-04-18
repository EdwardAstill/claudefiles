---
name: youtube
description: >
  Use for anything YouTube: transcripts (single video, playlist, channel), audio
  extraction (WAV / MP3 / any ffmpeg format), clip trimming, channel listing,
  and LLM summarisation. Fully integrated as `af youtube <subcommand>` — no
  external wrapper needed. Chains cleanly into `note-taker`,
  `knowledge-base`, and `test-taker`.
---

# YouTube

All YouTube operations are built in as `af youtube`. Source lives in
`tools/python/src/af/youtube.py`. Runtime deps (`yt-dlp`,
`youtube-transcript-api`) lazy-install on first use; `ffmpeg` is required for
audio. No API key needed for transcripts or audio. `summary` uses Anthropic
if `ANTHROPIC_API_KEY` is set; otherwise falls through to an in-context
prompt the calling agent can answer.

## Subcommand map

| Command | Purpose |
|---------|---------|
| `af youtube transcript <url> [--out DIR] [--limit N]` | Video → `.txt`, playlist → folder of `.txt`, channel → bulk fetch recent videos |
| `af youtube audio <url> [--format mp3\|wav\|flac\|...] [--quality 0-9] [--start HH:MM:SS --end HH:MM:SS] [--embed-thumbnail] [--out DIR]` | Audio extraction + optional clip trim |
| `af youtube summary <url> [--out FILE] [--model ID] [--keep-transcript]` | Transcript → structured summary (Anthropic, or prompt-fallback) |
| `af youtube channel <@handle\|url> [--limit N]` | TSV list: `id   date   duration   title` |
| `af youtube playlists <@handle\|url> [--limit N]` | TSV list: `id   count   title` |

All commands accept any YouTube URL shape: `watch?v=`, `youtu.be/`,
`/shorts/`, `/embed/`, `/live/`, `/playlist?list=`, `/@handle`,
`/channel/UC…`, `/c/name`, `/user/name`, or bare `@handle`.

---

## Workflow

```
1. Classify the URL  →  2. Pick the right subcommand  →  3. Run from target dir  →  4. Verify
```

### Classification

| Input | Subcommand |
|-------|-----------|
| Single video URL | `transcript` / `audio` / `summary` |
| Playlist URL (`list=` only) | `transcript` (folder per playlist), `audio` (loop per entry) |
| Channel (`@handle`, `/channel/…`, etc.) | `transcript --limit N`, or `channel` for metadata only |
| Just want metadata | `channel` or `playlists` (no downloads) |
| Need timestamps in the summary | Use raw yt-dlp VTT path — `af youtube` strips timestamps |

### Target directory

All write commands default to CWD. Override with `--out`. Common destinations:

- `~/projects/knowledge/notes/transcripts/` (then chain into `knowledge-base`)
- `/tmp/yt-<slug>/` for scratch work
- The active project for in-repo research

Ask if the user hasn't said.

---

## Examples

**Transcript of one video:**

```bash
af youtube transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --out /tmp/yt
```

**Whole playlist:**

```bash
af youtube transcript "https://www.youtube.com/playlist?list=PLxxxx" --out ~/notes/talks
# Creates ~/notes/talks/<Playlist Title>/<video>.txt per entry
```

**Recent 20 videos from a channel:**

```bash
af youtube transcript "@veritasium" --limit 20 --out /tmp/veritasium
```

**MP3 audio (best VBR):**

```bash
af youtube audio "https://youtu.be/dQw4w9WgXcQ" --format mp3 --quality 0
```

**WAV for ASR:**

```bash
af youtube audio "<url>" --format wav --out /tmp/asr
```

**Trimmed clip:**

```bash
af youtube audio "<url>" --start 00:01:30 --end 00:02:45 --format mp3
```

**Music library style (metadata + thumbnail):**

```bash
af youtube audio "<url>" --format mp3 --embed-thumbnail
```

**Summary (Anthropic):**

```bash
export ANTHROPIC_API_KEY=...
af youtube summary "<url>" --out /tmp/summary.md
```

**Summary fallback (no key — print prompt for calling agent to answer):**

```bash
af youtube summary "<url>" --keep-transcript --out /tmp/ready-to-summarise.md
```

Then Read `/tmp/ready-to-summarise.md` and produce the summary inline.

**Channel inventory (metadata only, no downloads):**

```bash
af youtube channel "@veritasium" --limit 10
af youtube playlists "@veritasium"
```

---

## Verification

```bash
ls -lh *.txt                                           # transcripts: 1–100KB typical
ffprobe -v error -show_entries format=duration,bit_rate -of default=nw=1 <audio>
file <audio>                                            # "Audio file" / "WAVE audio" / "MPEG ADTS"
```

Zero-byte `.txt` = transcript disabled; move on. Tiny / truncated audio =
yt-dlp rate-limited — retry with `--quality 5` or add `--retries 5`.

---

## Chains into

| Goal | Next skill |
|------|-----------|
| Dense reference notes from transcripts | `note-taker` (LLM mode) |
| Feed into the personal KB | `knowledge-base` + `mks` |
| Answer a question set over transcripts | `test-taker` |
| Clean or strip before summary | `regex-expert` (`sd`) |

---

## Timestamps

`af youtube transcript` joins snippet text with spaces — no timestamps. If the
user needs them:

```bash
uv run --with yt-dlp yt-dlp --write-auto-subs --skip-download \
  --sub-lang en --sub-format vtt \
  -o "%(title)s.%(ext)s" "<url>"
```

Parse the VTT cues for `HH:MM:SS` anchors, then feed to the summary prompt.

---

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Invalid YouTube URL.` | URL not parseable | Check URL has `v=`, `youtu.be`, `/shorts/`, `/embed/`, or `/live/` |
| `TranscriptsDisabled` / `NoTranscriptFound` | Captions unavailable in any language | No recovery — log and skip. For audio-based videos, use the `audio` + ASR path |
| `VideoUnavailable` / private / age-gated | yt-dlp can't fetch metadata | Out of scope — suggest authenticated `yt-dlp --cookies-from-browser` |
| Playlist loop skips most entries | Many entries have no transcript | Expected — `SKIP <title>: <error>` per failure |
| Filename collisions | Two videos share sanitised title | Run from distinct `--out` per batch, or rename after |
| `ffmpeg not found` | System package missing | `pacman -S ffmpeg` / `apt install ffmpeg` / `brew install ffmpeg` |
| yt-dlp 403 / 429 | Rate-limited | Retry later, or bump `--quality` down, or add sleep with raw yt-dlp |
| WAV huge | Uncompressed — expected | Pick `--format mp3` unless ASR / editing needs uncompressed |
| Summary hallucinated / vague | Auto-captions garbled (noisy audio) | Use audio + proper ASR; warn user the transcript quality is low |

---

## Do not

- Do not scrape transcripts via `browser-control` when `af youtube` works — slower and fragile.
- Do not call the YouTube Data API v3 — this skill intentionally has no API key dependency.
- Do not feed raw transcripts into downstream LLM work without at least skimming one file first; auto-captions can be gibberish for music, accents, or heavy jargon.
- Do not default to WAV when MP3 will do — a 1-hour WAV is ~600 MB and will blow through context if Read into the conversation.
- Do not summarise a video you could not confirm has a usable transcript — surface the gap (transcripts disabled, ASR needed) rather than fabricating from the title.
- Do not re-download audio you already have on disk; check for `<title>.mp3` / `.wav` before invoking `audio`.
