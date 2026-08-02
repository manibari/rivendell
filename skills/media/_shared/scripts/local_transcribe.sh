#!/usr/bin/env bash
# Transcribe a LOCAL audio/video file with mlx-whisper (Apple Silicon native).
#
# Sibling to audio_transcribe.sh — that one is URL→whisper.cpp (online fallback).
# THIS one is local-file→mlx-whisper: no yt-dlp, faster on M-series, fully offline
# (audio never leaves the machine). Handles .mov/.mp4/.m4a/.mp3/.wav/… (anything
# ffmpeg reads).
#
# Pipeline: ffmpeg (→16kHz mono wav, loudness-normalized) -> mlx_whisper -> .txt
#           (+ .srt for timestamps), then a repetition-loop check on the output.
#
# Usage:
#   local_transcribe.sh <media-file> [output.txt]
#
# Env:
#   WHISPER_MODEL=mlx-community/whisper-large-v3-turbo   # turbo=fast+good; large-v3=max accuracy
#   WHISPER_LANG=auto        # zh/en/ja/… or auto-detect (default: auto)
#   FORMAT=txt               # txt | srt | both  (srt keeps timestamps → chapter alignment)
#   NORMALIZE=1              # 0 disables EBU R128 loudness normalization
#   CONDITION_ON_PREV=False  # True restores whisper's default cross-segment context
#   ASR_PROMPT=""            # initial prompt — proper nouns for this recording, biases decoding
#
# Quiet-recording defaults, learned the hard way (2026-08-02): a meeting recorded
# at mean_volume -33 dB transcribed into a repetition loop — 10280 lines holding
# only 123 distinct sentences, completely unusable. Two changes fixed it and are
# now the default here:
#   1. loudness-normalize before ASR (quiet audio makes whisper far likelier to loop)
#   2. condition_on_previous_text=False (that is the feedback path the loop runs on;
#      whisper's own default is True, which is why the failure is so easy to hit)
# The cost of (2) is slightly weaker cross-segment coherence. Set CONDITION_ON_PREV=True
# when the recording is clean and you want that context back.
#
# Proper nouns are a SEPARATE problem and a bigger model does not fix it — measured
# on whisper.cpp small → large-v3-turbo, the same names stayed wrong. The lever that
# does work is ASR_PROMPT: list the names before the run and bias decoding, rather
# than proofreading afterwards.
set -euo pipefail

IN="${1:?usage: local_transcribe.sh <media-file> [output.txt]}"
OUT="${2:-}"
MODEL="${WHISPER_MODEL:-mlx-community/whisper-large-v3-turbo}"
LANG="${WHISPER_LANG:-auto}"
FORMAT="${FORMAT:-txt}"
NORMALIZE="${NORMALIZE:-1}"
CONDITION_ON_PREV="${CONDITION_ON_PREV:-False}"
ASR_PROMPT="${ASR_PROMPT:-}"

[ -f "$IN" ] || { echo "error: file not found: $IN" >&2; exit 1; }
command -v ffmpeg  >/dev/null || { echo "error: ffmpeg not installed (brew install ffmpeg)" >&2; exit 127; }
command -v ffprobe >/dev/null || { echo "error: ffprobe not installed (brew install ffmpeg)" >&2; exit 127; }
if ! python3 -c 'import mlx_whisper' 2>/dev/null; then
  echo "error: mlx-whisper not installed → pip install mlx-whisper  (Apple Silicon only)" >&2
  exit 127
fi

# A screen capture can be SILENT — fail loud rather than emit an empty transcript.
if ! ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$IN" 2>/dev/null | grep -q .; then
  echo "error: no audio track in '$IN' — nothing to transcribe (silent screen capture?)." >&2
  echo "       For a silent screen recording, sample frames + describe them instead (see SKILL.md)." >&2
  exit 2
fi

WORK="$(mktemp -d "${TMPDIR:-/tmp}/local-tx.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

# Filter order matters: volumedetect passes audio through untouched and reports the
# ORIGINAL level, so putting it ahead of loudnorm gets us the diagnostic and the
# normalized wav in a single decode pass.
AF="volumedetect"
[ "$NORMALIZE" = "1" ] && AF="volumedetect,loudnorm=I=-16:TP=-1.5:LRA=11"

echo "extracting audio → 16kHz mono wav (normalize=$NORMALIZE)…" >&2
if ! ffmpeg -y -i "$IN" -vn -af "$AF" -ar 16000 -ac 1 -c:a pcm_s16le \
     "$WORK/audio16.wav" >/dev/null 2>"$WORK/ffmpeg.log"; then
  echo "error: ffmpeg could not extract audio from '$IN'" >&2
  tail -5 "$WORK/ffmpeg.log" >&2
  exit 3
fi

