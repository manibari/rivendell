#!/usr/bin/env bash
# Fetch a YouTube video's subtitles and emit clean plain text.
#
# Design (learned the hard way — see the 429 note below): we do NOT ask yt-dlp
# to download every matching subtitle language. That fires one request per
# language and YouTube 429s the later ones, which under `set -e` would abort the
# whole run even after a usable track had already downloaded. Instead:
#   1. one metadata pass (yt-dlp -J) — lists available tracks AND gives the title
#   2. pick_track.py chooses ONE track (manual preferred over auto-caption)
#   3. download just that single track — no multi-request 429 cascade
#   4. vtt_to_text.py strips timestamps and de-duplicates rolling captions
#
# The title comes free from step 1, so callers never need a second yt-dlp call.
#
# Usage:
#   media_fetch.sh <youtube-url-or-id> [output.txt]
#
# Env overrides:
#   SUB_LANGS="en"        # language preference, comma-sep (default below)
#   OUTDIR=/tmp/yt-xyz    # where intermediates land (default: mktemp dir)
#
# On success, prints the clean text (to stdout or the output file) and writes a
# one-line summary to stderr:  title / language / manual-or-auto. If an output
# file is given, a sidecar "<output>.meta" records title, url, lang, and kind.
set -euo pipefail

# Resolve our own physical location (pwd -P) so sibling scripts are found even
# when this file is invoked through a symlink (rivendell deploys skills as
# symlinks into ~/.claude/skills/ — the physical path lands back in the repo).
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
URL="${1:-}"
OUT="${2:-}"
SUB_LANGS="${SUB_LANGS:-zh-Hant,zh-TW,zh-Hans,zh,en,ja}"

if [[ -z "$URL" ]]; then
  echo "usage: media_fetch.sh <youtube-url-or-id> [output.txt]" >&2
  exit 1
fi

if ! command -v yt-dlp >/dev/null 2>&1; then
  cat >&2 <<'EOF'
error: yt-dlp not installed. Install it first:
  brew install yt-dlp            # macOS (recommended)
  pipx install yt-dlp            # or via pipx
  python3 -m pip install -U yt-dlp
EOF
  exit 127
fi

OUTDIR="${OUTDIR:-$(mktemp -d "${TMPDIR:-/tmp}/yt-transcript.XXXXXX")}"
mkdir -p "$OUTDIR"
META="$OUTDIR/meta.json"

# Opportunistically impersonate a real browser. YouTube 429s bot-like clients
# far more aggressively; impersonation needs the curl_cffi backend. Detection is
# subtle: yt-dlp LISTS chrome as a target even without the backend, but marks it
# "(unavailable)" — and passing --impersonate chrome then hard-fails the whole
# run. So we enable it only when a chrome line exists WITHOUT "(unavailable)".
# To make it available:  pipx inject yt-dlp curl_cffi  (or pip install curl_cffi)
IMPERSONATE=()
if yt-dlp --list-impersonate-targets 2>/dev/null | grep -i chrome | grep -vq unavailable; then
  IMPERSONATE=(--impersonate chrome)
fi

# Escape hatch for a PERSISTENT 429 (IP rate-limited after many requests). Tested
# 2026-07-23: impersonation does NOT rescue a hard-blocked IP, but authenticating
# with browser cookies DOES — it uses your logged-in quota instead. Opt in with
# COOKIES=chrome (or firefox/edge/…). --ignore-no-formats-error is needed because
# the cookie path can otherwise abort with "Requested format is not available"
# before writing the (format-less) subtitle. Auto-caption-only videos are the
# ones that hit persistent 429 first, so this is often the only way to get them.
COOKIES_ARGS=()
if [[ -n "${COOKIES:-}" ]]; then
  COOKIES_ARGS=(--cookies-from-browser "$COOKIES" --ignore-no-formats-error)
fi

# --- Step 1: metadata pass (title + available subtitle languages) ------------
# One call, one request — safe from the multi-download 429. Don't let a non-zero
# exit abort us; validate the output instead.
set +e
yt-dlp -J --skip-download --retries 3 ${IMPERSONATE[@]+"${IMPERSONATE[@]}"} ${COOKIES_ARGS[@]+"${COOKIES_ARGS[@]}"} "$URL" >"$META" 2>>"$OUTDIR/yt.log"
set -e
if [[ ! -s "$META" ]]; then
  echo "error: could not read video metadata for $URL" >&2
  echo "  (private/age-restricted? try: yt-dlp --cookies-from-browser chrome ...)" >&2
  tail -3 "$OUTDIR/yt.log" >&2 2>/dev/null || true
  exit 2
