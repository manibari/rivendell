# Session Harvest Report

## Session 概要
- **日期**: 2026-08-31 ～ 2026-09-01（4 個 session，橫跨 2 個專案）
- **主要工作**:
  1. Token 用量日報生成（2026-08-31、2026-09-01，各 1 則，rivendell）
  2. 知識庫事實萃取 — 從 11 個近期 session 摘要更新人物/公司/專案持久事實（rivendell）
  3. crm-projection skill 執行 — 查詢 nx_client 客戶清單 + deal pipeline，交叉比對 customer-intel 報告（sales-assistant）
- **涉及技術**: Claude Code JSONL session 解析、bash 統計聚合、knowledge-graph 事實庫、CRM/deal pipeline 查詢

## 交叉比對結果（Step 4）

四個 session 的工作內容，**全部已有對應 skill/agent 覆蓋**，不是待補的模式：

| Session | 對應現有覆蓋 | 位置 |
|---|---|---|
| [1][2] Token 用量日報 | `token-analysis` agent（非 skills/ 底下的 skill，是排程 agent） | `bin/sk-token-analysis-cron` + `agents/registry/token-analysis.md` |
| [3] 知識庫事實萃取 | `knowledge-graph` skill | `skills/meta/knowledge-graph` |
| [4] crm-projection | `crm-projection` skill | `skills/.../crm-projection`（sales-assistant 專案） |

Session [4] 的使用者訊息甚至直接寫「Run the crm-projection skill」——這不是待萃取的隱性模式，是已命名 skill 的正常呼叫。

## Skill 候選清單

### 🔴 Weak: 無新候選

- **原因**: 本批 4 個 session 呈現的行為，都是**已存在 skill/agent 的排程執行結果**，不是使用者手動摸索出的新工作流程。Session-harvest 的目的是「從真實用法中長出新 skill」，但這裡沒有真實用法——只有既有自動化在跑。萃取這批 session 只會產生跟現有 skill 一字不差的重複建議（如「寫個 token 用量分析 skill」），對 skill library 沒有新增價值。

## 備註

- 樣本量偏薄（4 session、~8 則訊息、tool 使用僅 Bash×4），不足以觀察出跨 session 的重複模式；若要找到真正的候選，建議挑**互動式 session**（使用者手動下達多輪指令、走過摸索/修正過程的），而非排程 agent 的單輪批次輸出。
- 若之後 `token-analysis` 要正式轉成 `skills/` 底下的 skill（目前是 `agents/registry/` 下的排程 agent），可另案評估，非本次 harvest 範圍。
