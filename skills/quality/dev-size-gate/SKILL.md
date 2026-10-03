---
name: dev-size-gate
loop: dev
pdca: check
description: >
  Size is a signal, meaning is the reason (Yellow-Chick D37, PTI-ARES PTI-492):
  a folder holding more than 20 files directly has room to be grouped, a code file
  over 800 lines has room to be split — and both are enforced by a CI gate, not
  by self-discipline. Ships a portable `check_size.py` (git-index based, per-project
  config in the ratchet JSON, `--init` snapshots existing violations into a
  ratchet that may only shrink) plus the playbook for grouping folders by meaning.
  Also owns HOW to split one long file (references/file-split.md, absorbed from the
  former large-file-refactor on 2026-10-04) — one rule set, one voice.
  TRIGGER when: "資料夾太多檔", "超過 20 個檔", "要歸納", "資料夾分類", "檔案太長要拆",
  "模組化重構", "monolith", "拆檔", "size gate", "大小守衛", "平鋪", setting up a new repo's
  CI gates, adding a file to a folder that already holds 20, a file passing 800 lines,
  splitting a large component/module, or `check_size.py` / `size_ratchet.json` showing up red.
  SKIP when: a throwaway prototype or one-off script repo; designing new module
  boundaries from scratch (system-design).
tags: [quality, structure, gate, ci, ratchet]
version: 1.1.0
source: manual
languages: all
---

# dev-size-gate

> 「當你的資料夾下面的檔案過多，那代表有歸納的空間；如果你的程式碼太長，那應該也有拆分的空間。」
> —— 2026-09-30，Yellow-Chick D37 的起點

全域規則早就寫了「200–400 行常態、800 上限」，但靠自律的規則會漂：Yellow-Chick 當時
`handle.py` 862 行、`tests/` 298 檔平鋪。所以這條規則做成**機械 Gate**：CI 紅了才算數。

## 規則

| 規則 | 門檻 | 紅了怎麼辦 |
|---|---|---|
| 資料夾寬度 | 一層**直接**放超過 20 個檔（git 索引裡的） | 二選一：照意義分子資料夾；或放 `README.md`，寫 `## 為什麼平鋪` 標題、底下至少一行理由 |
| 檔案長度 | 程式檔 401–800 行黃燈（列出不擋）；超過 800 行紅 | 照「什麼屬於一起」拆，步驟見 [references/file-split.md](references/file-split.md) |
| 舊帳清單 | 導入當下已超標的項目記進 `size_ratchet.json` | 數字只准變小；修好就從清單刪除——修好卻沒刪也紅，免得它再長回去 |
| 豁免 | 產生檔（OpenAPI client、lock 類）可不算行數 | 每一項都要寫理由，沒寫理由紅。豁免只管行數，不管資料夾寬度 |

**核心原則：大小只是說「看這裡」，搬動的理由必須是它本來就屬於別處。** 不對半切、
不按日期或大小分組、不開 `misc/` / `utils2/`。

平鋪是合法答案，但要寫得出理由。好理由的例子：
- Alembic `versions/`：一條 `down_revision` 串起來的鏈，檔名就是順序，分資料夾反而拆散它
- 同一次驗收的截圖：一張對應報告裡一個步驟，拆開就對不回去

## 導入一個專案（Step 1–4）

**Step 1 — 複製腳本**（原樣複製，不改程式；專案差異寫進清單的 `config`）：

```bash
mkdir -p scripts/checks
cp ~/Code/rivendell/skills/quality/dev-size-gate/scripts/check_size.py scripts/checks/
```

**Step 2 — 產生舊帳清單**：

```bash
python3 scripts/checks/check_size.py --init
```

寫出 `scripts/checks/size_ratchet.json`。接著手動檢查三件事：
1. `config.line_scopes`：預設 `[""]`（整個 repo）。改成實際的程式目錄，例如
   `["app/", "frontend/src/", "scripts/", "tests/"]`——`docs/` 底下一次性的報表腳本不該算
2. `config.suffixes`：預設涵蓋常見程式語言；專案用不到的可以刪
3. 產生檔從 `files` 移到 `exempt` 並寫理由

清單已存在時 `--init` 會拒絕：清單只准手動變短，不准重新產生來洗掉變長的項目。

