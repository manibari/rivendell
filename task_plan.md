# Task Plan: Agent Registry v2 實作

> Requirement SoT: `docs/requirements/agent-registry.md`（v2, commit 9d0fc52）
> 願景: 上朝系統 — OODA 大臣 × PDCA 艦隊（memory: agent-system-vision）
> 本期 = Lever 1（registry SoT）。executor（Lever 2）、inbox（Lever 3）不在本期。

## Goal

一個 agent 一個 markdown 檔（`agents/registry/<name>.md`）成為所有排程單位的 SoT：
schema v2 + template、registry→agents.conf 生成器、全量轉檔、驗證接健檢、
dashboard 讀 registry、品質官（第一個 OODA 大臣）registry 檔 + memory 模板。

## Phases

> eng-review 過關（2026-07-28）：D1/D2/D3-topology/D4-parser/D5-tests/D6-guard 全定案，見 Decisions。

### Phase 0: 共用解析模組（D4-parser）— DONE
- [x] `dashboard/lib/registry.py`：用 PyYAML 解析（已是依賴,不多花成本；D4「純 stdlib」就地修正為用 yaml，手解易在邊界出錯）
- [x] `RegistryAgent` dataclass（吸收 AgentsJsonConfig 欄位）+ validate() + to_conf_tuple/line + check_label_collisions + load_registry_dir
- [x] D6 guard（`OODA_EXECUTOR_AVAILABLE=False` gate）、filename==name、skill 白名單（known_skills 注入,built-in 豁免留給 CLI）
- [x] `dashboard/tests/test_registry.py`：12 tests 全綠（parse/validate/collision/ooda-guard/skill-whitelist）

### Phase 1: Schema + template + 品質官（US-1 檔案面 / US-6）— pending
- [ ] `agents/registry/` 目錄 + `TEMPLATE.md`（schema v2 全欄位註解版）
- [ ] `agents/registry/quality-minister.md`：kind=ooda, enabled=false, pdca_role=check,
      mission/mission_metric/observe/authority 全填真實值；用不到的欄位從 schema 刪
- [ ] `agents/state/quality-minister/journal.md` 空模板（醒來讀/睡前寫格式）
- [ ] Schema 若因此修訂 → 同步改 `docs/requirements/agent-registry.md`

### Phase 2: 生成器（US-2）— CLI DONE, rewire PENDING（live 管線,待 checkpoint）
- [x] `bin/sk-registry-gen`：generate / validate / check 三子命令,import lib.registry
- [x] generate 拒絕在 validation FAIL 時輸出；check 用 normalized 7-tuple 比對(非文字 diff)
- [x] fail-fast：檔名≠name、label 撞名、缺必填、D6 ooda guard 全在 registry.py + CLI
- [x] D5 單元測試 12 綠
- [ ] **⚠️ live 管線步驟（待 user greenlight）**：`sk-setup-agents` 開頭改呼 `sk-registry-gen generate > $TRANSIENT_CONF`、跑完刪；`.gitignore` 加 `agents/agents.conf`；`git rm --cached agents.conf`。此步會重跑 launchd bootstrap（含 dashboard keepalive 服務）

### Phase 3: 全量轉檔（US-5）— 檔案 DONE（等價已證）, conf 移除與 rewire 綁定
- [x] 21 檔（20 active + autoresearch enabled:false）+ 品質官 = 22 agent
- [x] **D2-sales：sales 4 隻保留 enabled:true** + body 退役註記
- [x] **等價驗證通過**：`sk-registry-gen check agents/agents.conf` → "no drift"（行為 diff=0）
- [ ] conf 從 git 移除 → 與 Phase 2 rewire 原子綁定（同上 ⚠️ 步驟）

### Phase 4: 驗證接健檢（US-3）— pending
- [ ] `sk-tester-cron` 加 registry 驗證 section（呼 `sk-registry-gen --validate`，FAIL/WARN 併入報告，零新 pip 依賴）
- [ ] `sk-ssot-drift-cron` 加 drift check（呼 `--check`）
- [ ] skills 白名單存在性檢查（沿用 built-in 豁免規則）