MEAN_DB="$(grep -o 'mean_volume: -\?[0-9.]*' "$WORK/ffmpeg.log" | head -1 | awk '{print $2}' || true)"
if [ -n "$MEAN_DB" ]; then
  echo "  source level: mean_volume ${MEAN_DB} dB" >&2
  # -30 dB is roughly where quiet-audio repetition loops started showing up.
  if awk "BEGIN{exit !(${MEAN_DB} < -30)}"; then
    if [ "$NORMALIZE" = "1" ]; then
      echo "  note: very quiet source — normalized before ASR (this is the case NORMALIZE exists for)." >&2
    else
      echo "  WARNING: very quiet source and NORMALIZE=0. Expect repetition loops. Re-run with NORMALIZE=1." >&2
    fi
  fi
fi

case "$FORMAT" in
  srt)  FORMATS="srt" ;;
  both) FORMATS="all" ;;   # mlx_whisper -f takes ONE value; 'all' emits txt+srt+vtt+… (no comma lists)
  *)    FORMATS="txt" ;;
esac
LANG_ARG=(); [ "$LANG" != "auto" ] && LANG_ARG=(--language "$LANG")

# large-v3 and its turbo variant tend to emit 簡體 for --language zh regardless of
# what was spoken. An initial prompt written in 繁體 biases the decoder back; it is
# a mitigation, not a guarantee — check the output when the source is Taiwanese.
PROMPT="$ASR_PROMPT"
case "$LANG" in
  zh|Chinese|Mandarin|yue|Cantonese)
    if [ -n "$PROMPT" ]; then PROMPT="以下是繁體中文的內容。${PROMPT}"
    else PROMPT="以下是繁體中文的內容。"; fi
    ;;
esac
PROMPT_ARG=(); [ -n "$PROMPT" ] && PROMPT_ARG=(--initial-prompt "$PROMPT")

echo "transcribing with mlx-whisper (model=$MODEL, lang=$LANG, condition_on_prev=$CONDITION_ON_PREV)…" >&2
[ -n "$PROMPT" ] && echo "  initial prompt: ${PROMPT:0:80}" >&2
# mlx_whisper writes <input-basename>.<ext> into --output-dir (basename = audio16)
mlx_whisper "$WORK/audio16.wav" --model "$MODEL" \
  --output-dir "$WORK" --output-format "$FORMATS" \
  --condition-on-previous-text "$CONDITION_ON_PREV" \
  "${PROMPT_ARG[@]}" "${LANG_ARG[@]}" >&2

TXT="$WORK/audio16.txt"
SRT="$WORK/audio16.srt"

# Repetition-loop check. A looping transcript is not obviously broken at a glance —
# it reads like real sentences — so measure it: the 2026-08-02 failure was 10280
# lines carrying 123 distinct ones (1.2%). Anything under 5% is degenerate output,
# not a transcript. Warn loudly rather than let it flow into a document.
LOOP_RATIO=""
if [ -f "$TXT" ]; then
  TOTAL="$(grep -c '[^[:space:]]' "$TXT" || true)"
  UNIQ="$(sort -u "$TXT" | grep -c '[^[:space:]]' || true)"
  if [ "${TOTAL:-0}" -ge 200 ] && [ "${UNIQ:-0}" -gt 0 ]; then
    LOOP_RATIO="$(awk "BEGIN{printf \"%.1f\", 100*${UNIQ}/${TOTAL}}")"
    if awk "BEGIN{exit !(${UNIQ}/${TOTAL} < 0.05)}"; then
      echo "  WARNING: repetition loop — ${TOTAL} lines, only ${UNIQ} distinct (${LOOP_RATIO}%)." >&2
      echo "           This transcript is not usable. Try: NORMALIZE=1 CONDITION_ON_PREV=False," >&2
      echo "           and check the source level reported above." >&2
    fi
  fi
fi

emit() {  # $1=src $2=dest  — copy if dest given, else cat
  [ -f "$1" ] || return 0
  if [ -n "$OUT" ]; then cp "$1" "$2"; else cat "$1"; fi
}

if [ -n "$OUT" ]; then
  base="${OUT%.txt}"
  [ -f "$TXT" ] && cp "$TXT" "$OUT" && echo "  transcript → $OUT ($(wc -w <"$OUT" | tr -d ' ') words)" >&2
  [ -f "$SRT" ] && cp "$SRT" "${base}.srt" && echo "  timestamped → ${base}.srt" >&2
  # .meta sidecar so save_note.sh gets attribution; kind=asr flags ASR reliability.
  DUR="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$IN" 2>/dev/null | cut -d. -f1)"
  cat >"${OUT}.meta" <<EOF
title: $(basename "$IN")
source: ${IN}
lang: ${LANG}
kind: asr
model: mlx-whisper/${MODEL##*/}
duration_sec: ${DUR:-?}
mean_volume_db: ${MEAN_DB:-?}
normalized: ${NORMALIZE}
condition_on_previous_text: ${CONDITION_ON_PREV}
initial_prompt: ${PROMPT:-}
distinct_line_pct: ${LOOP_RATIO:-n/a}
EOF
else
  [ -f "$TXT" ] && cat "$TXT" || { [ -f "$SRT" ] && cat "$SRT"; }
fi

[ -f "$TXT" ] || [ -f "$SRT" ] || { echo "error: mlx-whisper produced no transcript" >&2; exit 4; }
