---
name: video-transcript
description: >
  Read an online video's spoken content (via its subtitles) and transform it into one of four
  outputs: (1) 重點摘要 / TL;DR, (2) a rewritten, readable 繁體中文 article, (3) a clean 逐字稿
  (verbatim transcript, timestamps & filler removed), or (4) a 繁體中文 translation of a
  foreign-language video. Works on YouTube and any other yt-dlp-supported site (Bilibili, Vimeo,
  X/Twitter, TikTok, …). Pulls manual subs (preferred) or auto-captions.
  TRIGGER when: user pastes a video URL and wants its content — "這支影片在講什麼", "幫我看這個
  YouTube", "整理這部影片重點", "把這影片轉成文章", "抓字幕", "影片逐字稿", "翻譯這個影片",
  "summarize this video", "transcribe this", or drops a youtube.com / youtu.be / bilibili / vimeo /
  x.com link asking to read / summarize / rewrite / translate it. Use this even when the user
  doesn't say "字幕" — if the content lives in an online video, this is the skill.
  DO NOT TRIGGER when: cutting a highlight clip out of a video (use video-clip-extract), producing a
  subtitle FILE / .srt for re-upload or translation-with-timing (use subtitle-file), transcribing a
  local audio/video file (that's a Whisper job), or the link is a plain web page (fetch it directly).
tags: [media, content, video, youtube]
version: 2.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Video Transcript → 轉意

Turn what an online video *says* into text you can use. The video's audio is the input; the
deliverable is one (or more) of four transformations the user picks. The hard, unreliable part —
getting clean text out of the site — is handled by the shared `media_fetch.sh` so you spend your
effort on the transformation, which is where the value is.

## Locate the shared fetcher

The fetch/clean scripts live in the media category's `_shared/`, reused by the sibling skills.
This locator resolves them whether you're in the repo or a symlinked install:

```bash
SKILL_DIR="$(cd -P "${CLAUDE_SKILL_DIR:-skills/media/video-transcript}" 2>/dev/null && pwd -P)"
SHARED="$SKILL_DIR/../_shared/scripts"
```

## Step 0 — Make sure yt-dlp is installed

```bash
command -v yt-dlp >/dev/null && yt-dlp --version || echo "NOT INSTALLED"
```

`brew install yt-dlp` is simplest for occasional single videos. For batches or if you keep hitting
429, install so the impersonation backend can sit alongside it (brew's can't easily):
`pipx install yt-dlp && pipx inject yt-dlp curl_cffi`. See the 429 note in gotchas.

## Step 1 — Fetch the transcript

```bash
bash "$SHARED/media_fetch.sh" "<video-url>" /tmp/transcript.txt
```

- Specific language only? `SUB_LANGS="en" bash "$SHARED/media_fetch.sh" <url> out.txt`
- It prints the **title** and whether it got `manual` vs `auto` subtitles to stderr, and writes a
  `<output>.meta` sidecar (title/url/lang/kind) — no second yt-dlp call needed for attribution.
- **Auto-captions have no punctuation and mishear proper nouns** — if kind is `auto`, say so and be
  cautious with exact quotes.
- **No subtitles at all** ("no subtitles found"): captions are disabled. Don't guess at content —
  fall back to local speech-to-text on the audio:

  ```bash
  bash "$SHARED/audio_transcribe.sh" "<url>" /tmp/transcript.txt
  # Chinese/other: WHISPER_LANG=zh ; bigger model: WHISPER_MODEL=medium ; login-walled: COOKIES=chrome
  ```

  This downloads the audio and runs whisper.cpp (`brew install whisper-cpp ffmpeg`; the model
  auto-downloads on first use). It's **ASR, not human subtitles** — slower, and it mishears proper
  nouns and homophones, so flag it as machine-transcribed and be cautious with names/quotes. Then
  transform as usual. For a long video this takes a few minutes; run it in the background.

Then read it: `wc -l /tmp/transcript.txt && head -50 /tmp/transcript.txt`

## Step 2 — Confirm which output the user wants

If they already said ("整理重點", "翻成中文"), skip. Otherwise ask — the modes differ a lot:

> 要哪種？① 重點摘要 ② 改寫成中文文章 ③ 乾淨逐字稿 ④ 翻譯成繁中

You can produce more than one (e.g. summary *plus* clean transcript).

## Step 3 — Transform

The cleaned text is spoken language: rambling, repetitive, no paragraph structure, and (if
auto-captioned) no punctuation. **Output is 繁體中文** unless asked otherwise. Ground everything in
the transcript — do not invent facts, numbers, or claims the speaker didn't make. Mark garbled
passages `[聽不清]` rather than guessing.

### Mode 1 — 重點摘要 / TL;DR

BLUF first: lead with a one-sentence answer to "這支影片在講什麼", then supporting points.

```markdown
# [影片標題]
**一句話總結**：<the core claim / what it's actually about>
## 重點
- <concrete point, not "討論了很多面向">
- <ordered by importance, not by appearance order>
## 值得記住的細節
- <specific numbers, names, examples the speaker gave>
```

Aim for 30-second readability. Cut throat-clearing. Mirror the video's chapters if it has clear ones.

### Mode 2 — 改寫成通順的中文文章

Reorganize into a written article — a rewrite, not a transcript. Fix structure, add paragraphs and
headings, drop filler and repetition, convert 口語 → 書面語 **without changing meaning or adding
claims**. Preserve the argument, examples, and conclusions.

### Mode 3 — 乾淨逐字稿

Verbatim — for people who want *what was said*. The script already stripped timestamps and
de-duplicated rolling captions; do light cleanup only: add punctuation & paragraph breaks; remove
pure filler ("呃", "um") only when it aids readability. Do NOT rephrase, summarize, or reorder.
If they want timing kept, that's the subtitle-file skill instead.

### Mode 4 — 翻譯成繁體中文

For a foreign-language video. Translate meaning, not words — idiomatic 繁中. Keep technical terms
accurate (original in parens on first use, e.g. 「注意力機制（attention）」). Preserve tone. Combine
with Mode 3 or 1 if useful.

## Notes & gotchas

- **HTTP 429 (Too Many Requests) — the main failure mode.** YouTube's subtitle endpoint rate-limits
  hard (auto-caption-only videos get limited first). Three tiers, in order of what actually works:
  - *Transient* (requests too close): the fetcher's exponential backoff (5→10→20s) clears it, and it
    downloads only ONE track to avoid the multi-language 429 cascade.
  - *Persistent* (IP limited after many requests / a playlist): backoff won't save you — it's a
    server-side block. **The tested fix that works: `COOKIES=chrome bash media_fetch.sh …`** — it
    authenticates with your logged-in browser cookies and uses that quota. (Tested 2026-07-23:
    cookies got through a hard 429 that impersonation could NOT.) Works with any browser yt-dlp
    supports (`COOKIES=firefox`, etc.).
  - *Prevent it up front*: install `curl_cffi` beside yt-dlp (`pipx inject yt-dlp curl_cffi`) — the
    fetcher auto-adds `--impersonate chrome`, cutting 429 *frequency* sharply. But note it **cannot
    rescue an already-blocked IP** — only cookies or time does that.
- **Very long / playlist videos**: fetch works the same; a 2-hour transcript is huge. Summaries are
  fine; for a full rewrite, chunk by chapter.
- **Age-restricted / private**: needs cookies (`--cookies-from-browser chrome`).
- **Attribution**: cite title + URL and whether subs were manual or auto (read the `.meta`).
