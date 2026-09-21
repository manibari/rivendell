# Changelog

Versioning: `MAJOR.MINOR.PATCH`(規則取自 PTI-ARES,fleet 共用慣例)。

- **PATCH**(第 3 碼)— 每次 push(碰 skills/dashboard/bin;`reports/*` 不算)。
- **MINOR**(第 2 碼)— 一個過 gate 的 initiative/Wave 項完成
  (eng-review / QA / office-hours design doc 任一 gate)。
- **MAJOR**(第 1 碼)— 只在產品負責人(Peter)明示時。

本檔是 release notes 的 **single source of truth**,與根目錄 `VERSION` 同步。
cut 一版:bump `VERSION` → 本檔前置一段 → `release: cut X.Y.Z — 主題` commit。

**Granularity rule(承 PTI-ARES 2026-07-01):事無大小都要寫上** —— 每個 shipped
feature/fix 一條 bullet 帶短 hash;不把多個修正捲成一條模糊敘述。進行中的放
`## Unreleased`。

## Unreleased

- 資料夾架構第一階段：應用、Agent、部署設定、助理通道、知識內容及部分平台規則移到各自模組；舊路徑保留相容入口，CI 與 Compose 改讀新位置。後續仍需抽離 `dashboard-legacy/lib` 剩餘規則與 `bin/sk` 的跨模組邏輯。
- 資料夾架構第二階段：API 路由按 Agent、專案、技能目錄、工作流程、協作、Harvest、部署及監控子功能拆模組，主檔只組裝應用；`sk` 部署與狀態指令回到所屬平台模組；工作流程設定由 Compose 掛載新位置，修正技能角色文件路徑並保留原本 API 路徑。

## 0.3.0 — skill loop 分類法 × 個人助理層 × agent registry v2 — 2026-09-16

> **回填說明**：0.2.2（2026-07-19）之後兩個月沒有 cut 版，累積 125 個非 reports
> commit。repo 沒有 git tag 可以錨定中間點，事後拆成多個 MINOR 等於是在發明歷史，
> 所以整段收斂成一個 0.3.0，依 initiative 分節、每條帶短 hash。granularity rule
> 從下一版恢復逐條即時記錄。

### skills 分類法：loop(subject)-object-action + PDCA

- **全庫重編為 15 個 loop 分類**（`3c6b7b9` 計畫 → wave 1 `f344ad2` `9ca631b`
  `578d007` `e2fa5c2` `95c4ec6` → wave 2 `222d481`）。`business/`、`media/`、
  `meta/` 三個以「像什麼」命名的資料夾解散，改以「屬於哪條 loop」歸戶：
  sales / gov / invest / hr / knowledge / platform 各自成 loop。
- **命名文法 v2 + PDCA frontmatter**（`56e8ddc` `107511c`）。124 個 skill 全數
  補上 `loop` / `pdca` 欄位,catalog 產出 Loop×PDCA 覆蓋表,frontmatter 值進 lint。
- **skills-by-role 八份角色 playbook**（`1fea6f9`）,`sk check` 守覆蓋率;角色頁
  改以 authority tier 分組（`5353e72` `a57d2cb` `b4fee6b`）。
- **dashboard `/skills` 改畫真實架構**（`ef1b848` `f1f8b7f` `e0e3b87`）——
  loop × PDCA 熱圖、角色 → 工作 → PDCA 結構檢視,sidebar 依「你在做什麼」重組。
- **繪圖 trigger 收斂到 chart-design**（`50b9189` `650a8db`）,附機械式 figure
  checker 與 three-claim handoff receipt。
- **system-design skill**（`630758c`）—— 補上沒人在產出的 SA/SD 環節。

### 個人助理層：知識庫 → dispatch → avatar

- **assistant stack 落地**（`15b17fe`）—— knowledge base、dispatch loop、avatar
  三件一起進 main。
- **`sk dispatch` 行動層**：模糊指令/信件事件 → 具體化提案（引知識庫）→ 分級確認
  （email/calendar 逐件 typed-yes、垃圾信批次、crm 放行、internal 自動）→ 確定性
  actuator 執行。模型永不執行寄送,payload hash 防竄改。
