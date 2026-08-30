# Session Harvest 報告 — 2026-08-30

## 結論先行

4 個 session 全部落在既有覆蓋範圍內（既有排程 agent 或既有 skill 常規執行），**本輪沒有新 skill 候選**。唯一值得記錄的是 Session [4]：`crm-projection` 的產生器腳本連續兩天（8/29、8/30）因同一個 `ModuleNotFoundError` 失敗，8/30 這次才真正補上 `sys.path` bootstrap 修掉根因並寫進 `.learnings/ERRORS.md`——這是「同一個坑踩兩次」的訊號，但修法已經回寫進腳本本體，不需要開新 skill，只需確認之後不再復發。

---

## Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|--------|----------|
| 1 | rivendell | 1 | 讀 2026-08-29 各專案 token 花費 → 產出繁中日報（既有排程 agent `token-analysis` 產出，非新模式） |
| 2 | sales-assistant | 14 | 執行既有 `crm-projection` skill（8/29 跑）：查 `nx_client` → 交叉比對 pipeline/customer-intel → 重跑產生器失敗 → 用 `PYTHONPATH=...` 環境變數繞過 → 寫 `projection.md`、`INDEX.md` |
| 3 | sales-assistant | 14 | 執行既有 `material-health` skill：檢查 `materials/` 缺 frontmatter、過期補助、孤兒檔案 → 寫 `HEALTH_REPORT.md`，無異常 |
| 4 | sales-assistant | 18 | 執行既有 `crm-projection` skill（8/30 跑）：同一個 `ModuleNotFoundError` **第二次**出現 → 這次直接 Edit `scripts/_crm_projection_gen.py` 加 `sys.path.insert(0, str(ROOT))` bootstrap，跑通後把復發記錄追加進 `.learnings/ERRORS.md` |

**先排除 1、3**：Session 1 是既有排程 headless agent（`reports/token-analysis-*.md` 系列每日固定產出，`agents/registry/token-analysis.md` 已註冊）；Session 3 是 `material-health` 依 SOP 執行，工具序列（Skill → 多輪 Bash 盤點 → Read → Write）符合其 SKILL.md 定義，是「skill 用得對」而非新模式。

Session 2、4 是同一個 `crm-projection` skill 連續兩天的執行紀錄，放在一起看才看得出真正的模式（見下）。

---

## Skill 候選

### 1.〔Moderate → 已自行解決，建議僅追蹤不開新 skill〕`crm-projection` 產生器的 PYTHONPATH 根因修復

- **現象**：`scripts/_crm_projection_gen.py` 用 `from services.nexus.clients import get_all_clients` 匯入，但腳本被直接以 `python3 scripts/_crm_projection_gen.py` 執行時，`sys.path[0]` 是 `scripts/` 而非專案根目錄，導致 `services.nexus` 匯入失敗。
  - **8/29（Session 2）**：踩到失敗 → 用 `PYTHONPATH=/Users/manibari/code/sales-assistant python3 scripts/_crm_projection_gen.py` 繞過，跑完就結束，沒有寫回腳本或記錄。
  - **8/30（Session 4）**：同一個錯誤**第二次**出現 → 這次不再只是繞過，而是 Edit 腳本本體加上 `sys.path.insert(0, str(ROOT))` bootstrap，跑通後主動 `cat >> .learnings/ERRORS.md` 記錄「2nd occurrence」與已套用的修法。
- **為什麼不建議開新 skill**：
  - 這不是「缺一個新工作流程」，而是**既有 skill 的執行環境有一個根因 bug**，且已經在 8/30 這次直接修進 `sales-assistant` 專案的腳本裡（`.learnings/ERRORS.md` 已有第二次復發記錄可查）。修復落點應該就是 `crm-projection` skill 自己的 runner script，不是 rivendell 通用 skill。
  - 唯一值得留意的是：**這是同一個坑的第二次**，代表 8/29 那次的環境變數繞過沒有回頭修根因，導致隔天重複發生。這比較像是「執行 skill 後要不要順手修環境問題」的紀律問題，屬於 `self-improving-agent` / `.learnings/ERRORS.md` 的職責範圍，而非 skill 覆蓋缺口。
- **建議動作**：本輪不開新 skill。下次 `crm-projection` 排程跑起來時確認 `python3 scripts/_crm_projection_gen.py` 能不帶 `PYTHONPATH` 直接跑通；如果又失敗，代表 8/30 的修法沒有真的生效，屆時再評估要不要把「跑完先驗證乾淨環境」寫進 `crm-projection` 的 SKILL.md 步驟。

### 2.〔Weak〕Session 1、3 — 無新候選

- Session 1 已有排程 agent（`token-analysis`）覆蓋，非新模式。
- Session 3 是既有 `material-health` skill 的常規執行，本次盤點無異常、無新落差。

---

## 建議下一步

本輪 0 個 Strong 候選、1 個 Moderate 觀察項（已有腳本層級修復，僅需追蹤是否真的不再復發）。不建議本輪新增或修改任何 skill。
