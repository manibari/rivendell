#!/usr/bin/env bash
# Transcribe a LOCAL audio/video file with mlx-whisper (Apple Silicon native).
#
# Sibling to audio_transcribe.sh — that one is URL→whisper.cpp (online fallback).
# THIS one is local-file→mlx-whisper: no yt-dlp, faster on M-series, fully offline
# (audio never leaves the machine). Handles .mov/.mp4/.m4a/.mp3/.wav/… (anything
# ffmpeg reads).
#
# Pipeline: ffmpeg (→16kHz mono wav) -> mlx_whisper -> .txt (+ .srt for timestamps).
#
# Usage:
#   local_transcribe.sh <media-file> [output.txt]
#
# Env:
#   WHISPER_MODEL=mlx-community/whisper-large-v3-turbo   # turbo=fast+good; large-v3=max accuracy
#   WHISPER_LANG=auto        # zh/en/ja/… or auto-detect (default: auto)
#   FORMAT=txt               # txt | srt | both  (srt keeps timestamps → chapter alignment)
set -euo pipefail

IN="${1:?usage: local_transcribe.sh <media-file> [output.txt]}"
OUT="${2:-}"
MODEL="${WHISPER_MODEL:-mlx-community/whisper-large-v3-turbo}"
LANG="${WHISPER_LANG:-auto}"
FORMAT="${FORMAT:-txt}"

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

echo "extracting audio → 16kHz mono wav…" >&2
ffmpeg -y -i "$IN" -vn -ar 16000 -ac 1 -c:a pcm_s16le "$WORK/audio16.wav" >/dev/null 2>&1 \
  || { echo "error: ffmpeg could not extract audio from '$IN'" >&2; exit 3; }

case "$FORMAT" in
  srt)  FORMATS="srt" ;;
  both) FORMATS="txt,srt" ;;
  *)    FORMATS="txt" ;;
esac
LANG_ARG=(); [ "$LANG" != "auto" ] && LANG_ARG=(--language "$LANG")

echo "transcribing with mlx-whisper (model=$MODEL, lang=$LANG)… long files take a while" >&2
# mlx_whisper writes <input-basename>.<ext> into --output-dir (basename = audio16)
mlx_whisper "$WORK/audio16.wav" --model "$MODEL" \
  --output-dir "$WORK" --output-format "$FORMATS" "${LANG_ARG[@]}" >&2

TXT="$WORK/audio16.txt"
SRT="$WORK/audio16.srt"

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
EOF
else
  [ -f "$TXT" ] && cat "$TXT" || { [ -f "$SRT" ] && cat "$SRT"; }
fi

[ -f "$TXT" ] || [ -f "$SRT" ] || { echo "error: mlx-whisper produced no transcript" >&2; exit 4; }
