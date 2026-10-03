# 分組 playbook：把過寬的資料夾照意義分開

從 Yellow-Chick 第二段分組提案（`docs/plans/development/2026-09-30-dev-size-gate.md` §4）
與 PTI-ARES feature slices 搬遷歸納。每一節是一種常見的過寬資料夾。

## 先做的三件事

1. **列出檔名、找前綴群**：`git ls-files <dir> | sed 's#.*/##' | sed 's/[_-].*//' | sort | uniq -c | sort -rn`。
   前綴群通常就是分組，但要用「這是什麼」確認，不是機械照前綴切
2. **先定對照表再搬**：舊路徑 → 新路徑寫成一張表（commit 進 plan 文件）。之後改引用、改連結都用這張表跑腳本
3. **查誰用寫死路徑找這些檔**：`grep -rn "<dir>/" --include=*.{py,ts,tsx,md,json,yml,sh}`，
   包含測試、CI、截圖輸出路徑、文件連結

## `tests/` 平鋪（最常見）

照被測程式的套件 / 領域分，一組一個子資料夾，例如 `tests/gates/`、`tests/calendar/`、`tests/secretary/turn/`。

Python / pytest 要注意：
- **收集模式**：`tests/` 沒有 `__init__.py` 時 pytest 用 rootdir prepend 模式，**檔名必須全 repo 唯一**。
  搬的時候不改檔名；子資料夾**不要**加 `__init__.py`（加了會切成 package 模式，所有 `from tests.x import` 都要跟著變）。
  PTI-ARES / mops_dbs 用 `pytest.ini` 的 importlib 模式，同名檔不衝突，但仍建議唯一
- `testpaths = ["tests"]` 會遞迴，不用改；`conftest.py` 留根目錄，子資料夾自動吃到
- **輔助模組**（`*_fixtures.py` 等）跟著主要使用者搬，import 改成 `from tests.<組>.<模組> import`
  （namespace package，靠 `pythonpath = ["."]`）；多組共用的留根目錄，根目錄剩下的也要 ≤ 20
- **路徑深度**：用 `Path(__file__).resolve().parent.parent` / `parents[1]` 找 repo 根目錄的，
  搬深一層要改成 `parents[2]`。改完整套跑一次，找不到檔會直接紅
- 測試 import 其他測試（`from tests.test_xxx import`）：第二段只改路徑；把被借用的 helper 抽到 `*_fixtures.py` 是另一件事

前端測試（Playwright 等）照畫面的領域分，跟已存在的子資料夾合併；寫截圖到固定路徑的 spec 同一個 commit 改路徑。

## 後端套件平鋪（`app/api/`、`app/<domain>/`）

- 照領域分子套件，根目錄只留共用基礎（deps、errors、schemas）
- 子套件裡的相對 import 多一個點：`from ..x` → `from ...x`、`from .deps` → `from ..deps`。
  用 `ruff check --select F821,F401` 與 `python -c "import app.main"` 抓漏
- 註冊點（`main.py` 的 `include_router`）用 `from .api.business import cards as api_cards` 保留原別名，下面一行不動
- 測試裡的 `monkeypatch.setattr("app.api.xxx...")` 字串要一起改
- **相容 shim 的取捨**：預設**不留** shim（shim 把檔案加回根目錄，數字又回去）。
  例外：有 joblib / pickle 檔、外部消費者、排程寫死了舊模組路徑——這時照全域規則保留 shim，
  並在 shim 所在資料夾 README 寫 `## 為什麼平鋪` 說明或把 shim 集中到一個 `compat/`
- 對外的 `__init__.py` 轉出名稱改指新位置，維持 `from app.x import name` 可用
- logger 名稱會跟著模組路徑變，搬前 grep 有沒有人用 logger 名稱過濾
- 有唯一寫入者 / ownership gate 的，搬完跑一次確認子套件仍歸同一個擁有者
- 有 OpenAPI 的，搬完匯出 schema 確認沒有 diff（operationId 看函式名與路徑，不看模組）

## `docs/plans/`、`docs/design/` 平鋪

- 照**工作票家族 / 主題**分（`crm/`、`tasks/`、`platform/`），**不照月份**——月份是時間不是意義
- 檔名不改（日期前綴保留，排序照舊），只換資料夾
- 用對照表一次改所有引用（`TODOS.md`、`ROADMAP.md`、`CHANGELOG.md`、`progress.md`、其他文件、程式註解）。
  有讀取器吃這些文件的（例如開發追蹤讀 `TODOS.md`），改完跑它的測試
- 建議順手加一條連結 gate：md 裡指向 `docs/` 的相對連結都要存在。搬幾百個檔靠人工核對一定漏

## `docs/verification/`、截圖資料夾

- **一次驗收一個資料夾**，報告與截圖放一起：截圖照檔名的主題前綴歸到它那一次驗收，報告 `.md` 一起搬進去
- 單獨一份、沒有截圖的報告（發版紀錄、狀態核對）留根目錄；超過 20 再照種類分
- 一次驗收自己就超過 20 張截圖：那是同一次驗收的證據，一張對應一個步驟——放平鋪 README，不硬拆

## 單一檔案過長

步驟見 [file-split.md](file-split.md)。拆的依據是「一段流程裡哪些本來屬於一起」，例如 Yellow-Chick `handle.py` 862 行拆成
回合頭尾（362）、分支（400）、分支的小答案（169），程式碼原樣搬、判斷一行沒改。

拆之前先存輸出基準（每個 endpoint / CLI 的輸出），拆完逐筆比對——沒有測試的重構不靠 import 成功判斷。
被 `monkeypatch.setattr(module, "name", ...)` 換掉的名字，要留在**呼叫它的那個模組**裡，換掉才有效。