- **`bin/sk-mail-triage-cron`**（daily 7:45）：重要信摘要推播、垃圾信 sk-junk 貼標
  + 批次確認（永不 expunge,junk-guard 保護知識庫已知寄件人）、可行動事件自動開提案;
  業務行為路由 Rightek-CRM。
- **knowledge-graph 啟用**（翻案,原排隊退役）：`scripts/kg.py` 唯一寫入 API
  + `bin/sk-facts-cron`（daily 21:30,知識庫自身 git 為交易邊界）+ `~/.claude/CLAUDE.md`
  recall 區塊。首跑落地 8 筆 facts / 6 entities。
- **avatar**：`/avatar` 頁（VRM 對話視窗、人格切換、引擎與 API 金鑰設定）+ `gateway/`
  （:8310,OpenAI 相容 `/v1/chat/completions`;引擎鏈 codex→claude→API key 直連）。
  雙人格林迪（Lindir）/ 米瑞爾（Míriel）,註冊表 `data/persona.conf`。
  後續 de-slop 助理語氣 + 對話歷史 + neural TTS endpoint（`bae732c`）。
- **link-collection flow**（`0f213f5`）—— 自動分類的連結收藏。
- ports.conf 補登記 mops:8200 與 iihi:8300 兩筆漂移。

### agent registry v2（雙層模型：registry → launchd）

- **schema v2 共用 parser + 第一個 OODA minister**（`1cc1130`）,`sk-registry-gen`
  CLI generate/validate/check（`4829baa`）,20 條 agents.conf 條目全數遷入
  registry（`d38af63`）。
- **`sk-setup-agents` 改由 registry 生成 conf**（`bd10c54`）,`agents.conf` 退為
  不進 git 的 build artifact（`94b03bf`）,registry 驗證接進 health check（`b880123`）。
- **`sk-projects-sync` 回歸**（`9898d95`）—— `~/.claude/projects.json` 在 repo 外、
  不隨 clone 走,先前兩個月無人重建。同時修掉它原本讀死 `agents.conf` 的問題。
- **`sk-setup-agents` 支援指名 label**（`4d5dbb1`）—— 加一個排程不必彈掉正在服務
  流量的 dashboard 與 gateway。

### qa-dataflow：驗證資料流「實際上」怎麼跑

- **skill 本體**（`7310f99`）,七個探針依「問的是什麼問題」拆開（`ee0c17c`）,
  功能關係圖當成維護中的 artefact 而非一次性報告（`26dc4d4`）,
  無出口的帶狀區與會跟著資料移動的基準線（`dd4955e`）。
- QA 家族收攏到 `skills/qa/`,並讓 deploy 不再跳過死連結（`65aef77`）。

### 多機維運與機器搬遷

- **per-machine 報告檔名**（`068a131` `a3b8156` `4a7b8af`）—— 兩台機器合併時
  70 個衝突有 64 個是同名的日期報告（`110d2b7`）。
- **`sk-relocate`**（`d68dd79`）—— 搬 repo 並重建所有記著舊路徑的東西;
  machine-migration 破損修復（`2f2cc60`）。
- **部署前置 preflight gate**（`5c43216`）,`sk-reboot` 無人值守重開機穿過
  FileVault（`04e6a8d`）。
- **BSD/GNU 可攜性**：`sed -i ''` 換掉（`38a07d2`）,`sk audit` 摘要從來沒進過
  報告（`117cd93`）,interval timer 改用 OnActiveSec 不在載入時就開火（`bf44ff7`）。
- WSL prod 改追 main,ROADMAP R1a 關閉（`b5929b9`）。

### 知識 loop：影音 → 知識庫

- **video/media skill 家族**（`c7f3991`）—— transcript / clip / subtitle,
  無字幕自動降級 Whisper（`55ea48e` `17f1ae3`）,持續 429 的 COOKIES 逃生口（`2abad9d`）。
