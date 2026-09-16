# Progress Log — Agent Registry v2

## Session: 2026-07-27

### Planning
- [x] Requirement v2 定版並 commit（9d0fc52）：雙層模型（OODA × PDCA）、US-1~6、品質官為第一大臣
- [x] 盤點 sk-setup-agents 解析格式、agents.json 讀者、agents.conf 條目 → findings.md
- [x] task_plan.md 建立（5 phases + D1-D4 決策）
- [ ] Gate: /gstack-plan-eng-review（定案 D1 生成器語言、D2 agents.json 去留）

### Eng-review（2026-07-28，Opus 4.8）
- [x] 抓到 requirement 內部矛盾：US-5「逐條等價」vs「sales disable」不可並存 → 定案純機械搬移（D2-sales）
- [x] agents.conf 拓樸：user 定調兩層模型（知識管理層 registry → 排程管理層 launchd），中間 conf 降為不進 git 的暫存（D3-topology）
- [x] 自決工程細節：D4 共用解析模組（避免兩份 parser）、D5 sk-registry-gen 單元測試、D6 kind:ooda+enabled:true 無 executor 要 fail-fast、D2 agents.json 吸收欄位後淘汰
- [x] 新增 Phase 0（共用 registry.py），Phase 2/3/5 併入上述決策
- 學到：純工程接線細節不該拿去問 user（agents.conf 進不進 git 是我該自決的）→ 已修正互動節奏

### Phase 0-5（2026-07-30 全數落地）

這一行三個月來一直寫著「未開始」,但實作在計畫定版兩天後就進去了,只是沒人回來
改這份紀錄。2026-09-16 依 git 回填:

- [x] **Phase 0** 共用 parser + schema v2,第一個 OODA minister（`1cc1130`）
- [x] **Phase 1-2** `sk-registry-gen` CLI:generate / validate / check（`4829baa`）
- [x] **Phase 3** 20 條 agents.conf 條目全數遷入 registry,純機械搬移如 D2-sales
      定案（`d38af63`）
- [x] **Phase 4** `sk-setup-agents` 改由 registry 生成 conf（`bd10c54`）;
      `agents/agents.conf` 退為不進 git 的 build artifact,兌現 D3-topology
      兩層模型（`94b03bf`）;registry 驗證接進 health check（`b880123`）
- [x] **Phase 5** 文件收尾 —— registry 成為 live SoT（`80e07c0`）
- [x] Gate `/gstack-plan-eng-review` —— 已於 2026-07-28 完成（見上一節）

**收尾缺口（2026-09-16 補）**:`~/.claude/projects.json` 住在 repo 外、不隨 clone
走,兩層模型上線後沒有任何東西負責重建它,drift 從 09-10 起天天報 9 筆沒人清。
`sk-projects-sync` 補回並改讀 registry（`9898d95`）,drift 歸零。

---

## 現在的焦點（2026-09-16）

Agent Registry v2 這條線已結案。接下來依 [ROADMAP.md](ROADMAP.md) Wave 0 止血,
三項都還沒動:

- [ ] **R1b** FlowView Suspense 修復,byte-exact 單獨 commit
- [ ] **R3** family-fiscal prod 回灌 fail-loud SECRET_KEY + 換真金鑰
      —— 財務資料 + 公網 tunnel,最高優先
- [ ] **R5** chimesflow-db / spms 容器從 `~/code` context 重建（volume 保留）

本機已知待辦（非 Wave):`.codex/hooks.json` 未進版控但 AGENTS.md 已描述該設定;
`bin/sk:905` 還留著搬家前的 `PROJECTS_DIR="$HOME/Documents/Projects"` 死路徑。
