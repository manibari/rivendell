---
date: 2026-05-03
iso_week: 2026-W18
period: 2026-04-27 to 2026-05-03 (last 7 days)
source: workflow-retro
---

# Workflow Retro — 2026-W18

## TL;DR

本週主軸是 **deck-building**：`slide-workflow` (6) + `office-pptx` (4) + `pitch-deck` (3) + `slide-template-extractor` (2) + `sales-material` (2) 合計 17 次觸發；同時今天新增 `slide-office-hours` skill 並 codify「storyline review = leverage point」哲學。系統健康面：所有 13 個 launchd agent exit 0、tester 連續 PASS、但 dashboard 本週經歷 6 次 watchdog 事件（含 4/27 半損 .next build 連鎖崩潰、5/1 一次延遲 1 小時復原）。Token 集中度高：news-stock + Peter-Work 兩專案吃掉 66% 週費用。

## 使用度

| Status | Skills | Agents |
|--------|--------|--------|
| 高頻 (5+) | `slide-workflow` (6) | — |
| 低頻 (2-4) | `office-pptx` (4)、`pitch-deck` (3)、`crm-projection` (3)、`customer-intel` (2)、`investment-research` (2)、`session-harvest` (2)、`skill-scout` (2)、`slide-template-extractor` (2)、`subsidy-scraper` (2)、`requirement` (2)、`sales-material` (2)、`gstack-office-hours` (2) | 13/13 全部 loaded、exit 0（rivendell 7 + news_stock 2 + sales-assistant 4） |
| 沉寂 (30+ days) | `knowledge-graph` (49d, 已建未用)、`ui-ux-pro-max` (54d, frontend-design 取代)、`mcp-builder`/`swiftui-patterns` (54-55d, 仍合理)、`telegram-bot`/`claude-to-telegram` (49d)、`audit-fix`/`ci-pipeline`/`setup-permissions`/`init-project`/`plan-check-style`/`qa-testing`/`headless-agent` (32-50d)、`gdrive-to-skills` (49d)、`destructive-command-guard`/`code-reviewer`/`security-review`/`review-pr` (>50d, 已被 gstack-* 取代) | 7 個 project-side agent 顯示 ○ unloaded（news_stock 的 maintainer/tester/developer + sales-assistant 全部 4 個）— 是排程未啟動，不是失敗 |

**值得注意**：
- 本週新增/活躍編輯了 5 個 skill（`slide-office-hours` 新建未 commit、`launchd-agent` 5 次修訂、`auto-stage`/`protect-secrets`/`skill-scout` 各 2 次）— 是 skill 維運高峰週。
- `knowledge-graph` 建立於 2026-03-11、最後觸發 2026-03-15 後再無使用。其他「沉寂」skill 多數是已被 gstack-* 系列覆蓋（合理），但 knowledge-graph 是「建好沒人用」— 需檢查是 description 沒對齊還是真不需要。
- `slide-office-hours`（今天剛建）已被使用 1 次、`workflow-retro`（本月 7 號建）今天才被觸發 — 兩個 meta skill 的 dogfood 還在熱身。

## 重複痛點

### Theme 1: Dashboard / Next.js build 穩定性
- **頻率**: 4 次跨 sources（`.learnings/` 2026-04-26 KeepAlive 不抓 hung process、2026-04-27 half-built .next、2026-04-28 diff-before-replace；`reports/watchdog.log` 6 次事件）
- **類別**: **Architectural** — watchdog 修補了 hung process 這個 class，但「壞 build cache → restart 也救不回」這個 class 還活著。
- **代表性事件**: 2026-04-27 11:35–12:03 web 連續 9 次 RESTART 失敗（.next 半損）；2026-05-01 18:53 API fail 拖到 19:54 才復原（1 小時延遲）；2026-05-03 10:54 api+web 同步 fail。
- **建議**: 實作 `.learnings/LEARNINGS.md` 2026-04-27 已寫好的 sentinel file pattern（`.next/.build-complete` 取代 `BUILD_ID` 作為 build commit point），讓 `start-web.sh` 真的能偵測半損 build 而不是看 BUILD_ID 假性 OK。

### Theme 2: 通路商 (channel-partner) 客戶分層的 skill 缺口
- **頻率**: 3 次跨 harvest（2026-04-24 `channel-partner-intake` Moderate、2026-04-30 `channel-partner-deck-pack` Moderate→Strong、04-30 customer-intel session 中華電 master deck 反向萃取 119 次 Edit）
- **類別**: **Editorial** — 既有 `presales-pipeline` 採平坦 `01_presales/<client-slug>/`，不表達「通路商→終端客戶」雙層結構；customer-intel 因此被 meta-work 污染。
- **代表性事件**: 中華電 master deck → `BRAND.md` + `tokens.json` + `EXAMPLE-2-FOOD-INDUSTRY.md` 三件式 pack（光泉、永豐紙業、立積電子等多客戶共用）。
- **建議**: 不立即新建 skill — 等「另一個通路」（非中華電）出現時才抽取 `channel-partner-pipeline`，避免把中華電的特殊規格寫死成假設。現階段在 `presales-pipeline` README 補一節說明雙層資料夾與 brand pack 抽取流程（成本低）。