- **`local-media-transcribe`**（`dc0724f`）—— mlx-whisper 全離線本機聽寫;
  本機 ASR 改成大聲失敗而不是吐出流暢的垃圾（`385a3b7`）。
- **知識庫**（`703c331` `97d62e3`）—— 影音筆記歸檔 + 可瀏覽 INDEX.md;
  `channel-scraper` 改成訂閱頻道而非逐條貼連結（`b8ac03d`）。

### gov / sales / 文字品質

- **subsidy-writer**：figures + reapply-from-approved + 分級待補清單（`71d0142`）,
  Phase 8 書面審查意見 → 審查會議簡報（`25da1f4`）;scraper 繞開兩個死掉的入口（`cd4437b`）。
- **`say-it-plain`**（`6702efb`）+ audience calibration（`ae91cf1`）;
  **`de-slopify`** 加 self-assessment 與內部代號掃描（`3966c9f`）。
- **`qa-journey`**（`f39315c`）、**`skill-apply`**（`df2275a`）、
  **`context-journal`**（`04302e7`）、**`pitch-deck` 出 PPTX 前的 copy-review gate**（`1537d08`）。

### 平台工具與 dashboard

- **`sk todo`**（`8501447` `a51c958`）—— 一頁列出還沒了結的事。
- **ports 以 live listener 為 SoT + ownership registry**（`47cf550`）。
- **dual-target deploy**（`d733e04`）—— 同一份 skill 同時進 Claude Code 與 Codex。
- **global hooks manifest**（`95d0882`）—— commit 了腳本不等於裝了 hook;
  auto-stage 重新接線讓描述它的規則重新為真（`4adcce5`）。
- **`sk clean` / `sk rename`**（`e557f56` `45eb5be`）,watchdog 移出 launchctl
  以便 systemd 也抓得到吊死的服務（`b27a54d`）,watchdog 追到網頁真正引用的
  資產（`3f5334d`）。
- dashboard token 重複計算與價格表（`998d945`）,avatar 404 其實是舊的 production
  build（`4674eb5`）,CI ruff 釘版本讓 lint 標準不再自己移動（`e731fc2` `c3257fd`）。

### 檢查工具誠實化

- **不再報告任何動作都清不掉的紅字**（`1ddbb27`）—— `_shared` 不是 skill 卻天天
  FAIL;沒 clone 在本機的專案其 agent 被計入 drift。兩者都改為分開陳述、不計入總數。

## 0.2.2 — tokens 頁誠實化：雙軸吞吐 + 砍幻覺金額 — 2026-07-19

- **fix(tokens): Max 吃到飽用戶的幻覺 $**。舊頁頭條大字是 `$total_cost_usd`
  ($64K),但那是 cache_read × opus 預設價（現役 fable-5 / opus-4-8 根本不在
  價格表→全 fallback opus $15/$75），而 Max 逐 token 實付 $0 → 純虛構。改：
  headline 拆「產出(in+out) / Context 重讀(cache) / 估算花費(API 等值·非實付)」；
  砍掉「每日花費」bar。
- **feat(tokens): context 疊加可視化**。後端 `DailyUsage.cache_tokens` +
  `total_cache_tokens`（read+create）；每日圖改**雙軸並排**（產出左軸·百萬、
  context 右軸·十億——兩者差 ~280× 不能共軸，疊線性軸會壓死產出那條）。
  recharts bar 關 `isAnimationActive`（headless QA 才截得到，rAF 動畫在虛擬
  時間下不觸發→bar 卡高度 0）。

## 0.2.1 — api 死亡螺旋根治 — 2026-07-18

- **fix(api): watchdog death-spiral** — 1GB session 語料冷掃 × 併發疊加 + 每
  agent 一次 launchctl(18s)→ 5s 探針必死 → kickstart 殺 → cache 清空 → 重掃,
  歷史累計 22,474 次重啟。修法:per-file granular JSONL cache(SQLite,
  mtime+size key,老檔一生解析一次)+ launchctl 單次 dump snapshot(5s TTL)+
  探針 5→15s。實測 overview 冷 2.4s/熱 1.4ms、agents 0.69s、tokens 3ms。

