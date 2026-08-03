# Rivendell Roadmap — Wave 制

> Living roadmap(平台 = skills 庫 + dashboard + agents + fleet 脊椎)。
> **制度取自 PTI-ARES**(`docs/plans/remediation-waves-2026-07.md` 模式):主題式
> Wave、每項獨立 commit + CHANGELOG + bump、貫穿硬 invariant 當驗收底線、
> known-gap register 不能只是文件。每週 retro(`workflow-retro`)對齊;Done 項
> 必須在 CHANGELOG 有對應條目(`doc-drift-sync`)。
> 依據:2026-07-18 紅藍隊評估(R1–R7,細節見當日 session / CHANGELOG 0.2.0)。

## 硬 invariant(貫穿所有 Wave 的驗收底線)

1. **Live 服務的 build 產物不可被任何背景程序觸碰**(`.next` 原子性;tester 已隔離,新排程一律比照)。
2. **宣稱完成 = 有驗證證據**(HTTP code / 截圖 / 測試綠;client 頁用 headless 截圖,不用 curl-grep)。
3. **機械收尾靠 gate 不靠記憶**(version bump、port 分配、README catalog)。
4. **抽象前先審計 ≥2 個成熟實作**(n=1 → deferred 進 known-gap register)。

## Wave 0 — 止血(先於一切;每項獨立 commit + CHANGELOG + bump)

- [ ] **R1a** 收斂 git split-brain:port-map 平行 session WIP 落地(**Peter**)→
      `chore/skill-quality` 合 main → WSL 改追 main。
- [ ] **R1b** FlowView Suspense 修復 byte-exact 單獨 commit(防 `checkout --` 滅失 → build 再炸)。
- [ ] **R3** family-fiscal prod 回灌 fail-loud SECRET_KEY(骨架 config 模式 backport)+
      prod 換真金鑰。**財務資料 + 公網 tunnel,最高優先。**
- [ ] **R5** chimesflow-db / spms 容器從 `~/code` context 重建(volume 保留)。

## Wave 1 — 可觀測(monitoring 0 → 1)

- [ ] **R2a** WSL 三件套(**Peter ~30min**:clone ops + OPS_KEY/HEALTH_KEY env + crontab;
      dashboard A2b systemd)。README 全備好。
- [ ] **R2b** agent 失敗告警:launchd agent exit≠0 → Telegram(復用 notify 管線)。
- [ ] **W22-2** doctor / harvest / material-health「exit-1 但有產出」dual-state 歸零。

## Wave 2 — 版本制度(本檔 + CHANGELOG 規則生效)

- [x] CHANGELOG 採 PTI-ARES 規則(PATCH/MINOR/MAJOR + 事無大小一條一行帶 hash)— 2026-07-18
- [x] `VERSION` 檔 + 0.2.0 catch-up cut — 2026-07-18
- [ ] rivendell 自身裝 version pre-push gate(骨架 `hooks/pre-push` 回灌)。
- [ ] dashboard footer 顯示 VERSION(過期 bump 可視化)。

## Wave 3 — Fleet 產化(demand-driven;mops / greenfield 拉動)

