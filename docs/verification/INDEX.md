# Rivendell 資料流索引

2026-09-22 依程式碼與隔離反證更新。先看現況，再看整合目標；目標尚未實作。

| 文件 | 回答的問題 |
|---|---|
| [實際功能關係圖](dataflow-functions-2026-09.png) · [HTML 原稿](dataflow-functions-2026-09.html) | 平台、知識、助理各自如何交接資料；哪些關卡真的會擋。主表。 |
| [實際儲存圖](dataflow-stores-actual-2026-09.png) · [Mermaid 原稿](dataflow-stores-actual-2026-09.mmd) | 資料目前寫在哪裡，誰讀取，哪些路徑是可選或相容讀取。 |
| [整合目標圖](dataflow-stores-target-2026-09.png) · [HTML 原稿](dataflow-stores-target-2026-09.html) | 按領域統一資料契約後應如何流動；此圖是待實作方案。 |
| [資料流稽核](dataflow-audit-2026-09-22.md) | 寫入者與讀取者對帳、隔離反證、現況落差、遷移驗收條件。 |
| [原系統資料流圖](../assets/diagrams/rivendell-system-data-flow.png) | 2026-09-22 原本的高層宣稱，作為現況對照。 |

## 領域與模組

| 領域 | 模組 | 資料所有權 |
|---|---|---|
| 平台能力 | `platform/capabilities/catalog/`、`platform/capabilities/workflows/`、Dashboard API/Web | 技能部署清單、角色與工作定義、playbook；舊 `workflow-map.json` 是相容支線。 |
| 平台執行與監控 | `bin/sk-exec-lib`、`platform/agent_fleet/`、`platform/monitoring/`（含 `evidence/`、`system/` 感測器） | `rivendell.db` 的 agent run 與 `execution_event`；互動 session tag 仍由 `tasks.jsonl` 寫入，再匯入 `execution_event`。 |
| 知識庫 | `knowledge/`、`skills/knowledge/`、`bin/sk-facts-cron` | repo 內影音筆記；獨立 `~/.claude/knowledge` 的 entity facts。 |
| 個人助理 | `apps/avatar-gateway/`、`assistant/conversation/`、`assistant/dispatch/` | 對話 log、提案、核准決定、執行結果。 |
| 系統周邊 | `platform/deployment/`、`platform/release/` | 部署與版本政策；這次只核對位置，沒有深入測試控制流程。 |

## 維護

改動資料寫入者、讀取者或跨領域 handoff 時，先更新主表、儲存圖與稽核表的對應列。圖中「實際」必須有程式碼或隔離測試依據；目標變更只更新目標圖。完成遷移後重新反證，才把目標路徑移入實際圖。每張圖保留實查日期。

目前最需要追蹤的落差（角色統計把讀取錯誤顯示為 0 已於 2026-09-23 改為 `ok / empty / unavailable`）：Gateway 把背景派工啟動當作提案成功；單筆 workflow API 沒有執行與清單端點相同的定義檢查。細節見 [稽核表](dataflow-audit-2026-09-22.md)。
