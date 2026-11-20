#!/usr/bin/env python3
"""Check the form of a Traditional Chinese end-user manual."""

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys


HAN = r"[㐀-䶿一-鿿豈-﫿]"
WORD = r"[A-Za-z0-9]"
MESSAGES = {
    "MW101": "中文旁請用全形標點（，；：！？。）",
    "MW102": "括號請用半形 ( ) 與 [ ]",
    "MW103": "中文與英文或數字之間要有一個半形空格",
    "MW104": "中文與半形括號之間要有一個半形空格",
    "MW105": "不要用破折號，改用 ( ) 或「：」",
    "MW106": "請用「選取」",
    "MW107": "畫面名稱只用 [ ]，不要加粗",
    "MW108": "畫面名稱去掉刪節號與冒號",
    "MW109": "選單路徑寫成 [甲] > [乙]",
    "MW110": "畫面名稱請用 [ ]；「」用於引用與錯誤訊息",
    "MW111": "請用「您」",
    "MW112": "改用「其」或重述名詞",
    "MW113": "改用「停止回應」「封鎖清單」「允許清單」",
    "MW114E": "不要放開發環境位址",
    "MW114W": "改用使用者在畫面上看到的說法",
    "MW115": "不要使用表情符號",
    "MW116": "標題層級／結尾標點／格式不符",
    "MW117": "兩個標題之間要有內文",
    "MW118": "步驟超過 12 個，請拆成多個工作",
    "MW119": "步驟超過 7 個，考慮拆分",
    "MW120": "一個步驟只做一個動作",
    "MW121E": "圖片替代文字／檔案有問題",
    "MW121W": "替代文字請以「螢幕擷取畫面」開頭",
    "MW122E": "提示框只用注意、秘訣、重要、警告，且不可相鄰",
    "MW122W": "一篇最多 2 個提示框",
    "MW123": "空白儲存格請填「不適用」或「無」",
    "MW124": "表格前的說明句以「。」結尾",
    "MW125": "全形標點旁不要空格",
    "MW126": "括號內不要空格",
    "MW127": "中文不要用斜體；預留位置請用粗體",
}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    col: int
    level: str
    code: str
    message: str


def _option(options, name, default=None):
    if isinstance(options, dict):
        return options.get(name, default)
    return getattr(options, name, default)


def _blank(chars, start, end):
    chars[start:end] = " " * (end - start)


def _masked_lines(lines):
    """Return visible prose and link-bracket positions for each original line."""
    result = []
    fenced = False
    fence_char = ""
    fence_len = 0
    frontmatter = bool(lines and lines[0].strip() == "---")
    for index, line in enumerate(lines):
        chars = list(line)
        links = set()
        if frontmatter:
            result.append((" " * len(line), links))
            if index and line.strip() == "---":
                frontmatter = False
            continue
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fenced:
            result.append((" " * len(line), links))
            if fence and fence.group(1)[0] == fence_char and len(fence.group(1)) >= fence_len:
                fenced = False
            continue
        if fence:
            fenced = True
            fence_char = fence.group(1)[0]
            fence_len = len(fence.group(1))
            result.append((" " * len(line), links))
            continue
        result.append((chars, links))

    comment = False
    for index, (chars, links) in enumerate(result):
        if isinstance(chars, str):
            continue
        line = lines[index]
        position = 0
        while position < len(line):
            if comment:
                end = line.find("-->", position)
                if end < 0:
                    _blank(chars, position, len(line))
                    break
                _blank(chars, position, end + 3)
                position = end + 3
                comment = False
            else:
                start = line.find("<!--", position)
                if start < 0:
                    break
                comment = True
                position = start
        visible = "".join(chars)
        for match in re.finditer(r"https?://\S+", visible):
            _blank(chars, match.start(), match.end())
        visible = "".join(chars)
        for match in re.finditer(r"(?<!!)\[[^\]\n]*\]\([^\)\n]*\)|!\[[^\]\n]*\]\([^\)\n]*\)", visible):
            fragment = match.group()
            left = match.start() + fragment.index("[")
            right = match.start() + fragment.index("]")
            links.update((left, right))
            _blank(chars, right + 1, match.end())
        visible = "".join(chars)
        for match in re.finditer(r"(`+)(.*?)\1", visible):
            _blank(chars, match.start(), match.end())
        result[index] = ("".join(chars), links)
    return result


