---
name: video-clip-extract
loop: knowledge
pdca: do
description: >
  Cut a highlight clip out of an online video and save it as a standalone file — WITHOUT downloading
  the whole thing. Give it a URL and a time range (or a topic to find), and it fetches just that
  span via yt-dlp --download-sections + ffmpeg keyframe-accurate cutting. Works on YouTube and any
  yt-dlp-supported site.
  TRIGGER when: user wants a *piece* of a video as video — "把這段剪出來", "剪一段", "擷取
  YouTube 片段", "下載這影片的 2:10 到 3:00", "clip the part where…", "cut a highlight from this
  video", "剪精華", or pastes a video URL with a start/end time or a "the bit about X" request.
  DO NOT TRIGGER when: user wants the words/text of the video (use video-transcript), a subtitle
  file (use subtitle-file), or the whole video downloaded (plain yt-dlp). Also skip for local video
  files already on disk (use ffmpeg directly).
tags: [media, video, ffmpeg, youtube]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Video Clip Extract — 剪片段

Pull one time-range out of an online video and save it as its own file. The value is doing it
*without* downloading the full video: yt-dlp's `--download-sections` fetches only the requested span.

## Locate scripts

```bash
SKILL_DIR="$(cd -P "${CLAUDE_SKILL_DIR:-skills/knowledge/video-clip-extract}" 2>/dev/null && pwd -P)"
SHARED="$SKILL_DIR/../_shared/scripts"   # media_fetch.sh, for topic→timestamp lookup
CUT="$SKILL_DIR/scripts/cut_clip.sh"
```

## Prereqs

Needs **both** `yt-dlp` and `ffmpeg` (`brew install yt-dlp ffmpeg`). The cut script checks and tells
you which is missing.

## Case A — user gave explicit times

Just cut. Times accept `HH:MM:SS`, `MM:SS`, or raw seconds.

```bash
bash "$CUT" "<url>" 1:05 2:30 /tmp/highlight.mp4
```

The script starts the clip on a clean keyframe (`--force-keyframes-at-cuts`) so it doesn't open on a
gray frame, and reports the output duration via ffprobe so you can confirm it matches the range.

## Case B — user described the moment ("the part about X"), no timestamp

You need to find *when* it happens first. Fetch the timestamped subtitles and locate the topic:

```bash
RAW=1 bash "$SHARED/media_fetch.sh" "<url>" /tmp/subs.vtt    # keep timing
```

Read `/tmp/subs.vtt`, find the cue(s) covering the topic, read their start time, and give a little
lead-in / tail so the clip isn't clipped mid-sentence (e.g. start ~2s before the cue, end ~1-2s
after the last relevant cue). Then cut with Case A. **Tell the user the timestamps you chose** and
why — if you guessed the boundary, say so, so they can nudge it.

## Notes & gotchas

- **429 rate-limiting** applies here too (same YouTube limits as the other media skills). The cut
  script auto-uses `--impersonate chrome` when `curl_cffi` is installed. A persistent 429 needs time
  to clear — don't retry in a loop.
- **Multiple clips**: call the cut script once per range. Name outputs distinctly.
- **Format**: output is mp4 (`bv*+ba` best video+audio, merged). If the user needs audio-only, that's
  a different job — use `yt-dlp -x --audio-format mp3 --download-sections`.
- **Accuracy**: keyframe cutting means the real start can land a fraction before your requested time
  (so nothing important is cut off). For frame-exact cuts, download the full video and ffmpeg-trim —
  slower, rarely needed.
- **Long ranges = big downloads**: a 20-minute "clip" defeats the point. If they want most of the
  video, just download it whole.
