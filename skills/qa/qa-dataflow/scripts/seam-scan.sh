#!/usr/bin/env bash
# seam-scan.sh — list the seams a dataflow audit needs to look at.
#
# This only reports LOCATIONS. It draws no conclusions and it is deliberately
# noisy: a false positive costs one Read, a false negative costs a wrong audit.
# Treat the output as a to-check list, not as findings.
#
# Usage: seam-scan.sh [repo-path] [--section store|failure|flag|handler] [--with-tests]
#        MAX=999 seam-scan.sh .        # show every hit instead of the first 60
#
# Test files are excluded by default. A dataflow audit is about the production
# path, and in a well-tested repo the fixtures out-number the real call sites
# several to one. Pass --with-tests when you are auditing the test suite itself.

set -uo pipefail

REPO="."
SECTION="all"
WITH_TESTS=0
while [ $# -gt 0 ]; do
  case "$1" in
    --section) SECTION="${2:-all}"; shift 2 ;;
    --with-tests) WITH_TESTS=1; shift ;;
    -*) shift ;;
    *) REPO="$1"; shift ;;
  esac
done

cd "$REPO" 2>/dev/null || { echo "cannot cd to $REPO" >&2; exit 1; }

# Worktrees matter: agent worktrees under .claude/ are full copies of the repo and
# will out-number (and visually bury) the real source tree if left in.
EXCLUDES='node_modules|/\.git/|/target/|/\.next/|/dist/|/build/|/__pycache__/|/\.venv/|/venv/|site-packages|/vendor/|/\.claude/|/\.worktrees?/'
[ "$WITH_TESTS" -eq 0 ] && EXCLUDES="${EXCLUDES}|/tests?/|_test\.|\.test\.|/spec/|/__tests__/|conftest"

# Source files only. Scanning a repo's data artifacts (a 400MB pcb.json, a build
# output tree) takes minutes and finds nothing — the seams live in code and config.
EXTS="py ts tsx js jsx mjs cjs rs go java kt swift rb php cs sql sh bash yaml yml toml ini cfg env"

RG_GLOBS=(); GREP_INCS=()
for e in $EXTS; do RG_GLOBS+=(-g "*.$e"); GREP_INCS+=(--include="*.$e"); done
GREP_EXCS=(--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=target
           --exclude-dir=.next --exclude-dir=dist --exclude-dir=build
           --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=venv
           --exclude-dir=vendor --exclude-dir=.claude --exclude-dir=.worktrees
           --binary-files=without-match)

# ripgrep when available (faster, respects .gitignore); grep -rn otherwise.
# Flags pass through, so callers can use -i / -l.
if command -v rg >/dev/null 2>&1; then
  scan() { rg --no-heading --line-number --color never --max-filesize 2M \
             "${RG_GLOBS[@]}" "$@" . 2>/dev/null | grep -Ev "$EXCLUDES"; }
else
  scan() { grep -rnE "${GREP_EXCS[@]}" "${GREP_INCS[@]}" "$@" . 2>/dev/null | grep -Ev "$EXCLUDES"; }
fi

# Find a line matching $1 whose NEXT line matches $2 — an except/catch handler is
# only interesting together with what its body does. Built on grep -A1 rather than
# a multiline regex because ripgrep is not guaranteed to exist as a binary
# (inside Claude Code `rg` is a shell function, invisible to scripts).
scan_pair() {
  grep -rnE -A1 "${GREP_EXCS[@]}" "${GREP_INCS[@]}" "$1" . 2>/dev/null \
    | grep -Ev "$EXCLUDES" \
    | awk -v nxt="$2" '
        /^--$/ { prev=""; next }
        /^[^:]*:[0-9]+:/ { prev=$0; next }
        { if (prev != "" && $0 ~ nxt) print prev; prev="" }'
}

section() {
  printf '\n=== %s\n%s\n' "$1" "$2"
}

count_report() {
  local out
  out="$(cat)"
  if [ -z "$out" ]; then
    echo "  (none found)"
  else
    echo "$out" | head -n "${MAX:-60}"
    local n
    n="$(echo "$out" | wc -l | tr -d ' ')"
    [ "$n" -gt "${MAX:-60}" ] && echo "  … ${n} total, showing ${MAX:-60}. Re-run with MAX=999 for all."
  fi
}

# ---------------------------------------------------------------- 1. stores
if [ "$SECTION" = "all" ] || [ "$SECTION" = "store" ]; then
section "WRITERS — who puts data into a store" \
"Every store needs a writer AND a reader. A store with writers but no readers
is side-mounted, not a system of record — whatever the docs claim."

echo "-- file writes"
scan '\.(write_text|write_bytes|writeFile|writeFileSync)\(|json\.dump\(|open\([^)]*["'"'"']w' | count_report