## 0.2.0 — 平台月:部署管理 × token 三層 × spine × skeleton — 2026-07-18

> Catch-up cut:0.1.0(6/13)後一個月的主線。當時無 granularity 規則,本段按
> initiative 收攏、每條帶代表 hash;此後恢復逐條記。紅藍隊評估(R1–R7)同日完成,
> 對應 Wave 0–3 見 ROADMAP。

### 部署管理頁(原 Port 對應)
- 當前部署 default + 相關部署 toggle(`31105be`);docker-label 認 owner + 來源
  資料夾 + iCloud 紅旗,解「5432 誰家的」(`76d4023`);改名部署管理(`a712887`)
- 健康維度讀共用 `ops/monitors.toml`(`80f3d6b`);WSL self-host 部署工具
  systemd+git-poll(`8f3e2fa`)+ 可設分支(`0bb5948`)
- `/api/*` 同源 proxy,不再 bake host 進 bundle(`991360d`)
- 系統程序 wild listeners 折疊一列(QA ISSUE-002,`268845d`)

### Token 三層
- 歸因收斂到頂層 repo(不再有 `xxx/apps/web` 碎片,`a88f647`)
- 30 天預設視圖 + `token_project_usage` 永久明細表(34 天回填,`02c8bae`)
- 每日「錢做了什麼」分析 agent(haiku)+ Telegram 日報(`46cb94e`)
- /api/tokens 歷史合併 SQLite(>30 天可視,`74b2bc1` `7a5c331`)

### Fleet spine + skeleton
- 登錄表 `docs/spine-modules.md` 19 模組 + 兩 spine family(`31a7745` `5cd850d`)
- spine skills:auth(`31271a4`)rbac(`be0404c`)schema-sync + logs n=1 defer
  (`69c0ff8`)versioning=enforcement gate(`c11a16e`)ai-vision-extract(`49c4f99`)
- `product-skeleton` repo:脊椎接線 + 出生走查驗證(抓到 .env cwd bug)+ 8 tests
  + CI + GitHub(`8f70421`→`d2cd600`,repo `manibari/product-skeleton`)
- 抽取 roadmap demand-driven 化(`302ad72`)

### 穩定性 / QA
- tester 每日 build 兩度弄壞 live dashboard(7/5 失敗版 / 7/13 成功版同炸)→
  build 隔離 `NEXT_DIST_DIR=.next-tester` 根治(`9291515`)
- FlowView useSearchParams 缺 Suspense 修復(7/5 全站 500 的斷根;仍待獨立 commit,R1b)
- QA 手冊法走查 6 頁:磁碟明細 list(`c2e13b8`)、總覽 skeleton + 60s TTL cache
  4.98s→3ms(`6d154b3`);操作手冊 + 箭頭圖 `docs/manual/`(`5cb3174`)
- 背景 agents 釘 model(harvest/retro→sonnet,防跟 CLI 預設飄,`ad1b0b9`)

### 治理
- port SoT `docs/port-allocation.md`(3=前端 8=後端 5=資料庫 + NN;tukey/Verdandi
  遷 05 區塊,`2b20554`)
- 平台資料地基 ADR(Postgres-now,`910219e`)
- ops 中央監控器 repo(`manibari/ops`:config 驅動 3-check、狀態變更告警、多 host、
  keyed health)+ family-fiscal host-local `/api/health`(branch 待合)

## [0.1.0] - 2026-06-13

### Added

- Established the first explicit Rivendell baseline version.
- Added `docs/ROADMAP.md` as the canonical development roadmap.
- Added backend regression tests for the port map parser and drift semantics.
- Documented release hygiene: version changes belong in `VERSION`, notable
  human-authored changes belong in this changelog, and scheduled report output
  remains owned by agents.

### Changed

- Clarified current operational priorities: launchd agent loading, CI coverage,
  dashboard/API tests, audit report correctness, and generated artifact hygiene.
- CI now runs dashboard frontend checks, backend lint/tests, and skill structure
  validation on pull requests without relying on unavailable PR filename fields.
