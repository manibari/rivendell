# Requirement: Dashboard Redesign (rivendell-next)

**Target User:** 個人（manibari / Peter）— rivendell 的唯一日常使用者
**Problem:** 8 個頁面（landing / agents / harvest / ports / projects / skills / tokens / workflow）視覺不一致、無共用 design system；workflow map 把 CoreTrack / DomainFlow / Maintenance / Situational / Orphan 攤平在同一頁，看不出層級與依賴。
**Trigger:** Skills 從 46 → 90+，workflow 邏輯（A/B/C/D 路徑、Gate 0/Pre-flight、companion skills）越來越深，現有平面陳列已撐不住。

**Tech Stack:** Next.js 16 + Tailwind（已在 dashboard-next/）
**Out of session:** 不動 backend / API，不加新頁

---

## User Stories

### US-1: 鎖定 Design System（DESIGN.md 為 SSOT）

**As a** dashboard 使用者
**I want to** 8 個頁面共用同一套色盤、字型、spacing、圓角、icon style
**So that** 跨頁切換不會有「進到不同 app」的錯亂感

**Acceptance Criteria:**
- [ ] `dashboard-next/DESIGN.md` 存在並定義：色盤、字型、spacing scale、border radius、shadow、icon family
- [ ] `globals.css` 把 design tokens 寫成 CSS variables（`--color-bg`, `--color-fg`, `--space-*`, `--radius-*`）
- [ ] 8 個 page 的硬寫色碼 / 字型 / spacing 全部移除，改用 token
- [ ] DESIGN.md 提到的 token 在至少 6 個 page 被實際使用（grep 驗證）

---

### US-2: Workflow Map 改用 Tree / DAG 顯示層級結構

**As a** dashboard 使用者
**I want to** 在 workflow page 看到 CoreTrack → CoreStep → skills 的層層展開（tree 或 DAG）
**So that** 一眼看出「UI Feature flow 走到 step 5 mockup 的時候會用哪些 skills」這種層級資訊

**Acceptance Criteria:**
- [ ] CoreTrack（如 UI Feature / Backend / Slide）顯示為頂層節點
- [ ] 每個 CoreStep 是子節點，展開後顯示 mandatory + optional skills
- [ ] DomainFlow（presales / sales-customer-intel 等）以另一棵 tree 並列或切換 tab 顯示
- [ ] Maintenance / Situational / Orphan 不擠進主 tree —— 用獨立區塊或側欄
- [ ] 點擊節點可摺疊 / 展開
- [ ] 在筆電（1440px）一個畫面看得完主流程，不需要橫向捲動

---

### US-3: Skill-as-Center 反向交叉引用

**As a** dashboard 使用者（特別是寫了某個 skill 不確定它怎麼被引用時）
**I want to** 點一個 skill node，看到它在哪些 CoreTrack / CoreStep / DomainFlow / Maintenance 出現
**So that** 我能驗證 skill 是不是 orphan、是不是被引用得太多（職責不清）

**Acceptance Criteria:**
- [ ] 點擊 tree 中的 skill node → 側欄或 modal 顯示「此 skill 出現在：UI Feature step 5 (mandatory) / Slide Building step 4 (optional) / ...」
- [ ] 出現次數為 0 → 標為 orphan（紅色 / 警示 icon）
- [ ] 從側欄可一鍵跳到 `/skills/{name}` 詳細頁

---

### US-4: 8 頁全面套用新 design system

**As a** dashboard 使用者
**I want to** landing / agents / harvest / ports / projects / skills / tokens 7 個頁面（外加重做的 workflow）都使用新的 design tokens
**So that** 達到「視覺一致」這個成功標準

**Acceptance Criteria:**
- [ ] 7 個 page 完成 DESIGN.md token 替換
- [ ] 跨頁的 navbar / header / card / table / button 樣式統一
- [ ] dev-mode 啟動 `pnpm dev` 不報 lint / type 錯
- [ ] Peter 自驗：8 個頁面切換不再有「醜或亂」的主觀感受

---

## Scope Boundary

| In Scope | Out of Scope |
|----------|-------------|
| 8 個 frontend page 的視覺重做 | Backend API 重構（FastAPI 部分） |
| `dashboard-next/DESIGN.md` 建立 | 新頁 / 新功能（如 cron 編輯器） |
| `globals.css` token 化 | 行動裝置 responsive（dashboard 是桌面工具） |
| Workflow page 改 tree / DAG | 多人帳號 / RBAC（單人工具） |
| Skill cross-reference 互動 | 後端資料模型改動 |
| 跨頁元件抽象（navbar / card / table） | i18n（中文寫死） |
| 設計討論文件 + mockup | 動畫 / motion design（除非極簡 hover） |

---

## 成功驗收（user-confirmed）

主驗收：**「視覺一致 + workflow map 不再亂」**——主觀感受。Peter 在完成後實際使用 30 分鐘，自我評估是否還有「醜或亂」的主觀痛感。

次驗收（客觀）：
- DESIGN.md 存在
- 至少 6 個 page 用了 token
- workflow page 主流程在 1440px 一個畫面看完
- 點 skill node 能反查出現位置

---

## 階段規劃（建議）

雖然 user 選了「全套一起做」，建議內部仍分兩段交付以降低風險：

1. **Stage 1 (Design + Workflow map)**: DESIGN.md → workflow page 重做（最大痛點）
2. **Stage 2 (Apply tokens)**: 其他 7 頁逐頁套用 design tokens

每階段可獨立驗收，避免 8 頁同時改 → debug 災難。

---

## Next Step

Per `### UI Feature / New Page` flow:

| Step | Skill | Purpose |
|------|-------|---------|
| 2 | `/user-flow` | 確認 workflow map 的互動流程（展開 / 收合 / 點選 / 跳轉） |
| 3 | `/gstack-design-consultation` | 鎖 DESIGN.md（色盤、字型、spacing、icon style） |
| 4 | `/gstack-design-shotgun` | 跑 workflow map 的 3-5 個視覺變體（tree / sankey / radial / DAG）讓 Peter 挑 |
| 5 | `/mockup` → `/gstack-design-html` | 把選中的變體做成 production-ready HTML |
| 6 | `/planning-with-files` → `/gstack-plan-eng-review` | 拆 task list + 架構審 |
