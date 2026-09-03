#!/usr/bin/env bash
# Sweep every project's .learnings/ + ~/.claude/learnings/, write inventory + flat dump.
# Step 1 of the learnings-promotion-sprint skill. Safe to re-run; clobbers /tmp/learnings-sweep/.
set -euo pipefail

OUT_DIR="${OUT_DIR:-/tmp/learnings-sweep}"
PROJECTS_DIR="${PROJECTS_DIR:-$HOME/Documents/Projects}"
GLOBAL_VAULT="${GLOBAL_VAULT:-$HOME/.claude/learnings}"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

INVENTORY="$OUT_DIR/inventory.tsv"
DUMP="$OUT_DIR/all.txt"

printf 'project\tpath\tlines\tentries\n' > "$INVENTORY"
: > "$DUMP"

# Count entries by counting `## [LRN-` / `## [ERR-` / `## [FEAT-` headers,
# falling back to `^## ` for vaults that don't use the bracket-ID convention.
count_entries() {
  # grep -c prints the count to stdout AND exits non-zero on zero matches.
  # `|| true` swallows the exit code; the printed count is the source of truth.
  local f="$1"
  local n
  n=$(grep -cE '^## \[(LRN|ERR|FEAT)-' "$f" 2>/dev/null || true)
  if [ "${n:-0}" -eq 0 ] 2>/dev/null; then
    n=$(grep -cE '^## ' "$f" 2>/dev/null || true)
  fi
  printf '%s' "${n:-0}"
}

dump_file() {
  local project="$1"
  local f="$2"
  local label="$3"  # LEARNINGS | ERRORS | FEATURE_REQUESTS

  local lines entries
  lines=$(wc -l < "$f" | tr -d ' ')
  entries=$(count_entries "$f")
  printf '%s\t%s\t%s\t%s\n' "$project" "$f" "$lines" "$entries" >> "$INVENTORY"

  {
    printf '\n\n========== [%s] %s (%s) ==========\n\n' "$project" "$label" "$f"
    # Prefix every `## ` heading with `### [<project>]` so the classifier can attribute.
    awk -v proj="$project" '
      /^## / { sub(/^## /, "### [" proj "] "); print; next }
      { print }
    ' "$f"
  } >> "$DUMP"
}

# Project-local vaults.
while IFS= read -r -d '' learnings_dir; do
  project_root=$(dirname "$learnings_dir")
  project=$(basename "$project_root")
  for fname in LEARNINGS.md ERRORS.md FEATURE_REQUESTS.md; do
    f="$learnings_dir/$fname"
    [ -f "$f" ] || continue
    [ -s "$f" ] || continue
    label="${fname%.md}"
    dump_file "$project" "$f" "$label"
  done
done < <(find "$PROJECTS_DIR" -maxdepth 3 -type d -name '.learnings' -print0 2>/dev/null)

# Global vault.
if [ -d "$GLOBAL_VAULT" ]; then
  for fname in LEARNINGS.md ERRORS.md; do
    f="$GLOBAL_VAULT/$fname"
    [ -f "$f" ] || continue
    [ -s "$f" ] || continue
    label="${fname%.md}"
    dump_file "__global__" "$f" "$label"
  done
fi

# Summary to stdout.
total_files=$(($(wc -l < "$INVENTORY") - 1))
total_entries=$(awk -F'\t' 'NR>1 {sum+=$4} END {print sum+0}' "$INVENTORY")
total_lines=$(awk -F'\t' 'NR>1 {sum+=$3} END {print sum+0}' "$INVENTORY")
project_count=$(awk -F'\t' 'NR>1 {print $1}' "$INVENTORY" | sort -u | wc -l | tr -d ' ')

cat <<SUMMARY
Sweep complete.
  Projects:      $project_count (incl. __global__ if present)
  Vault files:   $total_files
  Total lines:   $total_lines
  Total entries: $total_entries

Outputs:
  $INVENTORY
  $DUMP

Top 10 vaults by entry count:
SUMMARY
sort -t$'\t' -k4 -nr "$INVENTORY" | head -10 | awk -F'\t' '{ printf "  %-25s %4s entries  %s\n", $1, $4, $2 }'

cat <<NEXT

Next: hand $DUMP to a general-purpose subagent for classification (Step 2
in SKILL.md). The classifier reads this file and writes
$OUT_DIR/classified.md.
NEXT