- `sk-setup-agents` now uses the explicit `launchctl bootstrap gui/$UID` domain,
  with legacy `load` fallback.
- launchd agent PATH now includes `/usr/sbin:/sbin` so dashboard API can run
  system tools such as `lsof`.
- `sk check agents` now reads the same GUI launchd domain used by setup.

### Fixed

- Port map behavior now distinguishes declared compose ports from live listeners
  and untracked local listeners.
- Dashboard production builds now use the documented webpack path by default.
- Cleaned existing dashboard lint blockers so CI lint can pass.
- Cleared objective skill frontmatter warnings for missing `tags`, `version`,
  and `gdrive-to-skills` `imported_at`.
- Restored launchd agent loading: all 16 agents in `agents.conf` now report as
  loaded.
---

# 歷史：ISO-week 版號時期（0.1.0 之前）

以下是 semver 之前的舊 changelog,採 ISO 週版號（一週一迭代,`workflow-retro`
收斂）。保留原始紀錄以供追溯,**不再更新**;檔案頂端的 semver 規則才是現行制度。

## [未結算] — 條目已併入 0.3.0

> 這一段在改用 semver 時沒有收尾,就地擱置了三個月。其中的助理層／knowledge-graph
> 都已上線,已於 2026-09-16 併進上方 0.3.0;此處原樣保留,不再是待辦。

### Added
- 助理 Avatar：`/avatar` 頁（VRM 對話視窗、人格切換、引擎與 API 金鑰設定）+
  `gateway/`（:8310，OpenAI 相容 /v1/chat/completions；引擎鏈 codex→claude→API key 直連；
  對話模型零工具，辦事只開 dispatch 提案）。雙人格：林迪（Lindir）+ 米瑞爾（Míriel，自選名），
  註冊表 `data/persona.conf`，dispatch/triage 推播署名跟隨 active 人格。
  ports.conf 補登記 mops:8200 與 iihi:8300 兩筆漂移。
- `sk dispatch` 個人助理行動層：模糊指令/信件事件 → 具體化提案（引知識庫）→
  分級確認（email/calendar 逐件 typed-yes、垃圾信批次、crm 放行、internal 自動）→
  確定性 actuator 執行（send-mail/gcal/mail-actions/tg-notify，模型永不執行寄送，
  payload hash 防竄改）。`bin/sk-mail-triage-cron` daily 7:45：重要信摘要推播、
  垃圾信 sk-junk 貼標 + 批次確認（永不 expunge、junk-guard 保護知識庫已知寄件人）、
  可行動事件自動開提案；業務行為路由 Rightek-CRM。
- knowledge-graph 啟用（翻案，原排隊退役）：`scripts/kg.py` 唯一寫入 API
  （id 指派/append-only/supersede/verify 全封裝）+ `bin/sk-facts-cron`
  （daily 21:30，`bin/sk-facts-digest` 摘要 session → headless 抽 durable facts，
  知識庫自身 git 為交易邊界）+ `~/.claude/CLAUDE.md` recall 區塊。
  首跑落地 8 筆 facts / 6 entities。janitor 白名單納入 `facts-*`。
- `doc-drift-sync` skill (`skills/meta/`) — detects/fixes drift across
  CHANGELOG / ROADMAP / CLAUDE.md / progress and defines the weekly iteration cycle.
- `ROADMAP.md` + `CHANGELOG.md` — version/roadmap discipline for rivendell itself,
  reviewed each iteration at `workflow-retro`.

## [2026-W24] — 2026-06-13

### Added
- chimesflow-design + app-ops-baseline gate skills (`ff8ea85`).

### Fixed
- sk-setup-agents PROJECTS_DIR landmine + ssot-drift cron 11-arg (`8007c6d`).
- `bin/sk` cmd_check_ssot derives project from PROJECT_REL_PATH not label (`389eacb`).

### Added (earlier in W24)
- dashboard Git 衛生 panel — uncommitted/unpushed across ~/code repos (`7523816`).
- learnings: iCloud-detach + agent gotchas, 3 entries (`2181b66`).

---

_Earlier history predates this changelog (待補 if reconstructed from git log)._
