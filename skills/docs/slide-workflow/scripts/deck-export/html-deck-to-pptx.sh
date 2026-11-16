#!/bin/zsh
# Convert an HTML deck (one element per slide) to PPTX.
#
# Usage: html-deck-to-pptx.sh <deck.html> <out.pptx> [options]
#   --image          one screenshot per slide (exact look, text not editable)
#   --selector SEL   CSS selector of one slide (default .slide)
#   --keep-font      measure with the deck fonts, not Microsoft JhengHei
#   --font NAME      font name written into the PPTX (default Microsoft JhengHei)
#   --title TEXT     file property "title" and "author" (default empty)
#   --verify DIR     open the result in PowerPoint, save it as PDF and write
#                    DIR/cmp-NN.png (HTML on top, PowerPoint below) for review
#
# Needs: node + playwright (rivendell node_modules), uv (pulls python-pptx and pillow),
# PowerPoint for --verify. Work files go to a new folder under $TMPDIR.
set -e
HERE=${0:A:h}
DECK=${1:A}; OUT=${2:A}
[[ -f "$DECK" && -n "$2" ]] || { sed -n 2,13p "$0"; exit 2; }
shift 2
MODE=(); SEL=(--selector .slide); KEEP=(); FONT=(); TITLE=(); VERIFY=""
while (( $# )); do
  case $1 in
    --image) MODE=(--image) ;;
    --selector) SEL=(--selector "$2"); shift ;;
    --keep-font) KEEP=(--keep-font) ;;
    --font) FONT=(--font "$2"); shift ;;
    --title) TITLE=(--title "$2"); shift ;;
    --verify) VERIFY=${2:A}; shift ;;
    *) echo "unknown option: $1"; exit 2 ;;
  esac
  shift
done
(( ${#MODE} )) && KEEP=(--keep-font)  # the image deck shows the deck's own fonts
WORK=$(mktemp -d "${TMPDIR:-/tmp}/deck-export.XXXXXX")
node "$HERE/extract.js" "$DECK" "$WORK" $SEL $KEEP
uv run -q --with python-pptx --with lxml python "$HERE/build_pptx.py" "$WORK/layout.json" "$OUT" $MODE $FONT $TITLE
echo "pptx: $OUT"
echo "work files: $WORK"

if [[ -n "$VERIFY" ]]; then
  # PowerPoint is sandboxed; it reads and writes inside its own container
  BOX="$HOME/Library/Containers/com.microsoft.Powerpoint/Data/Documents/deck-export-check"
  mkdir -p "$BOX" "$VERIFY"
  cp "$OUT" "$BOX/check.pptx"
  osascript -e "tell application \"Microsoft PowerPoint\"
open POSIX file \"$BOX/check.pptx\"
set p to active presentation
save p in POSIX file \"$BOX/check.pdf\" as save as PDF
close p saving no
end tell"
  pdftoppm -png -r 96 "$BOX/check.pdf" "$WORK/ppt"
  rm "$BOX/check.pptx" "$BOX/check.pdf"
  rmdir "$BOX"
  uv run -q --with pillow python "$HERE/compare.py" "$WORK" "$VERIFY"
  echo "compare images: $VERIFY/cmp-*.png (read them before you deliver)"
fi
