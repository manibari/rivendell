# Session Harvest Report — 2026-05-06

## Session 摘要

| # | Project | Msgs | 主要活動 | 主要工具 |
|---|---------|------|---------|---------|
| 1 | Peter-Work | 68 | 為 CIO 承辦會議準備數位轉型案例（立積、力成、喬山 FMCS + 廠務 AI Agent），並做客戶名稱去識別化 | Write(19), Bash(16), Edit(14), Read(5) |
| 2 | news-stock | 36 | 投資研究 agent Continuous Mode：讀 portfolio、產生 daily 報告 | Bash(12), WebSearch(12), TodoWrite(5) |
| 3 | sales-assistant | 11 | CRM projection：從 nx_client / nx_deal 投影到本地 markdown | Bash(4), Read(3), Skill(1) |

Session 2 與 3 完全在既有 skill（`investment-research`、`crm-projection`）軌道上，無新 pattern。Session 1 含一個既有 skills 沒覆蓋到的 pattern。

---

## Skill 候選評估

### Strong — 無

3 個 session 中沒有出現「跨 session、跨專案重複、且既有 skills 沒覆蓋」的強候選。

### Moderate

#### 1. `case-study-anonymizer`（案例去識別化）

- **Purpose**: 把真實客戶交付物轉成可對外分享的匿名案例卡（一頁介紹），保留產業 / 規模 / 痛點 / 方案 / 成效，但移除可辨識資訊（公司名、人名、機台型號、特定產線代號）。
- **Trigger**: 使用者說「去識別化」、「把這個案例匿名」、「換成 A 公司」、「不能露出客戶名」、「拿 X 案子當墊檔但不能寫死客戶」。
- **Category**: `docs/`（與 `sales-material`、`pitch-deck` 同類）
- **Rationale**:
  - Session 1 出現明確訊號：「去識別化 → 喬山的東西先拿廠務 AI Agent 檔著」——把真實喬山 FMCS 案例改寫成匿名版本對 CIO 提案使用。
  - 既有 `customer-intel` 是「蒐集真實情報」、`sales-material` 是「組裝對特定客戶的提案」、`pitch-deck` 是「做投資人簡報」——都沒有「真實案例 → 匿名案例卡」這個轉換動作。
  - B2B 顧問 / SI / AI 服務商常見需求：客戶 A 不准曝光，但案例本身是最強銷售素材。
  - 風險：只有 1 個 session 樣本，可能是 one-off。建議先觀察 1–2 週，看是否再次出現。

### Weak

#### 2. `executive-workshop-prep`（高階主管案例 + 流程通識課準備）

- **Purpose**: 為高階主管場合（董事會、CIO meeting、EMT 通識課）準備「案例分享 + 流程梳理」雙軌教材。
- **Trigger**: 使用者說「高階主管案例分享」、「CIO 通識課」、「流程梳理 workshop」。
- **Rationale**: Session 1 提到「杰倫在所有高階主管案例分享 + 流程梳理通識課中大失分」，後續準備是要避開同樣失誤。但這是單次補救情境，且 `slide-workflow` + `slide-office-hours` + `pitch-deck` 已大致覆蓋簡報流程。**不建議建立**，除非後續再出現 2 次以上。

#### 3. `markdown-slide-build-pipeline`（markdown → slide 構建流程）

- **Purpose**: 用 `build.js` + `slide0X_xxx.md` 模式組裝簡報。
- **Rationale**: Session 1 出現 `build.js` + `slide01_cover.md` 檔名模式，但既有 `slide-workflow`、`pitch-deck`、`office-pptx` 已涵蓋簡報生成。沒有獨立 skill 化的價值。**不建議建立**。

---

## 建議行動

1. **不立即建立任何 skill**——3 個 session 樣本太薄，且最強候選 `case-study-anonymizer` 也只出現一次。
2. **觀察期**：未來 1–2 週若 `去識別化` / `匿名案例` 再出現 ≥ 2 次，再用 `/skill-creator` 建立 `case-study-anonymizer`。
3. **次優替代**：若不想新增 skill，可考慮把「去識別化 checklist」加進既有 `sales-material` 的 SKILL.md 作為一個小節（公司名 / 人名 / 機台型號 / 產線代號 / 數量級保留量級但模糊化）。

---

## 既有 skill 覆蓋確認

| Session 活動 | 既有 skill | 是否需強化 |
|------------|-----------|-----------|
| 投資研究 daily 報告 | `investment-research` | ✓ 已運作 |
| CRM projection | `crm-projection` | ✓ 已運作 |
| 為特定客戶組裝提案 | `sales-material` | ✓ 已覆蓋 |
| 簡報生成 | `slide-workflow` / `pitch-deck` | ✓ 已覆蓋 |
| 客戶情蒐 | `customer-intel` | ✓ 已覆蓋 |
| **真實案例 → 匿名案例卡** | **無** | ⚠️ 候選但樣本不足 |
