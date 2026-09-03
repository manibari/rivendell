---
name: subtitle-file
loop: knowledge
pdca: do
description: >
  Produce a subtitle FILE (.srt / .vtt) from an online video — keeping the timing — for re-upload,
  archiving, or translation-in-sync. Fetches the original subtitles and converts to clean SRT; can
  translate each cue into 繁體中文 while preserving timestamps (monolingual 繁中 or bilingual
  original+繁中). Works on YouTube and any yt-dlp-supported site.
  TRIGGER when: user wants a timed subtitle file, not prose — "幫我做字幕檔", "產生 srt", "下載字幕
  檔", "把字幕翻成中文（保留時間軸）", "生成雙語字幕", "export subtitles", "srt for this video",
  "translate the subtitles keeping timing". Also when they want to re-upload / burn-in subtitles.
  DO NOT TRIGGER when: user wants readable text / a summary / an article (use video-transcript — it
  throws timing away on purpose), or wants a video clip (use video-clip-extract). If they just want
  to *read* the translation, that's video-transcript Mode 4, not this.
tags: [media, subtitles, srt, youtube]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Subtitle File — 字幕檔（保留時間軸）

Make a properly-timed `.srt` from an online video's subtitles. Unlike video-transcript (which
discards timing to make prose), the whole point here is that each line stays in sync with the video.

## Locate scripts

```bash
SKILL_DIR="$(cd -P "${CLAUDE_SKILL_DIR:-skills/knowledge/subtitle-file}" 2>/dev/null && pwd -P)"
SHARED="$SKILL_DIR/../_shared/scripts"   # media_fetch.sh (RAW mode) + vtt_to_srt.py
```

## Step 1 — Fetch the timed subtitles (RAW mode)

`RAW=1` hands back the timestamped `.vtt` untouched (default mode would strip timing):

```bash
RAW=1 bash "$SHARED/media_fetch.sh" "<url>" /tmp/subs.vtt
# specific language:  SUB_LANGS="en" RAW=1 bash "$SHARED/media_fetch.sh" <url> /tmp/subs.vtt
```

Read `/tmp/subs.vtt.meta` for title/lang/kind. **Manual subs make good subtitle files; auto-captions
have approximate cue boundaries and no punctuation** — usable for a rough pass, warn the user if
that's all that exists.

## Step 2 — Convert to clean SRT

```bash
python3 "$SHARED/vtt_to_srt.py" /tmp/subs.vtt /tmp/out.srt
```

This strips karaoke tags, merges rolling-caption duplicates into single timed blocks, and renumbers
as SRT. If the user only wanted the original-language SRT, you're done — hand them `/tmp/out.srt`.

## Step 3 — Translate in place (if asked), preserving timing

This is the LLM part. Read the SRT and rewrite **only the text lines**, never the indices or the
`-->` timing lines. Two layouts:

- **Monolingual 繁中**: replace each cue's text with its 繁體中文 translation.
- **Bilingual**: keep the original line, add the 繁中 translation on the line below it (common for
  language-learning / accessibility).

Rules that matter for subtitles specifically:
- **Translate meaning, not words** — idiomatic 繁中 that reads at subtitle speed.
- **Keep it short** — a subtitle line the viewer reads in ~2 seconds. If a translation is too long,
  tighten it; don't overflow the cue.
- **One cue = one thought** — don't merge or split cues (that breaks timing sync).
- Preserve the exact timestamp lines and blank-line separators so the file stays valid SRT.

Write the result with the Write tool (don't try to sed multi-line cues). Then sanity-check:

```bash
head -12 /tmp/out.srt          # indices sequential? timings intact? text translated?
```

## Notes & gotchas

- **429 rate-limiting**: same as the other media skills — the fetcher backs off and auto-impersonates
  when curl_cffi is present; a persistent IP block needs time, not retries.
- **.vtt output**: if the user needs `.vtt` (web `<track>`), SRT→VTT is trivial — prepend `WEBVTT\n\n`
  and change `,` to `.` in timestamps. Mention this; do it if asked.
- **Validation**: an SRT is valid if blocks are `index / start --> end / text / blank`. If a player
  rejects it, the usual cause is a missing blank line between blocks or a stray index.
- **Don't confuse with video-transcript**: if they just want to *read* it, that skill's Mode 4 is
  less work. This skill exists specifically because they need the **file with timing**.