### Phase 5: Dashboard agent 卡 + 淘汰 agents.json（US-4 / D2-agentsjson）— pending
- [ ] `dashboard/lib/agents.py` 改 import Phase 0 的 registry.py，讀 registry 取代 `read_agents_json`
- [ ] `agents/[label]` 頁顯示 kind / schedule / skills / enabled；ooda 加 pdca_role + mission
- [ ] registry 無檔的歷史 agent → 標「未註冊」不噴錯
- [ ] 移除 `.claude/agents.json` 與 `read_agents_json`（欄位已吸收進 registry）

## Decisions

> 兩層模型（user 定調 2026-07-28）：**知識管理層**（registry = agent 身分/persona/skills/mission，唯一正本）
> → **排程管理層**（launchd）。中間 agents.conf 只是黏膠，使用者不該看到、不該為它做決定。

| # | 決策 | 狀態 |
|---|------|------|
| D1 | 生成器語言 = python（`bin/sk-registry-gen`），bash 管線不動。證據：sk-setup-agents 用 `IFS='\|' read` 吃 7 欄 pipe 格式（bin/sk-setup-agents:146） | 定案（eng-review） |
| D3-topology | **agents.conf 不進 git**，降為 build 暫存：`sk-setup-agents` 開頭現場呼 `sk-registry-gen` 產 conf、用完丟。registry 是唯一 committed 正本 → 無雙軌 SoT、drift 偵測自然成立（生成失敗即 drift）。`.gitignore` 加 agents.conf；requirement US-2/US-5 的「conf 標 GENERATED 並 commit」「逐條等價」AC 要改寫成「registry→conf 生成後與『當前 HEAD 的 conf』diff，驗證搬移無行為改變」 | 定案（user 2026-07-28） |
| D2-sales | 遷檔純機械：sales 4 隻保留 `enabled: true`（不打斷現跑 agent），退役分開 commit。移除 requirement US-5 AC-2 的 sales-disable，改註記「退役待 chimesflow ready」 | 定案（user 2026-07-28） |
| D2-agentsjson | `.claude/agents.json` 吸收進 registry schema（新增 merge_strategy / allowed_paths / forbidden_paths / max_files_changed / qa_pre_commit 欄位，歸 claude/ooda kind）後淘汰。唯一讀者 dashboard/lib/agents.py:144 於 Phase 5 改讀 registry | 定案（工程細節，我自決） |
| D4-parser | **單一 registry 解析模組**（`dashboard/lib/registry.py`，純 stdlib 不加 PyYAML）：被 (a) bin/sk-registry-gen CLI (b) dashboard/lib/agents.py 共用 import。避免兩份 frontmatter 解析器漂移。tester-cron 走 CLI 的 `--validate` 子命令，零新 pip 依賴 | 定案（DRY，我自決） |
| D5-tests | sk-registry-gen 要有單元測試（放既有 `dashboard/tests/`）：parse 合法、parse 非法→正確 FAIL、generate→golden conf、round-trip 等價。migration 等價檢查是一次性,不算 regression guard | 定案（測試非談判項，我自決） |
| D6-ooda-guard | 生成器遇 `kind:ooda` + `enabled:true` 但 executor 未到位（Lever 2 前）→ 明確報錯「no executor」,不產半套空 entry 的壞 plist。品質官本期 enabled:false 不觸發 | 定案（fail-fast，我自決） |
| D3-court | 奏摺格式本期不定案（Lever 3）；品質官 registry 只在 authority.escalate 寫行動類型 | 維持 |
| D4-oldfiles | 舊 task_plan/findings/progress（2026-04 workflow-map）已覆寫，舊內容留 git history | 已執行 |

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| （無） | | |

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | clean | 5 issues, all folded into plan (0 critical gaps) |

Findings folded: (1) requirement 內部矛盾 US-5 逐條等價 vs sales-disable → D2-sales；(2) agents.conf 雙軌 SoT 風險 → D3-topology 降暫存；(3) 兩份 frontmatter parser 風險 → D4-parser 共用模組；(4) sk-registry-gen 無測試 → D5；(5) kind:ooda+enabled:true 無 executor 會產壞 plist → D6-guard。

- **CODEX:** 略過（內部 infra plan，codex 對 ~/.claude skill 目錄無讀取價值）。
- **VERDICT:** ENG CLEARED — 計畫已定版，可進實作（Phase 0 起）。

NO UNRESOLVED DECISIONS
