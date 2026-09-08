# Session Harvest 報告 — 2026-09-08

輸入：6 個 session 的預摘要（非完整 transcript），~186 則訊息，$0 成本。已對照
`/Users/manibari/code/rivendell/skills/` 現有清單，避免重複建議。

## 免責聲明

本次輸入是「已濃縮過的摘要」，不是原始 transcript，看不到工具呼叫的實際順序與
參數。以下判斷基於摘要文字 + 檔案清單推論，證據強度標在每個候選旁邊；6 個
session 彼此領域幾乎不重疊（Tukey 顧問案 / ChimesFlow / rivendell 出差記錄 /
knowledge-graph 維護 / token 分析 / CRM projection），能佐證「重複出現」的候選
很少，多數只是單一 session 的觀察，不足以定案為 Strong。

---

## Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|--------|----------|
| 1 | Vault-Peter-Work | 25 | Tukey AI 平台 + RPA 開工單的技術/商業諮詢討論（DB 整合、PowerAutomate 按鈕驅動），含兩張截圖 |
| 2 | ChimesFlow | 6 | 無文字 intent，僅 5 次 Bash，資訊量不足以分析 |
| 3 | rivendell | 144 | 出差報告撰寫：讀行事曆截圖 + 名片照片 → 判斷屬於友達宇沛的角色/工作/PDCA → 客戶數位化現況討論 → Tukey AutoML 工作坊提案 → WebSearch/WebFetch 做公司研究 → 寫出 Marketing 介紹-整理.md |
| 4 | rivendell | 9 | 為個人知識庫（knowledge-graph）從近期 session 摘要中萃取人物/公司/專案事實 |
| 5 | rivendell | 1 | token 用量分析師：讀取單日各專案 token 花費 + 指令取樣，寫繁中日報 |
| 6 | sales-assistant | 1 | 執行既有的 crm-projection skill，查詢 nx_client 客戶清單 + deal pipeline |

（原始摘要未附精確時間戳，僅能確認「今天」= 2026-09-08 為分析時間點，不代表 6 個 session 皆發生於今日；避免捏造日期，此欄從缺。）

### 已確認「非缺口」的項目（查過 skills/ 才排除，附證據）

- **Session 4**（knowledge-graph 萃取）→ 已有 `skills/knowledge/knowledge-graph`，就是做這件事。
- **Session 5**（token 日報）→ 不是缺口，是既有排程任務的產出：`reports/token-analysis-*.md` 從 2026-07-05 每天都有（`ls reports/ | grep token` 可查），已經跑了兩個多月，本次只是同一排程任務的又一次執行。
- **Session 6**（crm-projection）→ 摘要本身就寫「Run the crm-projection skill」，使用者已經在用 `skills/sales/sales-crm-projection`，不是缺口。
- **Session 3 的公司研究段落**（友達宇沛數位化現況、WebSearch/WebFetch）→ 已有 `skills/sales/sales-customer-intel`（公司名 → 網路研究 → 業務報告）大致覆蓋，不必新開。

篩掉以上，真正有機會變成新 skill 的候選只剩下 session 1、session 3 各一小塊。

---

## Skill 候選

### 1. 出差照片 → 結構化行程與人脈紀錄（Moderate）

- **Purpose**：讀行事曆截圖 + 名片照片這類「出差隨手拍」，抽出時間/對象/公司，
  並判斷這筆紀錄屬於系統既有角色（役割）架構中的哪個角色、哪項工作、PDCA 的
  哪一環，作為出差報告的骨架。
- **Trigger**：使用者丟出行事曆截圖或名片照片說「幫我寫出差報告」「這是誰的角色
  跟工作跟 PDCA」。
- **Category**：workflow（rivendell 內部自動化）。
- **Rationale**：Session 3 完整跑過一次這個流程（圖片 → 角色判斷 → 商機延伸
  討論），且 CLAUDE.md 裡已經有「Task object：每個 run 要標 角色→工作→PDCA」的
  硬規則，代表這個分類動作是被期待重複發生的，只是目前沒有把「從照片起手」這段
  包裝成可重用流程。**證據強度**：僅 1 個 session 觀察到完整流程，未見重複；
  且與既有 `ai-vision-extract`（圖片→結構化資料的後端工程模式）、`task-brief`
  （角色/工作/PDCA 標記）在概念上部分重疊——新 skill 應該是這兩者之上的一層
  「出差debrief 專用組合」，而不是從零發明抽取邏輯。建議：先觀察是否有第 2 次
  出差報告需求再動手，避免為 n=1 案例建 skill。

### 2. Tukey/RPA 顧問案技術路線討論（Weak）

- **Purpose**：把「客戶想在自家 AI 平台加新功能，該用哪條技術路線（自建 DB 串接
  vs PowerAutomate 按鈕驅動）」這類架構選型討論，整理成結構化的方案比較。
- **Trigger**：客戶顧問案中出現「要不要自己做 vs 用現成 RPA 工具」的路線選擇。
- **Category**：sales / advisory。
- **Rationale**：Session 1 是一次性的技術諮詢對話，25 則訊息裡沒有看到明確的
  「重複工具序列」，比較像是一般顧問對話被 Claude 輔助思考，不是可抽出的固定
  流程。且這類架構選型建議高度依賴客戶當下情境，硬套模板風險是產出空泛答案。
  **不建議現在做**，先歸類為觀察項，若同類「A vs B 技術路線比較」再出現 2 次以上
  再考慮。

### 3. 逐字稿 → 行銷文件整理（Weak）

- **Purpose**：把 `marketing-transcript.txt` 這類原始逐字稿整理成
  `Marketing 介紹-整理.md` 這種結構化行銷說明文件。
- **Trigger**：使用者丟一份逐字稿要求整理成介紹文件。
- **Category**：docs / shared。
- **Rationale**：Session 3 的檔案清單顯示這個轉換發生過一次，但摘要沒有透露
  轉換的具體規則（分段方式、留什麼刪什麼），無法從單一觀察歸納出可重用模板。
  且現有 `video-transcript`（線上影片逐字稿）+ `doc-coauthoring`（通用協作寫作）
  + `de-slopify`（繁中文字打磨）三個 skill 組合起來已經能覆蓋「逐字稿→整理文件」
  的大部分需求，缺的比較像是「串起來」而不是「新建」。**不建議新建 skill**。

---

## 結論

這批 6 個 session 彼此領域分散、多數是 1 次性任務，能佐證「重複出現、值得固化」
的證據很薄。唯一有完整流程可觀察的是 session 3 的出差照片處理，列為 Moderate
但建議先觀察是否重複發生（至少再出現 1-2 次同類「照片→出差報告」需求）再決定
要不要真的開一個新 skill，避免用單一案例定義通用流程。其餘候選（Tukey 顧問案
路線討論、逐字稿整理）證據不足，列 Weak、暫不建議動手。