echo
echo "-- DB writes / commits"
# Deliberately narrow: bare .save() / .create() match canvas contexts and DTO
# builders far more often than they match a database, and the noise buries the
# real hits.
scan 'session\.(add|add_all|commit|bulk_|merge|delete)\(|db\.(session|commit|add)|\.execute\(\s*(insert|update|delete)|INSERT +INTO|UPDATE +[A-Za-z_.]+ +SET|DELETE +FROM|\.objects\.(create|update|bulk_create)\(|prisma\.[a-z]+\.(create|update|upsert|delete)|sqlx::query!?\(|diesel::(insert|update|delete)' | count_report

section "READERS — who takes data back out" \
"Compare against the writer list. Mismatches are the whole point of the audit."

echo "-- file reads"
scan '\.(read_text|read_bytes|readFile|readFileSync)\(|json\.load\(|open\([^)]*["'"'"']r' | count_report

echo
echo "-- DB reads"
# Same reasoning as writes: .filter( / .find( are array methods in most files.
scan 'session\.(query|get|scalars?|execute)\(|db\.(session\.)?query\(|SELECT .+ FROM|\.objects\.(filter|get|all)\(|prisma\.[a-z]+\.(find|count|aggregate)|sqlx::query_as|diesel::.*load' | count_report
fi

# ------------------------------------------------------------- 2. failures
if [ "$SECTION" = "all" ] || [ "$SECTION" = "failure" ]; then
section "SWALLOWED FAILURES — where a broken flow stays silent" \
"For each hit ask one question: when this fails, does the user ever find out?
If not, this is where 'the flow looks fine' hides a flow that has been broken
for months. Flag non-fatal WRITES especially — a store whose write failure
does not block shipping was never the system of record."

echo "-- explicit non-fatal markers"
scan -i 'non-fatal|nonfatal|best[- ]effort|fire[- ]and[- ]forget|swallow|ignore (the )?(error|failure)' | count_report

echo
echo "-- empty / logging-only catch blocks"
# The handler body is on the NEXT line, so this has to be a multiline match.
# Matching `except X:` alone flags every exception handler in the repo and the
# real ones drown.
# Backslashes are doubled because awk unescapes the -v string once before it
# becomes a regex; a single \( arrives as a bare ( and blows up the match.
scan_pair 'except[^:]*:[[:space:]]*$' \
          '(pass|\\.\\.\\.|return|log(ger|ging)?\\.(warn|warning|info|debug|error)|print[[:space:]]*\\()' | count_report

echo
echo "-- js/ts: empty or log-only catch"
scan 'catch[[:space:]]*\([^)]*\)[[:space:]]*\{[[:space:]]*(\}|console\.)|\.catch\([[:space:]]*\([[:space:]]*\)[[:space:]]*=>[[:space:]]*\{?[[:space:]]*\}?[[:space:]]*\)' | count_report

echo
echo "-- Rust: silent defaults on failure"
scan 'unwrap_or_default\(\)|unwrap_or\(|ok\(\)\?|let _ =' | count_report
fi

# ---------------------------------------------------------------- 3. flags
if [ "$SECTION" = "all" ] || [ "$SECTION" = "flag" ]; then
section "FLAGS — the default value IS the current behaviour" \
"Read each default. A beautifully implemented path behind a flag that defaults
to off is dead code in production. Record: name | default | which path it takes
| is the other path tested."

echo "-- env var reads with defaults"
scan 'os\.environ\.get\(|os\.getenv\(|process\.env\.|std::env::var\(|env::var\(|getenv\(' | count_report

echo
echo "-- feature-flag-shaped names"
# Upper-case only, on purpose: lower-case `enabled:` / `disabled=` is UI state on
# every other line of a React codebase and matching it drowns the real flags.
scan '\b(ENABLE|DISABLE|USE|FEATURE|TOGGLE|EXPERIMENTAL)_[A-Z0-9_]+\b|\b[A-Z][A-Z0-9_]*_(ENABLED|DISABLED|FLAG|TOGGLE|MODE)\b' | count_report
fi

# -------------------------------------------------------------- 4. handlers
if [ "$SECTION" = "all" ] || [ "$SECTION" = "handler" ]; then
section "HANDLERS READING RAW SOURCES — bypasses of the intended layer" \
"An HTTP handler that opens a file or reads an artifact directory is routing
around whatever layer the architecture doc says owns that data. Count them:
the count is the size of the migration nobody scheduled."

scan -l '@(app|router)\.(get|post|put|delete|patch)|@(app_)?route|fastapi|express\(\)|axum::routing' 2>/dev/null \
  | grep -Ev '/tests?/|_test\.|\.test\.|/spec/|conftest' \
  | sort -u | head -40 \
  | while IFS= read -r f; do
      [ -f "$f" ] || continue
      hits="$(grep -nE '\.(read_text|readFile|read_to_string)\(|json\.load\(|open\(|Path\(|glob\.glob\(' "$f" 2>/dev/null | head -5)"
      [ -n "$hits" ] && { echo "-- $f"; echo "$hits" | sed 's/^/   /'; }
    done
fi

cat <<'EOF'

=== NEXT
Nothing above is a finding yet. Read each hit, then:
  1. build the writer/reader table per store  (Phase 1)
  2. predict, then actually cut, each dependency  (Phase 2)
Locations without file:line evidence in the report do not count.
EOF