fi

# --- Step 2: choose exactly one track ----------------------------------------
if ! pick_out="$(python3 "$SCRIPT_DIR/pick_track.py" "$META" "$SUB_LANGS")"; then
  # No subtitles at all. FALLBACK=whisper degrades gracefully to local ASR
  # instead of dead-ending (opt-in: Whisper is slow + downloads audio, so it's
  # not the default). Bilibili is the common trigger — its subs are login-walled,
  # so a browser not logged into Bilibili looks identical to "no captions".
  if [[ "${FALLBACK:-}" == "whisper" ]]; then
    echo "no subtitles for $URL — falling back to whisper.cpp (audio ASR)…" >&2
    exec bash "$SCRIPT_DIR/audio_transcribe.sh" "$URL" ${OUT:+"$OUT"}
  fi
  echo "error: no subtitles found for $URL (captions disabled, or Bilibili not logged in)" >&2
  echo "  next step: re-run with FALLBACK=whisper to transcribe the audio locally." >&2
  exit 3
fi
IFS=$'\t' read -r LANG KIND TITLE <<<"$pick_out"

# --- Step 3: download just that one track, with backoff on 429 ---------------
# Manual vs auto flag is exclusive so we pull a single file (no second request).
# But even a single subtitle download can hit HTTP 429 when YouTube is rate-
# limiting your IP (e.g. after processing several videos in a row, or a
# playlist). yt-dlp's own --retries doesn't reliably back off on 429 for
# subtitles, so we wrap the call in an exponential-backoff loop: 429 is
# transient, and waiting a few seconds almost always clears it.
if [[ "$KIND" == "manual" ]]; then
  SUBFLAG=(--write-subs)
else
  SUBFLAG=(--write-auto-subs)
fi

find_vtt() {
  shopt -s nullglob
  for cand in "$OUTDIR"/*."$LANG".vtt "$OUTDIR"/*.vtt; do
    printf '%s' "$cand"; return 0
  done
  return 1
}

vtt=""
delay=5
for attempt in 1 2 3 4; do
  set +e
  yt-dlp \
    --skip-download "${SUBFLAG[@]}" \
    --sub-langs "$LANG" \
    --sub-format vtt --convert-subs vtt \
    --sleep-subtitles 1 --sleep-requests 1 --retries 3 \
    ${IMPERSONATE[@]+"${IMPERSONATE[@]}"} ${COOKIES_ARGS[@]+"${COOKIES_ARGS[@]}"} \
    -o "$OUTDIR/%(id)s.%(ext)s" \
    "$URL" >>"$OUTDIR/yt.log" 2>&1
  set -e
  vtt="$(find_vtt || true)"
  [[ -n "$vtt" ]] && break
  if [[ $attempt -lt 4 ]]; then
    echo "  rate-limited (429) or empty — backing off ${delay}s (retry ${attempt}/3)…" >&2
    sleep "$delay"
    delay=$((delay * 2))
  fi
done

if [[ -z "$vtt" ]]; then
  echo "error: subtitle download kept failing for $URL ($LANG/$KIND) after retries" >&2
  echo "  likely a persistent 429 — wait a minute and try again, or use a different network." >&2
  tail -3 "$OUTDIR/yt.log" >&2 2>/dev/null || true
  exit 4
fi

echo "► ${TITLE}" >&2
echo "  track: ${LANG} (${KIND} subtitles)" >&2

# Sidecar metadata (both modes) so callers get title/url/lang/kind without a
# second yt-dlp call.
write_meta() {
  [[ -n "$OUT" ]] || return 0
  cat >"${OUT}.meta" <<EOF
title: ${TITLE}
url: ${URL}
lang: ${LANG}
kind: ${KIND}
EOF
}

# --- Step 4: emit -----------------------------------------------------------
# RAW=1 → hand back the timestamped .vtt untouched (subtitle-file needs timing).
# default → clean prose via vtt_to_text.py (video-transcript wants readable text).
if [[ "${RAW:-}" == "1" ]]; then
  if [[ -n "$OUT" ]]; then
    cp "$vtt" "$OUT"; write_meta
    echo "  raw vtt → $OUT" >&2
  else
    cat "$vtt"
  fi
else
  if [[ -n "$OUT" ]]; then
    python3 "$SCRIPT_DIR/vtt_to_text.py" "$vtt" "$OUT"; write_meta
  else
    python3 "$SCRIPT_DIR/vtt_to_text.py" "$vtt"
  fi
fi
