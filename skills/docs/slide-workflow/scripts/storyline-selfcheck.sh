#!/usr/bin/env bash

SIGN=false
if [ "${1:-}" = "--sign" ]; then
  SIGN=true
  shift
fi
if [ "$#" -ne 1 ]; then
  printf '用法：storyline-selfcheck.sh [--sign] <path/to/storyline.md>\n' >&2
  exit 2
fi

STORY="$1"
if [ ! -f "$STORY" ]; then
  printf '找不到 storyline 檔案：%s\n' "$STORY" >&2
  exit 2
fi

if ! awk 'NR == 1 && $0 != "---" { exit 1 } /^---$/ { delimiters++; if (delimiters == 2) exit 0 } END { if (delimiters < 2) exit 1 }' "$STORY"; then
  printf 'storyline 缺少完整的 frontmatter：%s\n' "$STORY" >&2
  exit 2
fi

frontmatter_value() {
  awk -v key="$1" '
    NR == 1 && $0 != "---" { exit }
    /^---$/ { delimiters++; if (delimiters == 2) exit; next }
    delimiters == 1 && index($0, key ":") == 1 {
      value = substr($0, length(key) + 2)
      sub(/^[ \t]*/, "", value)
      sub(/[ \t]*$/, "", value)
      if (value ~ /^".*"$/ || value ~ /^\047.*\047$/)
        value = substr(value, 2, length(value) - 2)
      print value
      exit
    }
  ' "$STORY"
}

GENRE="$(frontmatter_value genre)"
if [ -z "$GENRE" ] || [ "$GENRE" = "presales" ]; then
  printf '這份 storyline 是 B2B 提案（genre: presales 或未填），要由 /slide-office-hours 簽核，不能自行簽核。\n' >&2
  exit 2
fi
case "$GENRE" in
  internal|talk|report|other) ;;
  *)
    printf 'genre 值「%s」無效；可用值：presales、internal、talk、report、other。\n' "$GENRE" >&2
    exit 2
    ;;
esac

FAILED=false
for KEY in audience expected_action; do
  VALUE="$(frontmatter_value "$KEY")"
  if [ -n "$VALUE" ]; then
    printf '通過：%s 已填寫。\n' "$KEY"
  else
    printf '未通過：%s 未填寫。\n' "$KEY"
    FAILED=true
  fi
done

if awk '/^---$/ { delimiters++; next } delimiters >= 2 && /^## / { found = 1; exit } END { exit !found }' "$STORY"; then
  printf '通過：內文有 ## 段落。\n'
else
  printf '未通過：內文沒有 ## 段落。\n'
  FAILED=true
fi

if awk '/^---$/ { delimiters++; next } delimiters >= 2 && (index($0, "<在這裡寫>") || index($0, "TODO") || index($0, "TBD")) { found = 1; exit } END { exit found }' "$STORY"; then
  printf '通過：內文沒有佔位文字。\n'
else
  printf '未通過：內文含有 <在這裡寫>、TODO 或 TBD。\n'
  FAILED=true
fi

if [ "$FAILED" = true ]; then
  exit 1
fi
if [ "$SIGN" = false ]; then
  printf '自我檢查通過；可用 --sign 簽核。\n'
  exit 0
fi

SIGNED_AT="$(date '+%Y-%m-%dT%H:%M:%S%z' | sed -E 's/([+-][0-9]{2})([0-9]{2})$/\1:\2/')"
SIGNED_AT="$SIGNED_AT" perl -0777 -i -pe '
  if (/\A---\n(.*?)^---(?=\n|\z)/ms) {
    my $frontmatter = $1;
    my $original_length = length($frontmatter);
    for my $pair ([status => "signed-off"], [signed_by => "self-check"], [signed_at => $ENV{SIGNED_AT}]) {
      my ($key, $value) = @$pair;
      if ($frontmatter =~ /^\Q$key\E:/m) {
        $frontmatter =~ s/^\Q$key\E:[^\n]*/${key}: ${value}/m;
      } else {
        $frontmatter .= "${key}: ${value}\n";
      }
    }
    substr($_, 4, $original_length, $frontmatter);
  }
' "$STORY"
printf '自我檢查通過，已簽核：%s\n' "$STORY"
