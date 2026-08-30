## Session Harvest 報告 — 2026-08-21

**結論先講**：8 個 session 裡，只有 **1 個 Moderate 候選**（IC-YMS 的「重寫前系統現況三方稽核」），其餘 7 個都命中既有 skill 或證據太薄，不構成新 skill。

---

### 一、Session 摘要

| # | 專案 | 訊息數 | 關鍵活動 | 產出/素材 |
|---|------|--------|----------|----------|
| 1 | IC-YMS | 106 | build+後端測試驗證 → 前後端當機 → 使用者要求截圖證明 → 又跑掉 → 使用者考慮整包重寫；期間產出「三方對照盤點」與「文件清理候選清單」 | `00-system-inventory-2026-08-21.md`、`doc-cleanup-candidates-2026-08-21.md`、app-3400.png |
| 2 | Norns-ERP | 151 | 討論影像辨識+出入庫模組該獨立還是併入既有系統；決定包材庫存當第一垂直切片先跑通，會計引擎往後挪；伴隨行動裝置設計系統討論 | IMG_2921/2929.jpg（實物照片）、design-system-mobile.md、design-system.md、f1.png |
| 3 | PTI-ARES | 34 | 純 commit 流程 | — |
| 4 | TailTrack | 6 | 詢問 Apple Developer 帳號設定 | — |
| 5 | Verdandi-AutoML | 99 | 回顧 AutoML 專案目前開發進度 | CrossfilterEda.tsx、charts.tsx、drive.py、v1-baseline.png |
| 6 | rivendell | 78 | 整理 skill-quality 分支內容 → push | — |
| 7 | rivendell | 1 | token 用量分析師日報生成（`sk-token-analysis-cron` 排程 agent 產出） | 對應 `reports/token-analysis-2026-08-20.md` |
| 8 | sales-assistant | 19 | 執行既有 `crm-projection` skill，查 nx_client + deal pipeline 並交叉比對 | — |

---

### 二、Skill 候選

#### Session 1（IC-YMS）→ **Moderate**：`system-reality-audit`（重寫前系統現況三方稽核）

實際讀了產出的兩份文件（不是只看摘要）：

- `00-system-inventory-2026-08-21.md` 有完整方法論：對照 **A. 程式碼實際有什麼**（掃 routes/pages/routers/permissions.json）、**B. 文件宣稱有什麼**、**C. 客戶要什麼**，每條斷言都附 `file:line` 或指令輸出，落差分成 G1~G5（文件過期未更新 / 權限靜默隱藏 / 死碼 / 客戶回報迴歸 / 文件互相矛盾）並標嚴重度。
- `doc-cleanup-candidates-2026-08-21.md` 依盤點結果把每份文件分類成 🗑️刪 / 📦歸檔 / ✏️改 / ✅留，每條附證據，且明講「只列候選、不執行刪除」。
- 觸發情境很清楚：使用者說「怎麼又跑掉了」「要不要乾脆重寫」時，與其直接動手改或重寫，先跑這套「地基有什麼」的三方稽核，把「文件說的」「code 有的」「客戶要的」對齊，才知道真正的落差在哪。這跟 `github-repo-audit`（結構/文件覆蓋率評分）、`doc-drift-sync`（CHANGELOG/ROADMAP 版本對齊）都不是同一件事。

**保留 Strong 評級的理由不足**：
1. **N=1** — 這批 digest 只看到這一次，沒有跨 session 重複出現。
2. **與 `qa-dataflow` 觸發詞有重疊** — 該 skill 的觸發清單已包含「architecture 跟實作有沒有走鐘」，方法論卻是「單一資料流的功能關係圖 + 甲乙對抗反證」，跟這次「整系統三方對照 + 文件去留分類」的產出形狀不同。是否該開新 skill，還是把 `qa-dataflow` 擴充成「單資料流模式」+「全系統盤點模式」兩種，值得先問過你再定。

**建議**：下次遇到「系統跑掉、考慮重寫」的情境再出現一次類似模式時，直接開 `system-reality-audit`；現在先記一筆，不倉促動手。

#### Session 2（Norns-ERP）→ 不開新 skill，屬於既有路由正常運作

「模組該獨立還是併入」「先做哪個垂直切片」是產品範疇的思考/探索階段決定，AskUserQuestion 用了 12 次也符合 CLAUDE.md Step 0 的路由設計（office-hours 模式反問、不急著出稿）。這個結論本身也呼應既有 memory `fleet-infra-spine`（8+ 產品共用 infra spine、從成熟產品交集抽取）。設計系統檔案的產出對應既有 `gstack-design-consultation`。沒有缺口。

#### Session 3（PTI-ARES）、Session 6（rivendell）→ 純例行操作，無新模式

commit、push 這類單步驟操作，證據量不構成 workflow candidate。

#### Session 4（TailTrack）→ 證據太薄

僅 6 則訊息問 Apple Developer 帳號設定，看不出可重複步驟，不下判斷。

#### Session 5（Verdandi-AutoML）→ Weak，證據不足以成案

「回顧開發進度」是常見 ad-hoc 動作，71 次 Bash 但 digest 看不到具體在查什麼（測試？log？git log？）。如果這類「開發進度回顧」在其他專案重複出現，才值得考慮是否要一個通用的 progress-review skill；這次先不開。

#### Session 7、8（token-analysis / crm-projection）→ 已是既有 skill/agent，非候選

`token-analysis` 已有 `bin/sk-token-analysis-cron` + `agents/registry/token-analysis.md` 排程機制；`crm-projection` 是既有 skill 正常被呼叫。兩者都是「系統正常運作」的證據，不是缺口。

---

### 三、結論與建議

- **唯一值得追蹤的候選**：IC-YMS 的重寫前三方稽核模式（`system-reality-audit`），目前評 **Moderate**，卡在 N=1 和與 `qa-dataflow` 的觸發詞重疊，需要你決定要開新 skill 還是擴充 `qa-dataflow`。
- 其餘 7 個 session 沒有新缺口，不建議動手開發。
- 本報告只在對話中輸出，**沒有寫入 `reports/`** —— 依 rivendell CLAUDE.md 規則，`reports/*` 由排程 agent 自己擁有，互動 session 不手動寫入；今天的 `harvest-2026-08-21-*.md` 是空檔（該次排程 agent 疑似跑空/失敗），如果你要把這份內容補進去，跟我說一聲我再寫。
