# Session Harvest 報告 — 2026-08-30（mac 機）

## 結論先行

4 個 session 全部落在既有覆蓋範圍內，**本輪沒有新 skill 候選**。唯一實質工作的 Session [3]（138 則訊息）做了三件事：用既有 `resolving-merge-conflicts` skill 解掉兩機分岔的 70 個衝突、把已經在 `.learnings/LEARNINGS.md` 寫好的「根治方案」推廣執行到 5 個 report cron、以及一份 PDCA 分類的 skill taxonomy 規劃文件——三件事分別由既有 skill、既有紀律（記錄→執行根治）、和一次性規劃內容覆蓋，沒有缺口。

---

## Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|--------|----------|
| 1 | MingOS-art | 6 | 讀 `art-bible.md` / `asset-requests.md`，AskUserQuestion 一次 → 樣本太小，看不出模式 |
| 2 | rivendell | 1 | 讀各專案 8/30 token 花費 → 產出繁中日報（既有排程 agent `token-analysis`，非新模式） |
| 3 | rivendell | 138 | 用 `resolving-merge-conflicts` skill 解兩機 merge 衝突 → 把 8/30 稍早記在 LEARNINGS 的「per-machine 檔名根治」推廣到 5 個 report cron → 修 `com.sk.gateway` 未進 whitelist 的問題 → 寫 PDCA taxonomy 規劃文件 (`docs/plans/2026-08-30-skill-loop-taxonomy-wave1.md`) |
| 4 | rivendell | 6 | 讀最近 4 個 session 的使用者訊息摘要 → 寫進實體知識庫（既有 `knowledge-graph` skill 的例行動作） |

**先排除 1、2、4**：
- Session 1 只有 6 則訊息、3 次工具呼叫，內容太薄，看不出可複製的步驟序列。
- Session 2 是既有排程 agent（`agents/registry/token-analysis.md` 已註冊），非新模式。
- Session 4 是既有 `knowledge-graph` skill 的例行寫入，工具序列（Bash 讀摘要→寫實體檔）符合其定義。

Session 3 是本輪唯一值得細看的（見下）。

---

## Skill 候選

### 1.〔Weak〕「單點抓到根因後，掃過所有 sibling 檔案套用同一修法」——不建議開新 skill

- **現象**：Session 3 裡的 `a3b8156` commit 把 `sk-harvest-cron` 已經修過的「per-machine 檔名」解法，一次推廣到另外 5 個 report cron（`ssot-drift` / `token-analysis` / `workflow-retro` / `tester` / `sk audit`），因為這 6 支腳本共用同一個「檔名只帶日期不帶機器名」的反模式，兩台機器同一天各自產出同名報告 → 70 個 merge 衝突裡 64 個都是這個根因。
- **為什麼不算新模式**：
  - 這次執行的動作已經在同一天稍早（8/30 13:34 的 `110d2b7` LEARNINGS entry）被明確寫下「How to apply: 根治——把 harvest 的 per-machine 檔名修法推廣到所有 report cron」。Session 3 只是照著自己剛寫的清單執行，不是臨場摸索出新流程。
  - 同一種「找到一處 bug → grep 找 sibling 檔案是否有同一反模式 → 逐一套修法」的做法，在更早的 `.learnings/LEARNINGS.md`（2026-04-22，pipefail guard 案例：「One sibling had the guard, neighbors didn't」）已經出現過一次。兩次時間跨度四個月，屬於「好工程習慣」等級的原則，不是有固定工具序列、值得包成 skill 的具體工作流——已經被 CLAUDE.md 的 Engineering Gotchas 段落覆蓋（git pipefail 那條），不需要疊床架屋開新 skill。
- **建議動作**：不開新 skill。如果未來 3 個月內這個「抓到根因後主動掃 sibling」的動作又出現第 3 次，且每次都有相同、可辨識的工具序列（例如：先 `grep -rl <反模式>` 列清單、再逐檔 Edit、最後跑驗證指令），屆時再評估是否值得包成一個輕量 checklist skill。目前證據太薄。

### 2.〔Weak〕PDCA skill taxonomy 規劃文件——內容產出，非流程模式

- Session 3 後段寫的 `docs/plans/2026-08-30-skill-loop-taxonomy-wave1.md`（319 行）是把 business/media/meta 三類 skill 重新分類進 PDCA 迴圈的規劃內容，屬於一次性的規劃產出（用既有 `planning-with-files` 或直接文件撰寫即可涵蓋），不是可重複的工具呼叫序列。

### 3.〔Weak〕Session 1（MingOS-art）——樣本不足

- 6 則訊息、3 次工具呼叫，無法判斷是否有可複製模式。若之後同專案再出現類似的 art-bible / asset-requests 讀取＋提問流程，屆時再併案評估。

---

## 建議下一步

本輪 0 個 Strong、0 個 Moderate 候選。唯一觀察項是「根因抓到後掃 sibling 套修法」的原則性重複（04-22、08-30 各一次），先繼續在 `.learnings/LEARNINGS.md` 累積案例，不急著開 skill。
