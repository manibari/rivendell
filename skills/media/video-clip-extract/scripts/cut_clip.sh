#!/usr/bin/env bash
# Download only a time-range of a YouTube (or any yt-dlp) video and save it as a
# standalone clip — without pulling the whole file.
#
# The efficiency trick is yt-dlp's --download-sections: it fetches just the
# requested span. We add ffmpeg via --force-keyframes-at-cuts so the clip starts
# cleanly on a keyframe (otherwise the first fraction of a second can be gray).
#
# Usage:
#   cut_clip.sh <url> <start> <end> [output.mp4]
#     start/end accept HH:MM:SS, MM:SS, or raw seconds (e.g. 90).
#
# Examples:
#   cut_clip.sh "https://youtu.be/ID" 1:05 2:30 highlight.mp4
#   cut_clip.sh "https://youtu.be/ID" 0 45            # first 45s -> auto-named
#
# Env:
#   IMPERSONATE=0   # set to 0 to disable browser impersonation (default: auto)
set -euo pipefail

URL="${1:-}"; START="${2:-}"; END="${3:-}"; OUT="${4:-}"
if [[ -z "$URL" || -z "$START" || -z "$END" ]]; then
  echo "usage: cut_clip.sh <url> <start> <end> [output.mp4]" >&2
  echo "  start/end: HH:MM:SS | MM:SS | seconds" >&2
  exit 1
fi

command -v yt-dlp >/dev/null || { echo "error: yt-dlp not installed (brew install yt-dlp)" >&2; exit 127; }
command -v ffmpeg >/dev/null || { echo "error: ffmpeg not installed (brew install ffmpeg)" >&2; exit 127; }

# normalize a timestamp to zero-padded HH:MM:SS for --download-sections.
# Accepts raw seconds, MM:SS, or HH:MM:SS; each field is padded so e.g. 1:05
# becomes 00:01:05 (a bare "00:1:05" is an invalid timestamp).
norm() {
  local t="$1" h=0 m=0 s=0
  if [[ "$t" =~ ^[0-9]+$ ]]; then
    printf '%02d:%02d:%02d' $((t/3600)) $(((t%3600)/60)) $((t%60)); return
  fi
  local IFS=: parts
  read -ra parts <<<"$t"
  case ${#parts[@]} in
    3) h=${parts[0]}; m=${parts[1]}; s=${parts[2]} ;;
    2) m=${parts[0]}; s=${parts[1]} ;;
    *) s=${parts[0]} ;;
  esac
  # strip any fractional seconds; clip boundaries are integer-second granular
  s=${s%%.*}
  printf '%02d:%02d:%02d' "$((10#$h))" "$((10#$m))" "$((10#$s))"
}
S=$(norm "$START"); E=$(norm "$END")

IMPERSONATE_ARGS=()
# Only enable if a chrome target is actually usable (see media_fetch.sh note):
# yt-dlp lists it even without curl_cffi, marked "(unavailable)", and passing it
# then would hard-fail the download.
if [[ "${IMPERSONATE:-1}" != "0" ]] \
   && yt-dlp --list-impersonate-targets 2>/dev/null | grep -i chrome | grep -vq unavailable; then
  IMPERSONATE_ARGS=(--impersonate chrome)
fi

if [[ -z "$OUT" ]]; then
  OUT="clip_${S//:/}-${E//:/}.mp4"
fi

echo "cutting ${S} → ${E} from ${URL}" >&2
yt-dlp \
  --download-sections "*${S}-${E}" \
  --force-keyframes-at-cuts \
  -f "bv*+ba/b" \
  --merge-output-format mp4 \
  --retries 3 ${IMPERSONATE_ARGS[@]+"${IMPERSONATE_ARGS[@]}"} \
  -o "$OUT" \
  "$URL"

if [[ -f "$OUT" ]]; then
  dur=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$OUT" 2>/dev/null || echo "?")
  echo "✓ wrote $OUT (${dur}s)" >&2
else
  echo "error: clip not produced — check the time range and that the video is downloadable" >&2
  exit 2
fi
