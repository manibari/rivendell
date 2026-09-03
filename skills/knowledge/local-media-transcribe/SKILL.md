---
name: local-media-transcribe
loop: knowledge
pdca: do
description: >
  Transcribe a LOCAL audio/video file on disk (screen recording, meeting capture, voice memo,
  .mov/.mp4/.m4a/.mp3/.wav) into text, then explain it — verbatim 逐字稿, 重點摘要/TL;DR, a readable
  繁體中文 article, or a 繁體中文 translation. Runs speech-to-text fully offline with mlx-whisper
  (Apple Silicon), so audio never leaves the machine. For screen recordings it also samples key
  frames so the explanation covers what's ON SCREEN, not just what's said.
  TRIGGER when: user points at a file already on disk and wants its spoken content — "把這支影片轉逐字稿",
  "這個螢幕錄影在講什麼", "聽寫這段錄音", "本機影片轉文字", "會議錄影整理重點", drops a .mov/.mp4/.m4a
  path, or references a Screen Recording on the Desktop and wants it read/summarised/explained.
  DO NOT TRIGGER when: the content is an ONLINE video URL (use video-transcript — it pulls real
  subtitles, faster & more accurate than ASR), cutting a clip (video-clip-extract), or building an
  upload→transcribe FEATURE into a web app (audio-transcription-flow).
tags: [media, audio, video, transcribe, whisper, local]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Local Media Transcribe — 本機影音聽寫並說明

Turn a file already on disk into text you can use. Unlike `video-transcript` (online, real subtitles),
this is **ASR on local audio** via mlx-whisper — the input is the file's own audio, plus (for screen
recordings) sampled frames so the *explanation* reflects what was on screen. Offline, private, free.

## Locate scripts

```bash
SKILL_DIR="$(cd -P "${CLAUDE_SKILL_DIR:-skills/knowledge/local-media-transcribe}" 2>/dev/null && pwd -P)"
SHARED="$SKILL_DIR/../_shared/scripts"
TX="$SHARED/local_transcribe.sh"          # local file → mlx-whisper → text
# reuse: $SHARED/save_note.sh (archive to knowledge base), build_index.py (rebuild index)
```

## Step 0 — Prereqs (one-time)

```bash
command -v ffmpeg >/dev/null || echo "need: brew install ffmpeg"
python3 -c 'import mlx_whisper' 2>/dev/null || echo "need: pip install mlx-whisper  (Apple Silicon only)"
```

mlx-whisper is Apple-Silicon-only. On Intel/other, fall back to the sibling `audio_transcribe.sh`
engine (`brew install whisper-cpp`) or an API — but on this stack, mlx is the fast path.

## Step 1 — Inspect the file (find it, check it has audio, get duration)

⚠️ **Resolve the path via glob — never hand-type a macOS screen-recording name.** They contain a
`U+202F` NARROW NO-BREAK SPACE between the time and `AM/PM` (e.g. `10.17.11⍽PM.mov`), not a regular
space; typing a normal space gives "No such file or directory" on a file that plainly exists. Let the
shell expand it:

```bash
cd ~/Desktop
for f in Screen\ Recording\ 2026-07-27*.mov; do F="$HOME/Desktop/$f"; done   # captures the real bytes
ffprobe -v error -show_entries format=duration:stream=codec_type -of default=noprint_wrappers=1 "$F"
```

- **No audio track** → you cannot transcribe. Say so, and offer the visual-only route (Step 3) —
  a silent screen capture is read by describing frames, not by ASR.
- **Long file (>~20 min)** → warn the user it'll take a few minutes and runs in the background; don't
  block silently. Consider `run_in_background: true` for the transcribe call and poll.

## Step 2 — Transcribe

```bash
bash "$TX" "$F" /tmp/transcript.txt        # writes transcript.txt + transcript.txt.meta
# timestamps too (for chapter alignment / clip picking):
FORMAT=both bash "$TX" "$F" /tmp/transcript.txt   # also writes /tmp/transcript.srt
# force language / bigger model when needed:
WHISPER_LANG=zh WHISPER_MODEL=mlx-community/whisper-large-v3 bash "$TX" "$F" /tmp/transcript.txt
# feed the proper nouns BEFORE the run — this is the lever for names (see below):
ASR_PROMPT="宏捷、穩懋、Carson、re-tapeout" WHISPER_LANG=zh bash "$TX" "$F" /tmp/transcript.txt
```

Defaults: model `whisper-large-v3-turbo` (fast, strong), language auto-detect, EBU R128
loudness normalization on, `condition_on_previous_text=False`. **It's ASR** — punctuation
and proper nouns can be wrong; flag uncertainty before quoting exactly.

