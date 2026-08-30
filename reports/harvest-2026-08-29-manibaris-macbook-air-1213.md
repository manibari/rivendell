# Session Harvest 報告 — 2026-08-29

## 結論先行

4 個 session 裡 3 個是雜訊（既有排程日報、既有 skill 常規執行、單次瑣事查詢），只有 **Session 1（PTI-ARES）** 有討論到工作流程決策，但樣本量單薄（僅一段對話式決策、無跨專案重複證據），**本輪沒有找到足以開新 skill 的紮實候選**。

---

## Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|--------|----------|
| 1 | PTI-ARES | 77 | 討論 DFM 規則上線流程：「每條規則先開一個 branch，確認 ok 就關閉」→「最後要把 confirmed 拔掉嗎」→ 收斂成「用開關（feature flag）取代 per-rule branch」；同步編輯 `CHANGELOG.md`、`engine.py`、`enricher.py`、`exporter.py`、`policy.py` |
| 2 | rivendell | 1 | 讀 2026-08-28 各專案 token 花費 → 產出繁中日報（既有排程 agent 產出，非新模式） |
| 3 | sales-assistant | 14 | 執行既有 `crm-projection` skill：查 nx_client 客戶 → 交叉比對 pipeline/customer-intel → 寫 `projection.md`、重建 `INDEX.md` |
| 4 | -Users-manibari-code | 2 | 單次查詢「給我 ssh public key」，一次 Bash 完成，無延伸模式 |

**先排除 2、3、4**：Session 2 是既有排程 headless agent（`reports/token-analysis-*.md` 系列每日固定產出）；Session 3 是既有 skill（`crm-projection`）依 SOP 執行，工具序列（Bash 查詢 → 交叉比對 → Read → Skill）符合其 SKILL.md 定義，是「skill 用得對」而非新模式；Session 4 是一次性瑣事查詢，無重複結構。

真正可能有新模式的只有 **Session 1**，但證據不足以直接開新 skill（見下）。

---

## Skill 候選

### 1. 〔Weak〕DFM 規則上線的「branch-per-rule → toggle」決策 — 不建議開新 skill

- **現象**：使用者在 Session 1 反問自己「是不是該先幫每一個 rule 先開一個 branch，已經確定 ok 的就關閉」→「那我最後是不是還要把 confirmed 拔掉」→ 自己收斂成「用開關來代替應該即可」。過程中同步改了 `engine.py`（規則引擎）、`enricher.py`、`exporter.py`、`policy.py`，是 PTI-ARES 規則上線流程的一次工程決策。
- **為什麼不建議開新 skill**：
  - 這是**單一 session 內的自問自答**，digest 沒有工具序列上的重複結構可萃取（Bash 46 次多半是查驗證/跑測試，不是可模板化的固定步驟）。
  - 「per-branch 驗證 vs feature-flag 開關」是通用軟體工程決策模式，屬於 `~/.claude/CLAUDE.md` Coding Defaults 常識層級，不是 PTI-ARES 專屬領域知識；如果真的要固化，落點也該是「規則引擎上線策略」這種更通用的工程實踐筆記，而非綁死在 DFM 領域的 skill。
  - 已有 `odb-dfm-reference` 覆蓋 PTI-ARES 的 ODB++/DFM 領域知識（Job→Step→Layer、parse seam、幾何陷阱），這次的 engine/enricher/exporter/policy 改動屬於該領域的規則上線流程，如果之後同類「規則怎麼安全上線」的問題在該專案重複出現 2 次以上，應該先進 `odb-dfm-reference` 的補充章節或 PTI-ARES 自己的 `.learnings/LEARNINGS.md`，不是開 rivendell 通用 skill。
- **建議動作**：本輪不動作，僅記錄觀察；若 PTI-ARES 下次上規則又重複「要不要開 branch / 要不要用開關」的猶豫，再考慮寫進該專案的 `.learnings/LEARNINGS.md`。

### 2.〔Weak〕Session 2–4 — 無新候選

- Session 2 已有排程 agent 覆蓋，非新模式。
- Session 3 是既有 `crm-projection` skill 的常規執行。
- Session 4 是一次性瑣事，無延伸價值。

---

## 建議下一步

本輪 0 個 Strong/Moderate 候選，不建議動作。下次 harvest 若 PTI-ARES 或其他專案出現「規則/功能開關上線流程」的重複詢問（≥2 次），可回頭升級評估。
