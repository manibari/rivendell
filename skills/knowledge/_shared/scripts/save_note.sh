#!/usr/bin/env bash
# Archive a processed video into a durable, searchable notes vault — so the
# knowledge outlives the /tmp transcript and the chat window. Without this the
# skill only ever READ videos; this is the "and remember it" half.
#
# Writes  $VIDEO_NOTES_DIR/YYYY-MM-DD-<slug>/
#   ├── note.md         frontmatter (title/url/source/lang/kind/duration/date)
#   │                   + the summary/article you pass in
#   └── transcript.txt  the full cleaned transcript (copied)
#
# Usage:
#   save_note.sh <transcript.txt> <meta-file|-> <summary.md|-> [notes_dir]
#     meta-file : the .meta sidecar media_fetch.sh writes (title/url/lang/kind); "-" to skip
#     summary   : a markdown file with your summary/article; "-" for transcript-only
#
# Env:
#   VIDEO_NOTES_DIR   default ~/video-notes
set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# Default vault = rivendell's own knowledge base (git-tracked, greppable). The
# script lives at <repo>/skills/knowledge/_shared/scripts/, so four levels up is the
# repo root; resolving physically means a symlinked install still lands in the
# repo. Override with VIDEO_NOTES_DIR (or arg 4) to write elsewhere.
DEFAULT_DIR="$(cd -P "$SCRIPT_DIR/../../../.." && pwd -P)/knowledge/videos"

TRANSCRIPT="${1:-}"
META="${2:--}"
SUMMARY="${3:--}"
NOTES_DIR="${4:-${VIDEO_NOTES_DIR:-$DEFAULT_DIR}}"

[[ -f "$TRANSCRIPT" ]] || { echo "usage: save_note.sh <transcript.txt> <meta|-> <summary.md|-> [dir]" >&2; exit 1; }

# --- pull metadata (from the .meta sidecar if given) -------------------------
title="" url="" lang="" kind="" duration=""
if [[ "$META" != "-" && -f "$META" ]]; then
  title="$(sed -n 's/^title: //p' "$META" | head -1)"
  url="$(sed -n 's/^url: //p' "$META" | head -1)"
  lang="$(sed -n 's/^lang: //p' "$META" | head -1)"
  kind="$(sed -n 's/^kind: //p' "$META" | head -1)"
fi
[[ -n "$title" ]] || title="untitled-$(basename "$TRANSCRIPT" .txt)"

# --- slug: keep CJK, collapse everything unsafe to a single hyphen -----------
slug="$(printf '%s' "$title" \
  | tr '/\\:*?"<>|' '-' \
  | tr ' ' '-' \
  | sed -E 's/-+/-/g; s/^-//; s/-$//' \
  | cut -c1-80)"
[[ -n "$slug" ]] || slug="video"

DATE="$(date +%F)"
DIR="$NOTES_DIR/${DATE}-${slug}"
mkdir -p "$DIR"

cp "$TRANSCRIPT" "$DIR/transcript.txt"

# kind=auto/manual are subtitles; "asr" is whisper. Flag reliability for search.
reliability="$kind"
[[ "$kind" == "auto" ]] && reliability="auto-caption (rough)"
[[ "$kind" == "manual" ]] && reliability="manual subs"

{
  echo "---"
  echo "title: \"${title//\"/\'}\""
  echo "url: ${url}"
  echo "source: $( [[ "$url" == *bilibili* ]] && echo bilibili || { [[ "$url" == *youtu* ]] && echo youtube || echo web; } )"
  echo "transcript_kind: ${kind:-asr}"
  echo "reliability: ${reliability:-asr (machine transcription)}"
  echo "date: ${DATE}"
  echo "tags: []"
  echo "---"
  echo
  if [[ "$SUMMARY" != "-" && -f "$SUMMARY" ]]; then
    cat "$SUMMARY"
    echo
  fi
  echo "## 逐字稿"
  echo
  echo "> \`transcript.txt\` (same folder) — 完整版。以下為前導："
  echo
  head -40 "$DIR/transcript.txt"
} > "$DIR/note.md"

# Keep the browsable index in sync (same pattern as the tender/subsidy scrapers:
# notes are source of truth, INDEX.md is a derived view regenerated on each write).
python3 "$SCRIPT_DIR/build_index.py" "$NOTES_DIR" >&2 2>/dev/null || true

echo "$DIR"
