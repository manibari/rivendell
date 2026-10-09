#!/usr/bin/env bash
# Find every Mach-O file under a directory (an .app, a bundled runtime) that needs something
# a clean Mac does not have. Two checks:
#
#   LINK   a linked library at an absolute path outside /usr/lib and /System/Library
#          (for example /opt/homebrew/opt/openssl@3/lib/libssl.3.dylib)
#   RPATH  an absolute rpath outside the directory. Search paths that do not exist are
#          skipped, so most are harmless (/Users/runner/... from the wheel's CI build).
#          A path that EXISTS on this machine is the dangerous case: the build machine finds
#          the library there and hides that a clean Mac will not (Homebrew libomp).
#
# A file's own install name (otool -D) is not a dependency and is ignored.
#
# Usage: check-macho-deps.sh <dir> [--strict]
#   exit 0  no LINK problems and no RPATH that exists on this machine
#   exit 1  at least one of those (--strict: also fail on any absolute outside rpath)
set -uo pipefail

ROOT="${1:?usage: check-macho-deps.sh <dir> [--strict]}"
STRICT="${2:-}"
ROOT="$(cd "$ROOT" && pwd)"

links=0 hidden=0 dormant=0 files=0
while IFS= read -r -d '' f; do
  file -b "$f" | grep -q 'Mach-O' || continue
  files=$((files + 1))
  rel="${f#"$ROOT"/}"
  # otool prints a "<file> (architecture x):" header per slice of a universal file; skip those.
  self="$(otool -D "$f" 2>/dev/null | grep -v ':$' | head -1)"

  while read -r lib; do
    [ -n "$lib" ] || continue
    [ "$lib" = "$self" ] && continue
    case "$lib" in
      /usr/lib/* | /System/Library/*) ;;
      /*) echo "LINK   $rel -> $lib"; links=$((links + 1)) ;;
    esac
  done < <(otool -L "$f" 2>/dev/null | grep -v ':$' | awk '{print $1}' | sort -u)

  while read -r rp; do
    case "$rp" in
      /usr/lib | /usr/lib/* | /System/Library/* | "$ROOT"/*) ;;
      /*)
        if [ -e "$rp" ]; then
          echo "RPATH  $rel -> $rp  (EXISTS here: this machine hides the problem)"
          hidden=$((hidden + 1))
        else
          [ "$STRICT" = "--strict" ] && echo "RPATH  $rel -> $rp  (absent here)"
          dormant=$((dormant + 1))
        fi
        ;;
    esac
  done < <(otool -l "$f" 2>/dev/null | awk '/LC_RPATH/{r=1} r && / path /{print $2; r=0}' | sort -u)
done < <(find "$ROOT" -type f \( -name '*.so' -o -name '*.dylib' -o -perm -u+x \) -print0)

echo "checked $files Mach-O files: $links bad links, $hidden rpaths that exist here, $dormant absent rpaths"
fail=$((links + hidden))
[ "$STRICT" = "--strict" ] && fail=$((fail + dormant))
[ "$fail" -eq 0 ]
