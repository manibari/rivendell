#!/usr/bin/env bash
# Fallback transcription for videos with NO subtitles: download the audio and
# run local speech-to-text (whisper.cpp). This is the escape route media_fetch.sh
# points to when a video has captions disabled — slower and less accurate than
# real subtitles (it's ASR, not human text), but it's the only way to read a
# no-caption video without watching it.
#
# Pipeline: yt-dlp -x (audio only) -> ffmpeg to 16kHz mono wav -> whisper-cli.
#
# Usage:
#   audio_transcribe.sh <url> [output.txt]
#
# Env:
#   WHISPER_MODEL=small     # tiny|base|small|medium|large-v3 (default: small)
#   WHISPER_LANG=auto       # ISO code (zh/en/ja/…) or auto-detect (default: auto)
#   MODEL_DIR=~/.cache/whisper-cpp   # where ggml-*.bin live (auto-downloaded)
#   COOKIES=chrome          # pass through to yt-dlp for rate-limited/private audio
set -euo pipefail

URL="${1:-}"
OUT="${2:-}"
MODEL="${WHISPER_MODEL:-small}"
LANG="${WHISPER_LANG:-auto}"
MODEL_DIR="${MODEL_DIR:-$HOME/.cache/whisper-cpp}"

if [[ -z "$URL" ]]; then
  echo "usage: audio_transcribe.sh <url> [output.txt]" >&2
  exit 1
fi
for tool in yt-dlp ffmpeg whisper-cli; do
  command -v "$tool" >/dev/null || { echo "error: $tool not installed (brew install $tool)" >&2; exit 127; }
done

COOKIES_ARGS=()
[[ -n "${COOKIES:-}" ]] && COOKIES_ARGS=(--cookies-from-browser "$COOKIES" --ignore-no-formats-error)

WORK="$(mktemp -d "${TMPDIR:-/tmp}/yt-audio.XXXXXX")"

# --- 1. ensure the model is present (auto-download from HuggingFace) ----------
MODEL_FILE="$MODEL_DIR/ggml-${MODEL}.bin"
if [[ ! -f "$MODEL_FILE" ]]; then
  mkdir -p "$MODEL_DIR"
  echo "downloading whisper model '${MODEL}' (one-time)…" >&2
  curl -fL --progress-bar \
    "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-${MODEL}.bin" \
    -o "$MODEL_FILE" || { echo "error: model download failed" >&2; rm -f "$MODEL_FILE"; exit 2; }
fi

# --- 2. download audio only, convert to 16kHz mono wav (what whisper wants) ---
echo "downloading audio…" >&2
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  --retries 3 ${COOKIES_ARGS[@]+"${COOKIES_ARGS[@]}"} \
  -o "$WORK/audio.%(ext)s" "$URL" >&2
AUDIO="$(find "$WORK" -maxdepth 1 -name 'audio.*' | head -1)"
[[ -n "$AUDIO" ]] || { echo "error: audio download produced nothing" >&2; exit 3; }

ffmpeg -y -i "$AUDIO" -ar 16000 -ac 1 -c:a pcm_s16le "$WORK/audio16.wav" >/dev/null 2>&1

# --- 3. transcribe ------------------------------------------------------------
echo "transcribing with whisper.cpp (model=${MODEL}, lang=${LANG})… this takes a while" >&2
whisper-cli -m "$MODEL_FILE" -f "$WORK/audio16.wav" -l "$LANG" \
  -otxt -of "$WORK/transcript" >&2

TXT="$WORK/transcript.txt"
[[ -f "$TXT" ]] || { echo "error: whisper produced no transcript" >&2; exit 4; }

# whisper.cpp emits one line per segment; collapse leading spaces
if [[ -n "$OUT" ]]; then
  sed 's/^[[:space:]]*//' "$TXT" > "$OUT"
  echo "  transcript → $OUT ($(wc -w <"$OUT" | tr -d ' ') words)" >&2
else
  sed 's/^[[:space:]]*//' "$TXT"
fi
