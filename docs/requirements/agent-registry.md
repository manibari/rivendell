# Agent Registry Schema — Requirement

> Status: draft v2
> Date: 2026-07-23（v1）→ 2026-07-27（v2：雙層模型修訂）
> Decided in-session: 涵蓋範圍=全部統一（kind 欄位）；遷移深度=schema + 全量轉檔；
> 第一個 OODA 大臣=Check 品質官
> Upstream vision: 「上朝」agent 系統（見 memory: agent-system-vision）
> This phase = Lever 1 of 3（registry SoT）。Lever 2（wake executor）、Lever 3（inbox 佇列）另立 requirement。

## 一句話

一個 agent 一個 markdown 檔，作為所有排程單位的單一事實來源——worker（單工腳本）
與 OODA 大臣（有人格、有 mission、自主決策）共用同一個 registry，靠 `kind` 區分；
本期交付 schema + 全量轉檔 + 第一個大臣（Check 品質官）的 registry 定義。

## 雙層迴圈模型（v2 核心修訂）

現行 rivendell agent 全是 **worker**：cron 觸發 → 固定 script → 固定輸出，工作寫死。
目標系統是雙層：

- **微觀（每個大臣獨立的 OODA）**：醒來一次跑一圈——
  Observe（讀世界狀態 + 自己的 journal）→ Orient(persona 規則層 + mission)→
  Decide（在 skill 白名單內挑本次行動；超出授權 → 寫奏摺請示，不硬幹）→
  Act（執行、寫回 journal、必要時交接）。
- **宏觀（艦隊合成一個 PDCA）**：每個大臣的人物目標對應 PDCA 一環，
  交接拓撲由角色決定：Plan 產出 → Do 的 inbox；Check 驗 Do 的產出；
  Check 的發現 → Act；Act 的改善回饋 Plan。皇帝（user）批 Plan、裁爭議。

worker 不升級、不淘汰——留著當手腳（零 API、決定性），大臣 observe worker 的
報告、必要時往 inbox 派工。cron 對大臣而言只是**心跳**，不是工作內容。

## Why now

- 「persona × 工作項目 × skill 權限」目前都不在執行路徑上：`agent-persona` skill
  是未實作的規格（`.claude/personas/` 不存在），`agents.conf` 無權限欄位。
- agent 身分散落三處（agents.conf / 各 cron script / `.claude/agents.json`）。
- 對齊既有決策：persona-card 架構（規則層 > 敘述層；worker projection 首個真實
  案例）、markdown-file-ssot、fleet-infra-spine 抽取原則（OODA 欄位由第一個真實
  大臣定，不憑空設計）、`agent-*` naming series。

## 目標使用者

Solo dev（Peter）+ 機器消費者：`sk-setup-agents`（排程生成）、dashboard-next
（顯示）、Lever 2 的 wake executor（未來）。

---

## Schema（草案 v2）

檔案位置：`agents/registry/<name>.md`。

```yaml
---
schema_version: 2        # v2: 加入 ooda kind 與自主層欄位
name: harvest            # unique, kebab-case；檔名必須等於 name
kind: script             # script | claude | service | ooda
enabled: true            # false = 不生成排程（取代註解掉 conf 行）
project: rivendell       # 相對 PROJECTS_DIR，禁止絕對路徑（repo-rename 規則）
entry: bin/sk-harvest-cron   # script/claude/service 必填；ooda 留空（走通用 executor）
extra_args: ""

schedule:
  type: interval         # interval | calendar | calendar_multi | keepalive
  value: 28800           # ooda 語意 = 心跳（醒來），不是工作觸發
log_dir: reports
label: ""                # optional 覆寫；預設衍生 com.sk.agent.<project>.<name>
                         # legacy 服務（com.sk.dashboard.api 等）用此欄保留舊 label

# ─── kind: claude | ooda 共用（規則層 — 機器可判定，executor 強制） ───
skills: []               # skill 白名單 = Act 的 action space
tools: ""                # --allowedTools 最小權限
paths_forbid: []
budget_usd: 0            # 單次醒來上限

# ─── 僅 kind: ooda（自主層 — 由第一個真實大臣「品質官」定案的欄位） ───
pdca_role: check         # plan | do | check | act — 決定宏觀交接拓撲
mission: ""              # 目標狀態（不是 task）：一句話說「世界維持在什麼樣子」
mission_metric: ""       # 可判定的達成指標（先例：autoresearch 的 goal+metric）
memory_dir: agents/state/<name>/   # journal.md + backlog.md；醒來先讀、睡前寫
observe: []              # Observe 允許讀的世界狀態來源（路徑 / DB read-only）
authority:               # Decide 的授權邊界（語意層；tools/paths 是強制層）
  can: []                #   授權內可直接 Act 的行動類型
  escalate: []           #   超出授權 → 寫奏摺（Lever 3 前先寫到 reports/court/）
handoff:
  on_finding: ""         # Check 發現問題交給誰（PDCA 拓撲的一條邊）

persona_card: docs/personas/<name>.md   # optional 敘述層 ref（worker projection）
---

## Mission（敘述層）

自由書寫：口吻、判斷準則的背景、輸出格式範例。executor 只當 prompt 素材；
一切強制走 frontmatter 規則層。
```