def _adjacent(chars, left, right):
    while left >= 0 and chars[left] in "*_":
        left -= 1
    while right < len(chars) and chars[right] in "*_":
        right += 1
    return left, right


def check_text(text, path="<text>", options=None):
    disabled = set(_option(options, "disable", []) or [])
    if isinstance(_option(options, "disable", []), str):
        disabled = set(_option(options, "disable").split(","))
    allowed = {term.casefold() for term in (_option(options, "allow_term", []) or [])}
    findings = []

    def add(line, col, level, code, message=None):
        if code not in disabled:
            findings.append(Finding(str(path), line, col, level, code, message or MESSAGES[code]))

    lines = text.splitlines()
    masked = _masked_lines(lines)
    headings = []
    alerts = []
    list_start = None
    list_indent = None
    list_count = 0

    def end_list():
        nonlocal list_start, list_indent, list_count
        if list_start is not None:
            if list_count > 12:
                add(list_start, list_indent + 1, "E", "MW118")
            elif list_count >= 8:
                add(list_start, list_indent + 1, "W", "MW119")
        list_start = list_indent = None
        list_count = 0

    for number, line in enumerate(lines, 1):
        visible, link_brackets = masked[number - 1]
        raw = line
        for match in re.finditer(r"https?://[^\s/:]+:\d+|localhost|127\.0\.0\.1|0\.0\.0\.0", raw, re.I):
            if match.group().casefold() not in allowed:
                add(number, match.start() + 1, "E", "MW114", MESSAGES["MW114E"])
        for match in re.finditer(r"\b(?:API|endpoint|port|JSON)\b|資料表", visible, re.I):
            if match.group().casefold() not in allowed:
                add(number, match.start() + 1, "W", "MW114", MESSAGES["MW114W"])

        for match in re.finditer(r"[,;:!?]|\.", visible):
            pos = match.start()
            char = match.group()
            before = pos > 0 and re.fullmatch(HAN, visible[pos - 1])
            after = pos + 1 < len(visible) and re.fullmatch(HAN, visible[pos + 1])
            if (char != "." and (before or after)) or (char == "." and before and (pos + 1 == len(visible) or after or visible[pos + 1] == " ")):
                add(number, pos + 1, "E", "MW101")
        for match in re.finditer("[（）［］]", visible):
            add(number, match.start() + 1, "E", "MW102")
        for pos in range(len(visible) - 1):
            left, right = _adjacent(visible, pos, pos + 1)
            if right >= len(visible) or left < 0 or (left != pos and right != pos + 1):
                continue
            a, b = visible[left], visible[right]
            if re.fullmatch(HAN, a) and re.fullmatch(WORD, b) or re.fullmatch(WORD, a) and re.fullmatch(HAN, b):
                add(number, right + 1, "E", "MW103")
            if (re.fullmatch(HAN, a) and b in "([" or a in ")]" and re.fullmatch(HAN, b)) and left not in link_brackets and right not in link_brackets:
                add(number, right + 1, "E", "MW104")
        for match in re.finditer(r"──|[—―]", visible):
            add(number, match.start() + 1, "E", "MW105")
        for match in re.finditer(r"點擊|點選|單擊|按一下|按(?=\s*[\[「])", visible):
            if match.group() == "按一下" and visible[max(0, match.start() - 5):match.start()] == "以滑鼠右鍵":
                continue
            add(number, match.start() + 1, "E", "MW106")
        for match in re.finditer(r"(?:\*\*|__)\[|\[(?:\*\*|__)|(?:\*\*|__)\]|\](?:\*\*|__)", visible):
            if any(match.start() <= p < match.end() for p in link_brackets):
                continue
            add(number, match.start() + 1, "E", "MW107")
        screens = []
        for match in re.finditer(r"\[([^\]\n]*)\]", visible):
            if match.start() in link_brackets:
                continue
            screens.append(match)
            inner = match.group(1)
            if "..." in inner or "…" in inner or inner.endswith((":", "：")):
                add(number, match.start() + 1, "E", "MW108")
        for first, second in zip(screens, screens[1:]):
            between = visible[first.end():second.start()]
            if ">" in between and between != " > ":
                add(number, first.end() + between.index(">") + 1, "E", "MW109")
        for match in re.finditer(r"(?:\*\*|__)>(?:\*\*|__)", visible):
            add(number, match.start() + 3, "E", "MW109")
        for match in re.finditer(r"(?:選取|輸入|移至|開啟|關閉|清除|按|點)\s*「", visible):
            add(number, match.start() + 1, "W", "MW110")
        for match in re.finditer(r"你(?!們)", visible):
            add(number, match.start() + 1, "E", "MW111")
        for match in re.finditer("它", visible):
            add(number, match.start() + 1, "W", "MW112")
        for match in re.finditer("當機|死當|黑名單|白名單", visible):
            add(number, match.start() + 1, "W", "MW113")
        for match in re.finditer("[\U0001f300-\U0001faff\u2600-\u27bf\ufe0f]", visible):
            add(number, match.start() + 1, "E", "MW115")

        heading = None
        if re.match(r"^\s{0,3}#{1,6}\s", visible):
            heading = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$", raw)
        if heading:
            level = len(heading.group(1))
            body = heading.group(2)
            if headings and level > headings[-1][1] + 1:
                add(number, heading.start(1) + 1, "E", "MW116", MESSAGES["MW116"] + "：標題層級跳級")
            if re.search(r"[。．.：:？?！!，,；;]$", body):
                add(number, heading.start(2) + len(body), "E", "MW116", MESSAGES["MW116"] + "：結尾標點")
            if "**" in raw or "`" in raw:
                add(number, heading.start(1) + 1, "E", "MW116", MESSAGES["MW116"] + "：標題格式")
            if level == 1 and _option(options, "no_h1", False):
                add(number, heading.start(1) + 1, "E", "MW116", MESSAGES["MW116"] + "：不允許一級標題")
            if headings and all(not item.strip() for item in lines[headings[-1][0]:number - 1]):
                add(number, heading.start(1) + 1, "W", "MW117")
            headings.append((number, level))

        item = re.match(r"^(\s*)(\d+[.)])\s+", visible)
        if item:
            indent = len(item.group(1))
            if list_start is None or indent != list_indent:
                end_list()
                list_start, list_indent = number, indent
            list_count += 1
            body = visible[item.end():]
            for screen in re.finditer(r"\[[^\]]*\]", body):
                body = body[:screen.start()] + " " * len(screen.group()) + body[screen.end():]
            actions = re.findall("選取|輸入|移至|開啟|關閉|清除|拖曳|選擇", body)
            if len(actions) >= 3 or "，或" in body or "或是" in body:
                add(number, item.end() + 1, "W", "MW120")
        elif list_start is not None and raw.strip() and len(raw) - len(raw.lstrip()) <= list_indent:
            end_list()

        alert = re.match(r"^\s*>\s*\*\*([^：]{1,4})：\*\*", visible)
        if alert:
            alerts.append(number)
            if alert.group(1) not in {"注意", "秘訣", "重要", "警告"}:
                add(number, alert.start(1) + 1, "E", "MW122", MESSAGES["MW122E"])
            if len(alerts) > 1 and all(not item.strip() for item in lines[alerts[-2]:number - 1]):
                add(number, alert.start() + 1, "E", "MW122", MESSAGES["MW122E"])

        for match in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", raw):
            alt, target = match.group(1), match.group(2)
            reason = None
            if not alt:
                reason = "替代文字不可為空"
            elif len(alt) > 150:
                reason = "替代文字超過 150 字"
            elif alt == Path(target).name or re.search(r"\.(?:png|jpe?g|gif|webp)$", alt, re.I):
                reason = "替代文字不可用檔名"
            elif not re.match(r"^[a-z]+://|^/", target, re.I) and path != "<text>" and not (Path(path).parent / target).exists():
                reason = "圖片檔案不存在"
            if reason:
                add(number, match.start() + 1, "E", "MW121", MESSAGES["MW121E"] + "：" + reason)
            if alt and not alt.startswith("螢幕擷取畫面"):
                add(number, match.start() + 1, "W", "MW121", MESSAGES["MW121W"])
        for match in re.finditer(r"<img\b", visible, re.I):
            add(number, match.start() + 1, "W", "MW121", "請用 Markdown 圖片語法")
        # A table pipe next to the space is cell padding, not a space beside the punctuation.
        for match in re.finditer(r"(?<=[^\s|]) [，。、：；！？「」《》＜＞]|[，。、：；！？「」《》＜＞] (?=[^\s|])", visible):
            add(number, match.start() + 1, "E", "MW125")
        for match in re.finditer(r"\( +| +\)", visible):
            add(number, match.start() + 1, "W", "MW126")
        for match in re.finditer(r"(?<!\*)\*(?!\*)([^*\n]+)\*(?!\*)|(?<!_)_(?!_)([^_\n]+)_(?!_)", visible):
            if re.search(HAN, match.group(1) or match.group(2)):
                add(number, match.start() + 1, "E", "MW127")

    end_list()
    if len(alerts) > 2:
        add(alerts[2], 1, "W", "MW122", MESSAGES["MW122W"])
    for index in range(1, len(lines)):
        if not re.match(r"^\s*\|?\s*:?-{3,}:?\s*\|", lines[index]):
            continue
        if "|" not in lines[index - 1]:
            continue
        previous = index - 2
        while previous >= 0 and not lines[previous].strip():
            previous -= 1
        if previous >= 0 and lines[previous].rstrip().endswith(("：", ":")):
            add(previous + 1, len(lines[previous].rstrip()), "W", "MW124")
        row = index + 1
        while row < len(lines) and "|" in lines[row] and lines[row].strip():
            content = lines[row].strip()
            if content.startswith("|"):
                content = content[1:]
            if content.endswith("|"):
                content = content[:-1]
            cells = content.split("|")
            offset = len(lines[row]) - len(lines[row].lstrip())
            if lines[row].lstrip().startswith("|"):
                offset += 1
            for cell in cells:
                if cell.strip() in {"", "-", "--", "—", "–"}:
                    add(row + 1, offset + 1, "E", "MW123")
                offset += len(cell) + 1
            row += 1
    # The adjacency scan can see one pair twice across emphasis markers; keep one finding.
    return sorted(set(findings), key=lambda item: (item.path, item.line, item.col, item.code, item.message))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-h1", action="store_true")
    parser.add_argument("--disable", default="")
    parser.add_argument("--allow-term", action="append", default=[])
    parser.add_argument("--include-readme", action="store_true")
    args = parser.parse_args(argv)
    paths = []
    for name in args.paths:
        item = Path(name)
        if item.is_dir():
            paths.extend(p for p in item.rglob("*.md") if args.include_readme or p.name != "README.md")
        elif item.is_file():
            paths.append(item)
        else:
            parser.error("找不到檔案或目錄：" + name)
    findings = []
    for path in sorted(set(paths), key=str):
        findings.extend(check_text(path.read_text(encoding="utf-8"), str(path), args))
    if args.json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False))
    else:
        for item in findings:
            print(f"{item.path}:{item.line}:{item.col}: {item.level} {item.code} {item.message}")
        print(f"{sum(item.level == 'E' for item in findings)} 個錯誤，{sum(item.level == 'W' for item in findings)} 個警告")
    return int(any(item.level == "E" or args.strict for item in findings))


if __name__ == "__main__":
    sys.exit(main())