- [ ] 第一隻真產品從 `product-skeleton` 出生(ic-yms NN=07)→ 出生走查回饋骨架。
- [ ] 骨架前端半邊(Next.js + 同源 proxy,iihi 模式)— 等第一隻真需求再蓋。
- [ ] spine P2:`spine-deploy` / `spine-swagger` / `spine-settings` / `spine-api-keys`。
- [ ] scraper spine(#16–18):mops `packages/` 升格 skill,對第二隻爬蟲審計。

## Wave 4 — 入口(把已有的能力變成看得見、按得下去的東西)

> lever-first。8 個抓取型 workflow 已經在跑(tender-scraper · subsidy-scraper ·
> mops-financial-scraper · customer-intel · tw-company-lookup · keyword-discovery ·
> investment-research · media/*),輸出散在 `materials/` · `knowledge/` · `reports/`,
> 但**沒有任何地方寫著哪個 workflow 的輸出去哪裡**——要知道就得去讀 SKILL.md。
> 缺的不是能力,是入口(對映 CLAUDE.md「增量接線 > 重寫」)。
> 起點:2026-08-02 對話(SaaS workflow 卡片牆截圖)。

- [ ] **W4-1(lever)** workflow 契約層:SKILL.md frontmatter 增 `inputs` /
      `outputs` / `connectors` 三欄,先補那 8 個抓取型 skill。資料源是既有
      frontmatter,不另建 metadata 系統。
- [ ] **W4-2** dashboard 卡片牆:讀 W4-1,一張卡 = 一個 workflow,露出串接圖示、
      輸出落點、最後執行時間(registry label + `reports/` 已有)。
- [ ] **W4-3** 一鍵執行:卡片 → `sk run <skill>`,輸出串進既有 agent log view。
- [ ] **W4-4** 淘汰機制:改用**刪除測試**(取自 mattpocock `improve-codebase-architecture`)
      ——「把這個 skill 拿掉,事情會變糟嗎?」變糟=真的在隱藏複雜度;反而更清爽=空殼。
      比原本「N 個月 0 觸發就標記」好在它是語意判準、不用等 N 個月。現況是
      `knowledge-graph` 靠 retro 人工點名 3 次才退,不是機制。
- [ ] **W4-5** invocation 分流:**已量測 = 121 個 skill 的 description 合計
      58,731 字元 ≈ 16.8K tokens,每個 session 都載入**(對上 FR 2026-05-08 的估算)。
      Claude Code 原生支援 `disable-model-invocation: true`——description 完全不進
      context(官方文件已查證;gstack CHANGELOG 說「Claude 會 strip 掉」是過時資訊)。
      **但機械掃描抽不出候選:121 個裡純斜線指令 0 個**,每一個都寫了自然語言觸發語,
      連 `knowledge-graph`(`when_to_use: when encountering durable facts during
      conversation`)、`agent-headless`、`skill-scout`、`gdrive-to-skills` 都是。
      所以這是**逐個設計決策**,不是 sweep:每個 skill 要答「模型該不該自己叫它,
      還是我當索引」(context load vs cognitive load,見 `writing-great-skills`)。
      配套:轉成 user-invoked 的多到記不住時,用 **router skill** 解(同上)。
      先做前 20 肥的(video-transcript 1171 字元 / doc-drift-sync 1100 / spine-auth
      1081 / spine-versioning 1080 / ai-vision-extract 1031)。
      注意:rivendell 現有的 `user_invocable`(底線)是自家 README 產生器讀的欄位,
      跟 Claude Code 的 `user-invocable`(連字號、語意相反)不是同一個東西。

搭配 Skill pipeline 的 `bin/sk index`(INDEX-first 檢索)——那條解 token 成本,
這個 Wave 解人找不到,同一個病的兩面。

**不做**:可組合的 workflow builder(使用者自己拉抓取節點 → 存放節點)。那是另一個
產品不是 rivendell 的增量,地基要動;等「臨時想組一個新的」出現第 3 次再重審。

## Skill pipeline(每週 retro 管理;與 Wave 並行的常態產線)

- **Retire `knowledge-graph`** — 0 triggers,3+ retros 連續點名(W22 action 1)。
- **`doe-ml-analysis`** — DOE/製程 ML EDA(heatmap→PCA→regression R²);harvest Strong,
  補製造運營 domain gap。
- **`bin/sk index`** — INDEX-first 分層 skill 檢索,砍 per-session token(FR 2026-05-08)。
- Later:`presales-poc-scoping` mother-skill(n≥3 觀察中)· domain gaps(商業洞察/
  製造運營 AOI/SPC/排程/EHS/法務,真案落地才抽)· DFM 知識 reference skill(Vault SoT)。

## Known-Gap Register(登記不修——每項要有去處,不能爛在文件)

| Gap | 現況 | 解除條件 |
|---|---|---|
| `server.py` 2433 行單檔 | 會痛未痛 | 下次大改 dashboard API 時拆 routers/ |
| spine-logs n=1 | deferred ⏸ | mops 蓋 log viewer = 第 2 實作 → 重審 |
| ai-vision-extract n=1 | skill 已抽形狀未驗 | 第 2 個拍照→抽取產品出現 |
| sales-assistant 爬蟲遷移 | parked(Peter) | 決策後擴充既有 import 橋;連動 4 殭屍 agents + :5433 退役 |
| autoresearch 未釘 model | 跟 CLI 預設飄(現=Fable 5) | Peter 拍板 sonnet 或保留 |
| auto-stage hook 捲檔 | pathspec 紀律擋著(**已捲 3 次**;2026-08-02 把 pitch-deck 67 行既有 WIP 一起 commit 進 `1537d08`) | 評估 hook 限縮到本 session 檔 |
| 單機 SPOF(R4) | 接受中 | 規模 justify 第二台 always-on 時 |

## Done(pre-Wave 主線,2026-06→07;細目見 CHANGELOG 0.2.0)

Telegram ops-bridge → task-brief gate → skill 品質(`sk lint`+generator 修根)→
部署管理頁(B/A1/A2a/A2b+proxy)→ port SoT(3/8/5+NN)→ token 三層(30d 視圖/
DB 明細/每日內容分析)→ QA 手冊法(3 fixes)→ tester build 隔離 → spine 5 skills +
19 模組登錄表 → product-skeleton(出生走查驗證+tests+CI+GitHub)。
早期:chimesflow-design + app-ops-baseline(`ff8ea85`)· PROJECTS_DIR 地雷
(`8007c6d`)· Git 衛生 panel(`7523816`)。

---

_每週 retro 移動項目;Done 需真 commit/CHANGELOG 對應,不捏造。_