Schema 設計原則：

1. **規則層 > 敘述層**：要被機器強制/驗證的都在 frontmatter；body 只放敘述。
2. **kind 決定必填欄位**：`script`/`service` 只需排程層；`claude`（有 prompt 的
   單工 worker）加規則層；`ooda` 再加自主層。
3. **自主層欄位以品質官為準**：只加品質官實際用到的欄位（fleet-infra-spine 原則），
   第二個大臣（Act 維修官）上線時再擴充。加欄位不 bump、改語意才 bump。

---

## User Stories

### US-1: 一個檔案定義一個 agent

**As a** solo dev
**I want to** 新增/修改 agent 時只編輯 `agents/registry/<name>.md` 一個檔案
**So that** agent 身分有單一事實來源，不再散落三處

**Acceptance Criteria:**
- [ ] Given registry 目錄，when 新增合法的 `<name>.md`，then `sk-setup-agents` 重跑後該 agent 的 plist 被生成並載入
- [ ] Given `enabled: false`，when 重跑，then 不生成該 plist（已載入的被 bootout）
- [ ] Given 檔名與 `name` 不一致，when 生成，then 報錯退出、不產生半套

### US-2: agents.conf 變成生成物

**As a** 排程管線（`sk-setup-agents`）
**I want to** 執行時從 registry 現場生成 conf（不進 git 的 build 暫存）再走既有 plist 流程
**So that** 既有 bash 管線改動最小（增量接線），且只有一份 committed 正本（registry）

> 定案（eng-review 2026-07-28, D3-topology）：agents.conf **不進 git**。`sk-setup-agents`
> 開頭呼 `sk-registry-gen generate` 產暫存 conf、跑完丟。無雙軌 SoT → drift 偵測自然成立
> （生成失敗即 drift）。取代原「conf 標 GENERATED 並 commit」設計。

**Acceptance Criteria:**
- [ ] Given 全量轉檔後的 registry，when `sk-registry-gen generate`，then 輸出與搬移前 HEAD conf 的**行為等價**（label、schedule、log_dir、extra_args 全比對通過）
- [ ] Given `sk-setup-agents` 執行，then 現場生成暫存 conf、跑完刪除；`.gitignore` 含 `agents/agents.conf`
- [ ] Given registry 檔壞掉（生成失敗），when `sk-ssot-drift-cron` 呼 `--check`，then 回報 drift

### US-3: Schema 驗證進健檢

**As a** `sk-tester-cron`（或 `bin/sk audit`）
**I want to** 每日驗證所有 registry 檔的 schema
**So that** 壞掉的 agent 定義在生效前被抓到

**Acceptance Criteria:**
- [ ] Given 缺該 kind 的必填欄位，then 標 FAIL
- [ ] Given `skills` 列了 `~/.claude/skills/` 不存在的 skill，then 標 FAIL（built-in skill 沿用既有 audit 豁免規則）
- [ ] Given `kind: ooda` 但缺 mission / pdca_role / memory_dir，then 標 FAIL
- [ ] Given `persona_card` 或 `observe` 指向不存在的路徑，then 標 WARN
- [ ] Given `name` 重複或衍生 label 撞名，then 標 FAIL

### US-4: Dashboard 讀 registry 顯示 agent 卡

**As a** dashboard 使用者
**I want to** 在 agents 頁看到 registry 身分（kind、pdca_role、mission、skills、schedule、enabled）
**So that** 未來「朝會」視圖有資料層可接