**Step 3 — 接 CI 與文件**：在 CI 的 gates 步驟加 `python3 scripts/checks/check_size.py --quiet`；
README 的開發指令加一行；專案 `AGENTS.md` / `CLAUDE.md` 補一段（照下面範本）。

```markdown
## 檔案大小與資料夾寬度

`scripts/checks/check_size.py`（CI 會跑）：程式檔超過 800 行擋、401–800 行只提醒；資料夾直接放超過 20 個檔，
要嘛按意義分子資料夾，要嘛放 README 寫 `## 為什麼平鋪`。上線時已超標的記在 `scripts/checks/size_ratchet.json`，
只准變小——改小了順手把數字調低，修好了從清單刪掉。拆檔按「什麼屬於一起」拆，不是對半切。
```

**Step 4 — 負面測試（建議）**：照 Yellow-Chick `tests/gates/test_size_gate.py`（21 條）寫：801 行紅、
800 過；21 檔沒 README 紅、20 過；README 只有標題沒內容紅；清單項目變大紅、修好未刪紅；豁免沒理由紅。
測試檔放 `tests/gates/`，**不要**放進已超標的 `tests/` 第一層——加進去它自己先違反 ratchet。

## 清單紅了：照紅的原因處理

| 訊息 | 意思 | 動作 |
|---|---|---|
| `[新的過長檔]` / `[新的過寬資料夾]` | 不在清單上的新超標 | 拆或分組；不准把它加進清單（清單只記導入當下的舊帳） |
| `[變長了]` / `[變多了]` | 舊帳又長了 | 這次的改動先歸位到子資料夾或拆出去；數字不准往上調 |
| `[已修好或已刪：從清單移除]` | 回到線下但清單還留著 | 同一個 commit 從清單刪除那一行 |
| `[從清單移除]`（平鋪 README） | 已經寫了平鋪理由 | 同上 |
| 提示「可以調低到 N」 | 變小但仍超標 | 順手把數字改成 N |

改清單用文字插入或刪行，不要整檔重新序列化。

**多 session 合併時的例外**：多條 lane 同時往同一個資料夾加檔，合併後數字會超過清單。
二選一並寫進合併 commit 訊息：(a) 合併當下把數字一次調成實際值，註明「基準隨 N 條 lane 合併上調」；
(b) 合併後立刻分組歸零。建議 (a) 然後馬上 (b)。這是唯一允許調高數字的情況。

## 分組怎麼做

細節（Python 測試收集、相對 import、路徑深度、連結改寫）見
[references/grouping-playbook.md](references/grouping-playbook.md)。四條共同做法：

1. **一個資料夾一個 commit**：`git mv`（保留歷史）、同一個 commit 改完所有引用、
   同一個 commit 從清單移除該項
2. **子資料夾也要 ≤ 20**，否則再分一層或寫平鋪 README；不准把超標從父層搬到子層
3. **名稱照「這是什麼」**：照領域 / 服務 / 工作票家族，不照日期、大小或「其他」。
   放不進任何一組的留在原層，不開 `misc/`
4. **搬完驗證**：整套測試、既有 gates、`check_size.py`、lint（Python 加 `ruff check --select F821,F401`）；
   有 OpenAPI 的確認 schema 沒有 diff

專案已經有 DDD / feature-slice 結構時，分組名稱直接沿用那套邊界（例如 rivendell
`docs/architecture/repository-layout.md`、mops_dbs `domains/*`、PTI-ARES `features/*`），
不另起一套命名。設計新模組邊界本身是 `system-design` 的事。

## 參考實作

| 專案 | 位置 | 備註 |
|---|---|---|
| Yellow-Chick | `scripts/checks/check_size.py`、`docs/plans/development/2026-09-30-dev-size-gate.md` | 原始版（D37），含第二段分組提案的完整對照表 |
| PTI-ARES | `scripts/checks/check_size.py`、`AGENTS.md`「檔案大小與資料夾寬度」 | 改成只算 git 索引；本 skill 的腳本從這版泛化 |

本 skill 的 `scripts/check_size.py` 與 PTI-ARES 版在 PTI-ARES 上輸出逐行相同（2026-10-04 驗證）。