## Step 2.5 — 可信度：read the script's own warnings before you read the transcript

The script now reports three things on stderr and records them in `.meta`. Read them
first — a bad transcript reads like a good one.

**`mean_volume` (source level).** Below roughly −30 dB, whisper starts looping. The
script normalizes by default, so this is usually just a note; it becomes a warning if
you set `NORMALIZE=0`.

**Repetition-loop check.** After transcription the script counts distinct lines vs total.
Under 5% distinct it warns and the transcript is garbage — not "a bit rough", unusable.
Real case (2026-08-02): a meeting at −33 dB produced **10280 lines carrying 123 distinct
sentences (1.2%)**. It looked like fluent prose. Normalizing the audio and turning off
`condition_on_previous_text` produced a readable result from the same file.

**Proper nouns — a bigger model does NOT fix this.** Measured on whisper.cpp
`small` → `large-v3-turbo`: the same names stayed wrong ("Ager" 27 times; SparkLabs came
out as "Spa Labs"/"Spotless"), and 繁中 output degraded to 简体. Do not reach for a bigger
model to fix names. Two things that do work:

1. **`ASR_PROMPT`** — list the names you expect before the run; it biases decoding.
   This is prevention, and it is the cheaper half.
2. **`(?)` markers** — mark every proper noun you inferred from context rather than
   heard clearly, and say so in the handoff: *「文件裡標 (?) 的專有名詞是我依上下文推測，
   建議回聽確認再對外發。」* Never silently guess a name into a document that leaves the
   building.

`(?)` is per-term; the `kind: asr` flag in the note frontmatter is per-file. Both are
needed — the file-level flag says "this came from a machine", the term-level marker says
"this specific word is a guess".

**繁中 caveat.** `large-v3` and its turbo variant tend to emit 简体 for `--language zh`.
The script prepends a 繁體 initial prompt for zh/yue as a mitigation — it is not a
guarantee. Spot-check the output when the source is Taiwanese.

## Step 3 — Add the visual layer (screen recordings only — this is the "說明")

Audio alone misses "點這裡 / 這個數字 / 這個畫面". Sample frames and read them so your explanation
ties narration to what was shown. Use the `.srt` timestamps to sample at topic boundaries, or evenly:

```bash
mkdir -p /tmp/frames
# one frame every 60s (tune to the video); scaled down to keep them cheap to read
ffmpeg -i "$F" -vf "fps=1/60,scale=1280:-1" /tmp/frames/f%03d.png >/dev/null 2>&1
```

Then `Read` a handful of the frames (or the ones at section changes) and weave the on-screen context
into the write-up. Don't read every frame of a 38-min video — pick the ones that matter.

## Step 4 — Deliver (ask which; screen-recording default = 逐字稿 + 章節摘要 + 畫面重點)

Same four transformations as `video-transcript` — pick per the user's ask:

1. **重點摘要 / TL;DR** — bullet the key points; for a screen demo, "做了什麼 → 結果".
2. **逐字稿** — clean verbatim: drop filler (嗯/呃/like), keep meaning; timestamps only if asked.
3. **可讀文章（繁中）** — rewrite spoken flow into a structured article.
4. **翻譯（繁中）** — for a foreign-language file.

For a screen recording, the useful default is a **章節式說明**: each section = a timestamp range,
what was said, and what was on screen (from Step 3).

## Step 5 — Archive (optional, offer it)

```bash
bash "$SHARED/save_note.sh" /tmp/transcript.txt "<one-line summary>"
# → knowledge/videos/YYYY-MM-DD-<title>/note.md  + rebuilt INDEX. Cures read-but-never-saved.
```

## Notes & gotchas

- **First run downloads the model** (~1.5 GB for turbo) into the HF cache — one-time, slow; later
  runs are fast. Say so if it's the first run.
- **ASR ≠ subtitles**: no speaker labels, proper nouns drift. If the content is ALSO online with real
  captions, `video-transcript` on the URL beats ASR — prefer it when a URL exists.
- **Big files**: a 38-min / ~850 MB .mov is fine; the ffmpeg step strips video first so whisper only
  sees a small wav. Extraction is quick; transcription is the long part.
- **Language**: auto-detect is usually right; force `WHISPER_LANG=zh` for Mandarin screen demos to
  avoid an English mis-detect on sparse early speech.
- **Whisper outputs 簡體 for Mandarin.** The raw `.txt` comes back Simplified. For a 繁中 deliverable,
  either convert (`opencc -c s2twp`) or — since you're rewriting/summarising anyway — just produce the
  explanation in 繁中 directly. Flag it if you hand back the raw 逐字稿 unconverted.