**Acceptance Criteria:**
- [ ] Given registry 檔存在，when 開 `agents/[label]` 頁，then 顯示至少 kind / schedule / skills / enabled；ooda 另顯示 pdca_role + mission
- [ ] Given agent 只在 DB 有執行紀錄、registry 無檔，then 正常顯示紀錄並標「未註冊」，不噴錯

### US-5: 全量轉檔（含除役標記）

**As a** solo dev
**I want to** 把現行 agents.conf 全部條目機械轉為 registry 檔
**So that** 不留雙軌 SoT

**Acceptance Criteria:**
- [ ] Given 轉檔完成，then conf 每一有效行都有對應 registry 檔，生成結果與轉檔前 HEAD conf 行為等價
- [ ] Given sales-assistant 已宣告 deprecated 但仍在跑，when 轉檔，then 4 個 sales agent **保留 `enabled: true`**（純機械搬移不打斷現跑 agent）+ body 註記「退役待 chimesflow ready，屆時單獨 commit 改 false」
- [ ] Given 被註解的 autoresearch 條目，then 轉為 `enabled: false` 的 registry 檔（唯一預期的狀態差異）

> 定案（eng-review 2026-07-28, D2-sales）：原「sales 標 enabled:false」與「逐條等價」矛盾——
> sales 現為 active，disable 會讓 diff≠0 且 bootout 4 個活躍 agent。改純機械搬移，退役分開決策。

### US-6: 第一個 OODA 大臣 — Check 品質官（registry 定義）

**As a** 皇帝（user）
**I want to** 用 registry 定義一個 Check 品質官：mission = 「worker 報告有人判讀，
異常在一個心跳內變成奏摺」，observe = reports/ + dashboard DB，authority =
只能寫朝報/奏摺/inbox 項目、不能改 code
**So that** OODA 自主層欄位由真實案例定案，且 Lever 2 executor 一上線就有第一個乘客

**Acceptance Criteria:**
- [ ] Given `agents/registry/quality-minister.md`（名稱暫定），then 通過 US-3 的 ooda schema 驗證
- [ ] Given 該檔 `enabled: false`（executor 未到位前不排程），then 生成器跳過它且不報錯
- [ ] Given 自主層任何欄位，then 品質官檔案裡該欄位有真實值（不留空殼欄位——用不到的欄位從 schema 刪掉）
- [ ] Given `memory_dir`，then `agents/state/quality-minister/` 建立且含 journal.md 空模板（醒來讀/睡前寫的格式先定好）

---

## Scope

| In Scope（本期） | Out of Scope（後續） |
|----------------|-------------------|
| Registry schema v2 + template 檔 | Lever 2：wake executor（讀 registry 組 OODA prompt、強制權限、跑品質官） |
| registry → agents.conf 生成器 | Lever 3：`agents/inbox/` 佇列與 PDCA 交接觸發 |
| 全量轉檔（含 sales 除役標記） | 朝會 digest UI、批示按鈕、Telegram 批奏摺 |
| schema 驗證接入 tester-cron / sk audit | 品質官實際執行與朝報產出（= Lever 2 驗收） |
| 品質官 registry 檔 + memory 模板（US-6，enabled: false） | 第二個大臣（Act 維修官）與其欄位擴充 |
| dashboard agent 卡讀 registry 欄位 | persona card 內容撰寫（只留 ref 欄位） |

## 依賴與既有規則對齊

- `project` 相對路徑、label 衍生 —— 遵守「Never hardcode the repo/project name」。
- 品質官的 observe 含 `reports/`：它是 reports 的**讀者**，朝報寫到獨立位置
  （建議 `reports/court/`，沿用 reports 由 agent own 的 curation 規則）。
- `agent-persona` skill 本期不改版；Lever 2 時升級為讀 persona_card 編譯 worker
  projection 的消費者。
- Skill 命名：後續抽 skill 歸 `agent-*` series。

## Open Questions（留給 plan 階段）

1. 生成器語言：擴 `sk-setup-agents`（bash 解析 frontmatter 難看）vs 小 python 工具
   （repo 已有 dashboard python 環境）。傾向 python 產 conf、bash 管線不動。
2. `.claude/agents.json` 是否併入 registry 淘汰？（plan 時盤點 dashboard 實際依賴。）
3. 奏摺格式（frontmatter 欄位、放 `reports/court/` 還是未來 `agents/inbox/`）——
   Lever 3 定案，本期品質官 registry 只在 authority.escalate 描述行動類型。
