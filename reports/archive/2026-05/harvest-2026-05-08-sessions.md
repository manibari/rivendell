# Session Harvest — 2026-05-08

## 整體摘要

| 項目 | 數值 |
|------|------|
| Session 數 | 4 |
| 總訊息數 | ~178 |
| 主要工具 | Bash(49) · Write(39) · Edit(33) · WebSearch(18) · Read(14) |
| Skill 觸發 | iot-factory-report, crm-projection, investment-research |

---

## Session 列表

### [1] Peter-Family · 96 msgs
- **主題**：與女友（吳欣曄）結婚的第一個五年計劃
- **核心方針**：月薪扛家（防禦）／獎金圓夢（體驗）／資產護航（防火牆）／教育賦能（長線投資）
- **產出檔案**：`2026-H2-kickoff.md`、`2026-H2-preparation.md`、`CLAUDE.md`、`INDEX.md`、`LEARNINGS.md`
- **工具分布**：Write(37) · Edit(22) · Bash(19) · Read(6)
- **判斷**：屬「個人/家庭長期計劃」的結構化文件協作，現有 skill 庫未覆蓋此情境。

### [2] Peter-Work · 19 msgs
- **主題**：SDP 提供 3 月 RO 每分鐘數據 CSV，呼叫 `iot-factory-report` skill 進行對齊分析
- **產出檔案**：`alignment-report.md`
- **工具分布**：Bash(14) · Skill(1) · Write(1)
- **判斷**：完全走既有 skill 流程，無新候選。

### [3] news-stock · 43 msgs
- **主題**：`investment-research` Continuous Mode，讀取 portfolio reports 並執行每日研究
- **產出檔案**：`daily-2026-05-08.md`、`portfolio-state.json`
- **工具分布**：WebSearch(18) · Edit(11) · Bash(6) · TodoWrite(4)
- **判斷**：完全走既有 skill 流程，無新候選。

### [4] sales-assistant · 20 msgs
- **主題**：`crm-projection` skill 投影 nx_client + nx_deal → 本地 markdown
- **產出檔案**：`INDEX.md`、`crm-projection.sh`、`projection.md`
- **工具分布**：Bash(10) · Read(7) · Skill(1)
- **判斷**：完全走既有 skill 流程，無新候選。

---

## Skill 候選評估

### 🟢 Strong

#### 1. `couple-life-planning`
- **目的**：協助使用者與伴侶共同制定多年期（3–5 年）人生 + 財務規劃文件，涵蓋四大支柱：防禦（月薪扛家）／體驗（獎金圓夢）／護航（資產防火牆）／賦能（教育投資）
- **觸發**：使用者說「五年計劃」「結婚規劃」「家庭財務架構」「couple plan」「life planning」「夫妻財務分工」「圓夢基金」
- **不觸發**：純投資組合規劃（用 `investment-research`）、商業 OKR（用 `requirement`）、單純個人記帳
- **分類**：`workflow/`
- **理由**：Session 1 共 96 訊息全在處理這類結構化規劃，使用者明確區分四帳戶/四支柱框架，且產出 INDEX.md + LEARNINGS.md 顯示這是會反覆使用的長期文件結構。現有 skill 庫沒有對應的個人/家庭規劃模板，但該框架（三獨立帳戶 + 教育長線）是可重用的。
- **預期模板**：`vision.md`、`finance-architecture.md`、`milestones-by-quarter.md`、`risk-firewall.md`、`learning-budget.md`、`INDEX.md`

### 🟡 Moderate

#### 2. `half-year-kickoff`
- **目的**：每半年（H1/H2）一次的個人/家庭 kickoff 流程，產出 `YYYY-H{1,2}-preparation.md`（前置盤點）+ `YYYY-H{1,2}-kickoff.md`（正式啟動），含目標、預算、里程碑、回顧上季
- **觸發**：使用者說「H2 啟動」「下半年計劃」「半年回顧」「preparation doc」「kickoff doc」「年中規劃」
- **不觸發**：每週/每月例會（太頻繁、不需 skill）、商業季報（用 `gstack-retro`）
- **分類**：`workflow/`
- **理由**：Session 1 出現明確的 `2026-H2-preparation.md` + `2026-H2-kickoff.md` 雙檔模式，這是可被多個專案/家庭/個人重複使用的節奏。但和 #1 有部分重疊，若採納 #1 可能合併。

### 🔴 Weak

#### 3. `local-port-audit`
- **目的**：列出本機目前佔用中的 port，協助避開衝突（`netstat`/`lsof` + 整理輸出）
- **觸發**：「盤一下現在的 port 有用的有哪些」「port 衝突」「哪些 port 在跑」
- **理由**：太薄、單一 bash 一行解決，不值得獨立 skill；可放進現有 `env-doctor` 或寫進 CLAUDE.md。

---

## 建議採納順序

1. **先做 `couple-life-planning`**（Strong）— 補上人生規劃這一塊空白，框架已被使用者驗證一輪
2. **暫緩 `half-year-kickoff`** — 等再出現一次 H1/H2 文件後再評估，或併入 #1 作為 sub-template
3. **不做 `local-port-audit`** — 改用 `env-doctor` 補一個 port check 子模組即可

---

## 既有 skill 命中觀察

- `iot-factory-report`、`crm-projection`、`investment-research` 三者本週都被正確觸發、產出檔案正常，flow 健康
- WebSearch 在 `investment-research` session 用了 18 次，是最高 tool — 符合該 skill 的「主動爬資訊源」設計，無需調整
