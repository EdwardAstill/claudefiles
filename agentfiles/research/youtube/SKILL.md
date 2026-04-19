---
name: youtube
description: >
  Use for anything YouTube. Trigger phrases: "get the transcript of this video",
  "download this playlist", "rip audio from this YouTube link", "download the
  video", "grab the mp4", "save as mkv", "summarise this YouTube video", "find
  videos by artist X", "download as MP3", "transcribe the talk", "list videos
  on this channel", "clip from 1:30 to 2:45", "I only have the channel name,
  find the video". Covers search, transcripts (video / playlist / channel
  bulk), audio extraction (WAV / MP3 / any ffmpeg format), video download
  (MP4 / MKV / WebM), clip trimming, channel + playlist listings, and LLM
  summarisation via `yt-tool <subcommand>`. Do NOT use for arbitrary web
  video (use web-scraper or browser-control) or for converting a local media
  file you already have (use file-converter).
---

# YouTube

All YouTube operations run through the external [yt-tool](https://github.com/EdwardAstill/yt-tool)
CLI — `uv pip install -e ~/projects/yt-tool` or `pipx install yt-tool` once published.
Runtime deps (`yt-dlp`, `youtube-transcript-api`) lazy-install on first use;
`ffmpeg` is required for audio. No API key needed for transcripts or audio.
`summary` uses Anthropic if `ANTHROPIC_API_KEY` is set; otherwise falls
through to an in-context prompt the calling agent can answer.

## Subcommand map

| Command | Purpose |
|---------|---------|
| `yt-tool transcript <url> [--out DIR] [--limit N]` | Video → `.txt`, playlist → folder of `.txt`, channel → bulk fetch recent videos |
| `yt-tool audio <url> [--format mp3\|wav\|flac\|...] [--quality 0-9] [--start HH:MM:SS --end HH:MM:SS] [--embed-thumbnail] [--out DIR]` | Audio extraction + optional clip trim |
| `yt-tool video <url> [--format mp4\|mkv\|webm] [--quality 720\|1080\|'bestvideo[h<=720]+bestaudio'] [--start --end] [--subs] [--embed-thumbnail]` | Video download (MP4 default) + optional clip / subs |
| `yt-tool summary <url> [--out FILE] [--model ID] [--keep-transcript]` | Transcript → structured summary (Anthropic, or prompt-fallback) |
| `yt-tool channel <@handle\|url> [--limit N]` | TSV list: `id   date   duration   title` |
| `yt-tool playlists <@handle\|url> [--limit N]` | TSV list: `id   count   title` |
| `yt-tool search <query> [--limit N]` | YouTube search → TSV: `id   duration   uploader   title`. No API key needed. |

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
| Need timestamps in the summary | Use raw yt-dlp VTT path — `yt-tool` strips timestamps |
| Only have a name / phrase, not a URL | `search` first → pick the id(s) → feed into another subcommand |

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
yt-tool transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --out /tmp/yt
```

**Whole playlist:**

```bash
yt-tool transcript "https://www.youtube.com/playlist?list=PLxxxx" --out ~/notes/talks
# Creates ~/notes/talks/<Playlist Title>/<video>.txt per entry
```

**Recent 20 videos from a channel:**

```bash
yt-tool transcript "@veritasium" --limit 20 --out /tmp/veritasium
```

**MP3 audio (best VBR):**

```bash
yt-tool audio "https://youtu.be/dQw4w9WgXcQ" --format mp3 --quality 0
```

**WAV for ASR:**

```bash
yt-tool audio "<url>" --format wav --out /tmp/asr
```

**Trimmed clip:**

```bash
yt-tool audio "<url>" --start 00:01:30 --end 00:02:45 --format mp3
```

**Music library style (metadata + thumbnail):**

```bash
yt-tool audio "<url>" --format mp3 --embed-thumbnail
```

**Summary (Anthropic):**

```bash
export ANTHROPIC_API_KEY=...
yt-tool summary "<url>" --out /tmp/summary.md
```

**Summary fallback (no key — print prompt for calling agent to answer):**

```bash
yt-tool summary "<url>" --keep-transcript --out /tmp/ready-to-summarise.md
```

Then Read `/tmp/ready-to-summarise.md` and produce the summary inline.

**Channel inventory (metadata only, no downloads):**

```bash
yt-tool channel "@veritasium" --limit 10
yt-tool playlists "@veritasium"
```

**Search for a term (no downloads):**

```bash
yt-tool search "Radiohead Creep" --limit 5
# id            duration  uploader       title
# XFkzRNyygfk   237s      Radiohead      Radiohead - Creep
# ...
```

**Artist → WAV files (the canonical "I only have a name" flow):**

Search first, then pipe ids into `audio`. Pick a sensible limit — 20 hits
rarely yields 20 distinct official tracks, so start at 5–10 and widen if
needed. Prefer the results whose `uploader` column matches the artist's
canonical channel (filter `grep` or read the user's pick).

```bash
mkdir -p ~/music/radiohead
yt-tool search "Radiohead" --limit 10 \
  | awk -F'\t' '$3 == "Radiohead" {print $1}' \
  | while read id; do
      yt-tool audio "https://www.youtube.com/watch?v=$id" \
        --format wav \
        --embed-thumbnail \
        --out ~/music/radiohead
    done
```

If the user wants every video on the artist's official channel rather
than search hits (more exhaustive but more noise — behind-the-scenes, live
cuts, shorts), swap `search` for `channel`:

```bash
yt-tool channel "@radiohead" --limit 50 \
  | cut -f1 \
  | while read id; do
      yt-tool audio "https://www.youtube.com/watch?v=$id" --format wav --out ~/music/radiohead
    done
```

Confirm the channel handle with the user first — some artists have
multiple (`@radiohead`, `@radiohead-topic`, fan channels). The
`-topic` channels YouTube auto-generates usually hold the cleanest
official audio.

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

`yt-tool transcript` joins snippet text with spaces — no timestamps. If the
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

- Do not scrape transcripts via `browser-control` when `yt-tool` works — slower and fragile.
- Do not call the YouTube Data API v3 — this skill intentionally has no API key dependency.
- Do not feed raw transcripts into downstream LLM work without at least skimming one file first; auto-captions can be gibberish for music, accents, or heavy jargon.
- Do not default to WAV when MP3 will do — a 1-hour WAV is ~600 MB and will blow through context if Read into the conversation.
- Do not summarise a video you could not confirm has a usable transcript — surface the gap (transcripts disabled, ASR needed) rather than fabricating from the title.
- Do not re-download audio you already have on disk; check for `<title>.mp3` / `.wav` before invoking `audio`.