### Theme 3: Skill audit 報告自身的描述錯置（資料品質）
- **頻率**: 5+ 次（`reports/skill-audit-2026-05-03.md` 的「全部 Skills 功能一覽」表中至少 6 個 skill 描述明顯錯置 — `workflow-retro` 顯示 sync-readme 的描述、`client-kickoff-docs` 顯示 telegram-bot、`env-doctor` 顯示 dispatching-parallel-agents、`mops-financial-scraper`/`presales-pipeline`/`repro-exam` 顯示 mockup/planning-with-files、`slide-office-hours` 顯示 rfq-writer）
- **類別**: **Mechanical** — audit 產生器的 frontmatter 解析錯（疑似分類路徑/檔名 mapping bug）。連續 6 天的 audit 都呈現同樣問題。
- **建議**: 修 `bin/sk audit` 的 frontmatter 讀取邏輯。優先級不高（人類靠檔名也能對應），但 audit 本身是給人類讀的，這個 bug 持續產出錯誤資訊會侵蝕 audit 報告的信任度。

## 集中度

- **Token 集中**: news-stock $1533 (35%) + Peter-Work $1334 (31%) = 66% 週費用。news-stock 受「六大指標 grading pipeline」推動本週 28 個 commit；Peter-Work 受 customer-intel + 中華電 master deck 反向萃取推動。兩者都是「正在重度建設」階段，預期下週收斂；但若同樣比例維持兩週以上，值得問「這是該專案最該用的工具嗎」。
- **單日峰值**: 2026-05-03 (今天) 7.55M tokens / $3803 / 22 sessions（含本次 retro 對話），是本週最高 — 主要來自 deck-building + slide-office-hours skill design。
- **失敗集中**: 0 個 agent 有 non-zero exit。Dashboard 是唯一失敗集中點 — 6 次 watchdog event（5 次自動復原、1 次延遲到 1 小時 = 5/1 18:53）。
- **Dashboard 健康**: 每週 6 次 watchdog fire 不是穩態。重啟頻率 = 「watchdog 在工作但根因沒解」。
- **Audit issues**: 18 個（較 2026-04-27 的 29 個下降 38%）— 主要改善是部署從 11 missing → 0、symlink 100% OK。剩餘多為 missing tags / version frontmatter。

## 下週 Actions (max 3, prioritized)

1. **修 `dashboard-next/start-web.sh` 的 sentinel file build 偵測** — Why now: `.learnings/` 2026-04-27 已寫明完整方案（`.next/.build-complete` sentinel）、watchdog 5/1 + 5/3 持續見到此 class of bug、修法是 1 行 sentinel + 1 個 if 判斷。Est. effort: 30 min。Expected impact: 消除 watchdog event 主要來源，dashboard 自我修復能力從「重啟 process」升級到「重新 build」。

2. **`presales-pipeline` README 補「通路媒介客戶」段落** — Why now: harvest 連續 2 週浮現 channel-partner pattern、customer-intel session 因此持續被 meta-work 污染。先用文字 codify 慣例（`YYYYMM_通路商/終端客戶名/` + brand pack 三件式），等下次第二個通路出現再決定是否抽 skill。Est. effort: 1 hr markdown。Expected impact: 防止 customer-intel skill 自身被在客戶研究 session 中反覆改寫。

3. **檢查 `knowledge-graph` skill description 對齊度** — Why now: 建立 49 天無觸發、最近一次使用是建立後 4 天。要嘛 description 沒對齊真實 trigger 詞、要嘛這個 skill 真的沒 fit。Est. effort: 15 min（讀 SKILL.md 對照 .learnings 找未觸發但應觸發的 case）。Expected impact: 決策保留 / 改 description / 退休 — 三選一，不再放著佔空間。

> 備註：Theme 3（audit 報告描述錯置）本週不列入 actions — 影響範圍僅限可讀性、且修 audit 解析器需要的 effort（>1 hr）跟 impact 比不上前三項。記錄在此供下週若仍存在再升級。

## 對照上週

跳過 — 本檔為第一次正式 retro（找不到 `reports/workflow-retro-2026-W17.md` 或更早的）。下週會回填上週 actions 完成度。
