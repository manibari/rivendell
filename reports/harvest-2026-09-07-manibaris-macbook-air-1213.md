# Session Harvest — 2026-09-07

## 摘要

3 個 session、約 64 則訊息、涉及 2 個專案（Vault-Peter-Work、sales-assistant）。其中 2 個 session（gov-subsidy-scraper、sales-crm-projection）是**既有 skill 的正常執行**，不構成新候選。唯一的新模式來自 Vault-Peter-Work：把散落的客戶engagement筆記＋截圖整理成一份 PDF 交付到 Downloads，目前**只出現這一次**，樣本不足，評級 Moderate（記錄觀察，暫不建議新建）。

## Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|-------|---------|
| 1 | Vault-Peter-Work | 37 | 讀取光泉（foodbev-retail 化名，見 client-codename-map 記憶）的多篇 discovery / goods-flow 筆記與流程截圖（p-01.png, p-02.png），彙整成一份 PDF，寫入並用 SendUserFile 送到 Downloads |
| 2 | sales-assistant | 17 | 執行既有 skill `gov-subsidy-scraper`：爬 grants.nat.gov.tw / SBIR / SIIR，跟現有 nx_ 資料去重 |
| 3 | sales-assistant | 10 | 執行既有 skill `sales-crm-projection`：查 `nx_client` 所有 active 客戶的 deal pipeline，交叉比對 |

## Skill 候選

### 1. 客戶 engagement 筆記彙整成 PDF（Vault-Peter-Work, session #1）
- **名稱**：`sales-engagement-digest`（暫名，若成案）
- **用途**：把某客戶在 Vault 裡分散的多篇 engagement 筆記（discovery 訪談、流程理解、截圖）讀齊，彙整成一份敘事連貫、附圖的 PDF 摘要，交付到 Downloads 供後續使用（如寄客戶、內部報告）。
- **觸發時機**：使用者說「把 X 客戶的資料整理成一份 PDF」「幫我彙整 [客戶] 的筆記」，且素材來源是 Vault 裡多篇零散 markdown + 截圖，而非素材庫裡的結構化素材。
- **涵蓋步驟**：(1) 依客戶名找齊相關筆記與截圖（STATE.md + discovery-*.md + goods-flow-*.md + 截圖）(2) 讀取彙整成單一敘事 (3) 排版含圖 (4) 匯出 PDF (5) 送到 Downloads
- **分類建議**：`sales`（loop: sales, pdca: do）
- **現有相似**：`sales-material` 是從**結構化素材庫**組裝 PPTX 提案，`office-pdf` 是通用 PDF 讀寫工具，兩者都不處理「Vault 裡零散 markdown 筆記 → 單一敘事 PDF」這段彙整邏輯。若這類任務再出現（例如另一個客戶也要整理 engagement 筆記），值得抽成 skill；本次只有 1 個樣本，先記錄不新建。
- **評級：Moderate**——步驟明確、非顯而易見（要挑對筆記、抓對截圖順序、彙整成連貫敘事），但只出現一次，不確定會不會重複。

### 2.（無新建議）gov-subsidy-scraper / sales-crm-projection 執行（session #2、#3）
- 兩者都是**既有 skill 的正常排程/手動執行**，工具序列（Bash + Skill）符合 skill 本身的設計，沒有偏離既有流程或需要新知識，不構成新候選。

## 結論

本輪沒有 Strong 候選。`sales-engagement-digest` 列為 Moderate 觀察，先記下不新建——等下次遇到「把某客戶散落筆記彙整成交付文件」的任務時，若模式重複出現，再評估是否收斂成獨立 skill 或掛在 `sales-material` 底下當一個子模式。
