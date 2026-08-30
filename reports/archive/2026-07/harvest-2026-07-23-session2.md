# Skill Harvest 報告 — 2026-07-23

##一、Session 摘要

| # | 專案 | 訊息數 | 主要活動 |
|---|------|--------|----------|
| 1 | Vault-Peter-Work | 30 | DFM 檢核服務計畫書修訂 — 使用者三次糾正文風（AI 痕跡、表格改段落、破折號改冒號） |
| 2 | Vault-Peter-Work | 186 | 中華電新商機情蒐：上旺科技（SMT）、泰翔保全，用 104 網站查公司業務、產出情蒐報告 + deck |
| 3 | Vault-Peter-Work | 31 | Channel sales deck，收斂為「產線/廠務/業務」三端框架，寫 storyline |
| 4 | PTI-ARES | 196 | Roadmap 查詢、engine/enricher 開發，專案特定 |
| 5 | rivendell | 57 | 討論 QA persona 設計不連貫問題 → 沉澱 persona-card-architecture 記憶 |
| 6 | rivendell | 88 | 補助案技術效益段落 → 用 session-harvest + skill-creator 沉澱技能 |
| 7 | rivendell | 18 | Agent registry schema，用 `/requirement` 產出 agent-registry.md |
| 8 | rivendell | 49 | Sales skills 缺口討論：MEDDIC 不夠用，約會議抓不到 EB、組織圖畫不出來 → 用 gstack-office-hours coaching |
| 9 | sales-assistant | 16 | 執行既有 `/crm-projection` |
| 10 | sales-assistant | 30 | 執行既有 `/subsidy-scraper` |
| 11 | code | 28 | 執行既有 `/repo-rename`（urd-bi → Urd-BI 等） |

已核對 `/Users/manibari/code/rivendell/skills/` 現有清單：session 9-11 是既有 skill 的正常執行，不算新候選。

---

## 二、Skill 候選

### 🟢 Strong — `eb-org-mapper`（暫名，business 分類）

**目的**：B2B 約會議前後，判斷「誰是 EB（Economic Buyer，真正有預算決策權的人）」並畫出組織圖，避免一直跟 Champion 開無效會議。

**觸發**：使用者說「這案子 EB 是誰」「組織圖」「約到對的人了嗎」，或準備第二次以上會議前。

**依據**：Session 8 明確指出「約會議的重點在於能不能向上抓到 EB，如何判斷 EB、如何把組織圖畫出來」是目前 MEDDIC 相關 skill 缺的一塊。查過 `skills/business/` 現有 14 個 skill（customer-intel、presales-pipeline、crm-projection 等），確認沒有任何一個處理「組織權力結構判讀」，純屬空白。

**理由**：這不是一次性任務，是業務流程裡會反覆出現的判斷點（每個新案子都要問一次），且有明確方法論可沉澱（職稱/簽核權/預算歸屬線索 → EB 假設 → 組織圖 → 驗證話術）。與 `customer-intel`（公司背景）、`presales-pipeline`（案件狀態）互補而非重複。

---

### 🟡 Moderate — 擴充 `customer-intel` 加入 104 資料來源

**目的**：104 人力銀行職缺內容（徵才職稀、技術棧、部門規模）是快速判讀公司業務範疇的高訊噪比來源，session 2 對上旺科技、泰翔保全都手動用 WebSearch 查 104。

**觸發**：不需要新 skill 觸發詞——這應該是 `customer-intel` 內部研究步驟的固定一站，而非獨立技能。

**理由**：查過 `customer-intel/SKILL.md`，目前資料來源只列 findbiz.nat.gov.tw + 一般 WebSearch，沒有把 104 列為標準步驟。與其新增一個技能造成觸發詞衝突（使用者不會分清楚「查 104」跟「customer-intel」的邊界），不如把 104 補進 customer-intel 既有的「情蒐」流程一步。**建議做法是編輯既有 SKILL.md，不是造新 skill。**

---

### 🔴 Weak — 不建議新增

- **「產線/廠務/業務」三端框架 storyline**（session 3）：太特定於這次 channel deck 的框架選擇，`slide-workflow` / `pitch-deck` 既有流程已足夠承接，框架本身是內容決策不是流程，不適合沉澱成 skill。
- **DFM 文風糾正**（session 1，表格→段落、破折號→冒號）：`de-slopify` 已有「審查文體模式」專門處理送審文件的文風。這兩條具體規則屬於**補規則**（在 de-slopify 內建 pattern 清單加兩條），不是新 skill。
- **Session 4 (PTI-ARES)、5、6、7**：屬專案特定開發、或已經在當次 session 內用 `requirement`/`skill-creator`/`session-harvest` 沉澱完畢（agent-registry.md、persona-card-architecture 記憶），無需重複造輪子。

---

## 三、建議下一步

1. 用 `/requirement` 走一輪 `eb-org-mapper` 的正式定義（誰用、輸入輸出、與 customer-intel/presales-pipeline 的邊界）。
2. 直接 Edit `customer-intel/SKILL.md`，把 104 加進資料來源清單 — 這個改動小，可以現在做。
3. `de-slopify` 補兩條中文審查文體規則（破折號→冒號、表格轉論文段落）。

要不要我現在就動手做第 2、3 點（小幅編輯既有 SKILL.md），還是先讓你看過這份報告再決定？
