# Skill Loop Taxonomy Wave 1 (小區先行) Implementation Plan

> **For Claude:** Use `skills/planning/executing-plans/SKILL.md` to implement this plan task-by-task.

**Goal:** 把 `business/`、`media/`、`meta/` 三個混裝分類拆成「一分類 = 一條 PDCA 循環」，skill 名補上缺的主詞/受詞，並把 loop/pdca 寫進 frontmatter 讓 README 能產出循環 × PDCA 覆蓋表。

**Architecture:** 三層座標——目錄 = 循環（主詞）、frontmatter `loop:`+`pdca:` = 機器可讀 SoT、skill 名 = 平面命名空間裡的辨識（deploy 後 symlink 是平的，名字必須自帶主詞或受詞）。dev 循環（planning/qa/quality/workflow/backend/frontend/git/docs 主體）**本波不動**，先在小區驗證循環制。

**Tech Stack:** bash（bin/sk、git mv）、Python（scripts/generate-readme-catalog.py）。無外部依賴。

**決策紀錄（Peter 2026-08-30 拍板）:** 1 小區先行；2 受詞用縮寫表；3 循環名用英文。

---

## 規範 v2 摘要（Task 1 會寫進 `.claude/CLAUDE.md`）

**命名文法**：`<循環>-<受詞>-<動作>`，但**已能一眼辨識的不動**（避免 churn）：

1. 名字必須能回答「誰的循環」或「對什麼對象」至少一項；兩者皆缺 → 補循環前綴。
2. 受詞不明（如 channel 是誰的 channel）→ 補受詞，用縮寫表。
3. 既有前綴/後綴系列（qa-\*、slide-\*、\*-scraper、\*-writer…）優先於循環前綴，不重複疊加。
4. 跨循環共用工具**不掛循環前綴**（`tw-company-lookup`、`sow-writer`、`mermaid-diagram`），物理上放最大使用者的循環目錄，frontmatter 標 `loop: shared`。
5. 一支 skill 若橫跨兩條循環的兩個環位（合併錯位）→ 拆，用 plan 設計。

**循環（英文，本波啟用 6 條）**：`sales`（業務開發）、`gov`（政府案件：標案+補助）、`invest`（投資研究）、`hr`（人資）、`knowledge`（內容消化）、`platform`（rivendell 自我改善）。`dev` 循環下一波。

**縮寫表**：`yt`(YouTube)、`tw`(台灣)、`mops`(公開資訊觀測站)、`crm`、`jd`、`rfq`、`sow`、`gov`、`hr`。新縮寫需先加進此表再用。

**frontmatter 新欄位**（全部 124 支最終都要有；本波先填小區 ~40 支）：

```yaml
loop: sales        # sales|gov|invest|hr|knowledge|platform|dev|shared
pdca: plan         # plan|do|check|act（單值；填不出單值 = 拆分訊號）
```

---

## 對照總表（本波全部動作）

| 現位置 | 動作 | 新位置 | loop | pdca |
|---|---|---|---|---|
| business/customer-intel | 改名+搬 | sales/sales-customer-intel | sales | plan |
| business/keyword-discovery | 改名+搬 | sales/sales-keyword-discovery | sales | plan |
| business/sales-material | 搬 | sales/sales-material | sales | do |
| business/client-kickoff-docs | 改名+搬 | sales/sales-client-kickoff-docs | sales | do |
| business/presales-pipeline | 搬 | sales/presales-pipeline | sales | do |
| business/material-health | 改名+搬 | sales/sales-material-health | sales | check |
| business/crm-projection | 改名+搬 | sales/sales-crm-projection | sales | act |
| business/tw-company-lookup | 搬 | sales/tw-company-lookup | shared | plan |
| business/tender-scraper | 改名+搬 | gov/gov-tender-scraper | gov | plan |
| business/subsidy-scraper | 改名+搬 | gov/gov-subsidy-scraper | gov | plan |
| docs/rfq-writer | 改名+搬 | gov/gov-rfq-writer | gov | do |
| docs/subsidy-writer | 改名+搬 | gov/gov-subsidy-writer | gov | do |
| docs/sow-writer | 不動 | docs/sow-writer | shared | do |
| business/investment-research | 改名+搬 | invest/invest-research | invest | do |
| business/mops-financial-scraper | 搬 | invest/mops-financial-scraper | invest | plan |
| business/jd-writer | 改名+搬 | hr/hr-jd-writer | hr | do |
| business/candidate-analysis | 改名+搬 | hr/hr-candidate-analysis | hr | check |
| media/* (5 支 + _shared) | 分類改名 | knowledge/*（skill 名不動，除下行） | knowledge | do |
| media/channel-scraper | 改名 | knowledge/yt-channel-scraper | knowledge | plan |
| meta/knowledge-graph | 搬 | knowledge/knowledge-graph | knowledge | act |
| meta/（12 支自我改善） | 分類改名 | platform/（skill 名全部不動，series 優先） | platform | 見 Task 7 |
| meta/{ci-pipeline,deploy,dev-process-gate,init-project,plan-check-style,setup-permissions,task-brief} | 搬 | workflow/ | dev | 見 Task 7 |

改名後 `business/`、`media/`、`meta/` 三個目錄消失。分類數 12 → 15（-3 +6）。

**缺環（登記不補，YAGNI）**：gov 缺 C/A（標案命中率檢討）、invest 缺 C/A（建議回測）→ Task 9 進 ROADMAP Known-Gap Register。

---

### Task 0: 前置檢查

**Step 1: 確認乾淨工作區與現有計數**

```bash
cd /Users/manibari/code/rivendell
git status --short          # 應為空（reports 除外——不碰）
./bin/sk lint | tail -1     # 記下基準：124 skills, 0 errors
grep -c "| \`" README.md    # 記下目錄列數基準
```

**Step 2: 產出全量引用清單（每支要改名的 skill 一份）**

```bash
for s in customer-intel keyword-discovery client-kickoff-docs material-health \
         crm-projection tender-scraper subsidy-scraper rfq-writer subsidy-writer \
         investment-research jd-writer candidate-analysis channel-scraper; do
  echo "== $s =="; ./bin/sk rename "$s" "x-$s" 2>/dev/null | grep -v "^DRY" || true
done > /tmp/rename-refs.txt
wc -l /tmp/rename-refs.txt
```

（`sk rename` dry-run 會列出含 code 檔在內的所有引用，含它不會自動改的。之後每個 Task 逐支處理。）

**Step 3: 記下 repo 外引用基準**

```bash
grep -n "customer-intel\|rfq-writer\|subsidy-scraper\|tender-scraper\|channel-scraper\|jd-writer\|candidate-analysis\|investment-research\|material-health\|crm-projection\|keyword-discovery\|client-kickoff-docs\|subsidy-writer" \
  ~/.claude/CLAUDE.md ~/.claude/projects/-Users-manibari-code-rivendell/memory/*.md
```

Expected: 全域 CLAUDE.md 的 Slide/Text-Report/Recurring 路由表多處命中 + memory 檔 2-3 處。Task 8 逐一更新。

---

### Task 1: 規範 v2 寫進 SoT

**Files:**
- Modify: `.claude/CLAUDE.md`（「Skill naming series」一節）

**Step 1: 改寫該節**——保留既有前綴/後綴系列清單，其上新增「循環層（主詞）」小節：命名文法五條規則、6 條循環定義、縮寫表、frontmatter `loop:`/`pdca:` 欄位定義（內容即本 plan 開頭「規範 v2 摘要」，濃縮到 ~15 行）。註明 dev 循環下一波、plan family 仍不收斂。

**Step 2: Commit**

```bash
git add .claude/CLAUDE.md && git commit -m "docs(claude): skill naming v2 — loop(subject)-object-action grammar + PDCA frontmatter"
```

---

### Task 2: 產生器與 lint 先行（工具先於搬家，搬完立即可驗）

**Files:**
- Modify: `scripts/generate-readme-catalog.py:21-22`（CATEGORY_ORDER/NAMES）
- Modify: `bin/sk`（lint 區段，搜 `cmd_lint`）

**Step 1: CATEGORY_ORDER 加入新分類、暫留舊分類**（搬家期間兩組並存，README 才不會漏算——這是 2026-07-23 學費）：

```python
CATEGORY_ORDER = ["meta", "platform", "agents", "planning", "workflow", "qa", "quality",
                  "git", "frontend", "backend", "sales", "gov", "invest", "hr",
                  "business", "knowledge", "media", "docs"]
```

`CATEGORY_NAMES` 對應加：`platform: 平台自我改善`、`sales: 業務開發`、`gov: 政府案件`、`invest: 投資研究`、`hr: 人資`、`knowledge: 內容消化`。

**Step 2: 產生器加 Loop × PDCA 覆蓋表**——掃 frontmatter `loop:`/`pdca:`，在 README 目錄後輸出一張表（列=循環、欄=P/D/C/A、格=skill 數），缺環格顯示 `—`。無 loop 欄位的 skill 不進表（過渡期正常）。

**Step 3: `sk lint` 加規則**——`loop:` 值必須 ∈ {sales,gov,invest,hr,knowledge,platform,dev,shared}、`pdca:` ∈ {plan,do,check,act}；欄位存在才驗值（本波不強制存在，下一波轉 error）。

**Step 4: 驗證未搬家前行為不變**

```bash
./bin/sk readme   # 仍應輸出 124 skills；新分類 0 支不顯示
./bin/sk lint | tail -1   # 仍 0 errors
```

**Step 5: Commit**

```bash
git add scripts/generate-readme-catalog.py bin/sk && git commit -m "feat(catalog): loop/pdca frontmatter — categories, lint values, Loop×PDCA coverage table"
```

---

### Task 3: sales 循環（8 支，最大批，先做建立節奏）

**Files:** `skills/business/{8 支}` → `skills/sales/`

**Step 1: 建目錄並搬（改名的用一次 git mv 完成搬+改名）**

```bash
mkdir -p skills/sales
git mv skills/business/customer-intel      skills/sales/sales-customer-intel
git mv skills/business/keyword-discovery   skills/sales/sales-keyword-discovery
git mv skills/business/sales-material      skills/sales/sales-material
git mv skills/business/client-kickoff-docs skills/sales/sales-client-kickoff-docs
git mv skills/business/presales-pipeline   skills/sales/presales-pipeline
git mv skills/business/material-health     skills/sales/sales-material-health
git mv skills/business/crm-projection      skills/sales/sales-crm-projection
git mv skills/business/tw-company-lookup   skills/sales/tw-company-lookup
```

**Step 2: 每支 SKILL.md frontmatter**——`name:` 改成新名（kebab 與目錄一致，lint 會抓）、加 `loop:` + `pdca:`（值照對照總表）。改名的 5 支同時檢查 description 內互相引用（如 material-health 提到 sales-material）。

**Step 3: 修 in-repo 引用**——照 `/tmp/rename-refs.txt` 該 5 支的清單逐一改（含 `agents/registry/crm-projection.md`、`material-health.md` 的 entry/name、`.claude/CLAUDE.md` 專案層若有）。registry 檔案本身也要改名：

```bash
git mv agents/registry/crm-projection.md agents/registry/sales-crm-projection.md   # name: 欄同步改
git mv agents/registry/material-health.md agents/registry/sales-material-health.md
./bin/sk-registry-gen validate   # 0 FAIL 才續
```

**注意**：registry rename 會改 launchd label → 舊 label 服務要 bootout。執行時跑：
`./bin/sk-setup-agents`（重新載入）+ `launchctl list | grep -E "crm|material"` 確認無舊 label 殘留。

**Step 4: 驗證**

```bash
./bin/sk deploy | grep -E "relink|link|fail"    # 應見 5 個 relink/link，0 fail
for s in sales-customer-intel sales-keyword-discovery sales-material sales-client-kickoff-docs \
         presales-pipeline sales-material-health sales-crm-projection tw-company-lookup; do
  [ -e ~/.claude/skills/$s ] || echo "BROKEN: $s"; done                # 無輸出 = 通過
for s in customer-intel keyword-discovery client-kickoff-docs material-health crm-projection; do
  [ -L ~/.claude/skills/$s ] && echo "STALE OLD LINK: $s"; done        # 舊連結應已被 relink 清掉
./bin/sk readme && ./bin/sk lint | tail -1
grep -rn "business/customer-intel\|skills/business/crm" . --include="*.md" --include="*.py" --include="sk*" | grep -v docs/plans | grep -v archive   # 應 0 命中
```

**Step 5: Commit**

```bash
git add -A skills/sales agents/registry README.md
git diff --cached --name-only   # 確認無外掛檔（auto-stage hook 學費）
git commit -m "refactor(skills): sales loop — business/ 8 skills into sales/, subject prefix + loop/pdca frontmatter"
```

---

### Task 4: gov 循環(4 支，跨 business/ + docs/)

**Step 1-5 同 Task 3 節奏：**

```bash
mkdir -p skills/gov
git mv skills/business/tender-scraper  skills/gov/gov-tender-scraper
git mv skills/business/subsidy-scraper skills/gov/gov-subsidy-scraper
git mv skills/docs/rfq-writer          skills/gov/gov-rfq-writer
git mv skills/docs/subsidy-writer      skills/gov/gov-subsidy-writer
```

frontmatter（loop: gov；pdca 照表）→ registry 兩支改名（`subsidy-scraper.md`、`tender-scraper.md` → `gov-*`，label 換新 → setup-agents 重載）→ 引用修正（注意 `sow-writer` 的 SKILL.md 內文引用 rfq/subsidy-writer；`subsidy-scraper` 的 headless agent 排程）→ 驗證同 Task 3 → commit `refactor(skills): gov loop — tender/subsidy/rfq under one subject`。

---

### Task 5: invest + hr 循環（4 支，小批合併做）

```bash
mkdir -p skills/invest skills/hr
git mv skills/business/investment-research   skills/invest/invest-research
git mv skills/business/mops-financial-scraper skills/invest/mops-financial-scraper
git mv skills/business/jd-writer             skills/hr/hr-jd-writer
git mv skills/business/candidate-analysis    skills/hr/hr-candidate-analysis
rmdir skills/business   # 此時應已空；非空 = 對照表漏了，停下來查
```

frontmatter + 引用（investment-research 被 customer-intel/tw-company-lookup 的 SKIP 條款引用——Task 3 改過的檔案還會再命中一次，用 grep 全量掃不要靠記憶）+ 驗證 + commit `refactor(skills): invest + hr loops; business/ dissolved`。

---

### Task 6: knowledge 循環（media/ 改名 + channel-scraper 補受詞 + kg 歸位）

```bash
git mv skills/media skills/knowledge
git mv skills/knowledge/channel-scraper skills/knowledge/yt-channel-scraper
git mv skills/meta/knowledge-graph      skills/knowledge/knowledge-graph
```

**特別注意：**
- `skills/knowledge/_shared/` 的腳本用 `cd -P` 穿透 symlink 定位（2026-07-23 學費）——搬完跑一支實測：`ls -la ~/.claude/skills/video-transcript/` 並執行其 `scripts/` 下任一 `--help`。
- `channel-scraper` 的 media/README.md 與 `_shared` 內引用、`knowledge/videos/INDEX.md` 生成腳本 `save_note.sh` 是否 hardcode `skills/media` 路徑：`grep -rn "skills/media" . --include="*.sh" --include="*.md" --include="*.py" | grep -v docs/plans`。
- knowledge-graph 剛在 main 翻案啟用（`bin/sk-facts-cron` 引用它的 `scripts/kg.py`）——`grep -n "knowledge-graph\|kg.py" bin/sk-facts-cron` 逐一改路徑，改完 `bash -n bin/sk-facts-cron`。

frontmatter（5 支 loop: knowledge；channel→plan、其餘 do、kg→act）+ 驗證 + commit。

---

### Task 7: platform 循環（meta/ 改名 + 7 支 dev 工具遷出）

```bash
git mv skills/meta skills/platform
for s in ci-pipeline deploy dev-process-gate init-project plan-check-style setup-permissions task-brief; do
  git mv skills/platform/$s skills/workflow/$s
done
```

**skill 名全部不動**（series 優先規則：skill-\*、session-\* 系列已載主詞）。frontmatter：
- platform 12 支：`loop: platform`；pdca — task-brief 已遷出；session-harvest/audit-fix/doc-drift-sync=check、workflow-retro/learnings-promotion-sprint/self-improving-agent/skill-creator=act、skill-apply/skill-scout/sync-readme/session-wrap=do、writing-great-skills=do。
- 遷出 7 支：`loop: dev`、pdca 本波可留空（dev 循環下一波定案）。

引用特別注意：`task-brief` 是全域 CLAUDE.md Step 0 HARD GATE 的路由目標（名字沒變、只搬目錄 → symlink relink 後全域引用不受影響，但 repo 內 `skills/meta/task-brief` 路徑引用要掃）。`self-improving-agent` 與 `~/.claude/settings.json` hook 耦合（見 .claude/CLAUDE.md 遺留註記）——只搬目錄不改名，hook 引用的是 deploy 後的平面名，應無感；仍要 `grep -n "meta/self-improving" ~/.claude/settings.json` 確認。

驗證（全量）+ `./bin/sk readme`（此時 meta/business/media 從 CATEGORY_ORDER 移除，最終 15 類）+ commit。

---

### Task 8: repo 外引用同步（全域 CLAUDE.md + memory）

**Files:**
- Modify: `~/.claude/CLAUDE.md`（Text Report 路由表 A/C 段、Recurring Maintenance 表、Slide 流程的 /customer-intel）
- Modify: `~/.claude/projects/-Users-manibari-code-rivendell/memory/` 中提及舊名的檔（`sales-assistant-deprecated.md` 提到 crm-projection/customer-intel/material-health）

**Step 1**：照 Task 0 Step 3 的命中清單逐一改為新名（/customer-intel → /sales-customer-intel、/rfq-writer → /gov-rfq-writer …）。
**Step 2**：全域 CLAUDE.md 不在 repo 內，無法 commit——改完在本 plan 文末補記「已同步 YYYY-MM-DD」。

---

### Task 9: 缺環登記 + README 結構樹 + 收尾

**Step 1**：ROADMAP.md Known-Gap Register 加兩列：

```markdown
| gov 循環缺 C/A（標案/補助命中率無人檢討） | 登記 | 投標 ≥10 件後建 gov-bid-retro |
| invest 循環缺 C/A（研究建議無回測） | 登記 | invest-research 產出 ≥1 季後重審 |
```

**Step 2**：README「Structure」樹手動改（`sk readme` 不會動它——2026-08-17 學費）；分類計數同步。

**Step 3: 總驗證**

```bash
./bin/sk lint | tail -1                          # 124 skills, 0 errors
./bin/sk readme                                  # 124 skills in 15 categories
./bin/sk deploy | grep -c fail                   # 0
ls ~/.claude/skills/ | wc -l                     # 與改名前同數
grep -rn "skills/business\|skills/media\|skills/meta" . --include="*" 2>/dev/null | grep -vE "docs/plans|archive|\.git/"   # 0 命中
```

**Step 4**：Final commit + push；ROADMAP Wave 記錄本波完成。

**Step 5（執行後人工）**：Peter 順一遍常用路由（/sales-customer-intel、/gov-rfq-writer）確認肌肉記憶換檔；下一波（dev 循環 60+ 支）另開 plan，帶著本波踩到的雷。

---

## 風險與回退

- 每個 Task 獨立 commit，出錯 `git revert` 單顆；symlink 壞掉的訊號是「skill 在 Claude Code 消失且無錯誤」——每批的 BROKEN 檢查是硬 gate，不跑完不准 commit。
- registry label 更換會產生新 launchd 服務名：舊 label 用 `launchctl bootout` 清（絕不 `kill`），`sk agent list` 對帳。
- 其他機器 pull 之後要跑一次 `./bin/sk deploy` + `./bin/sk-setup-agents`（symlink 與 launchd label 都變了）——寫進 commit message 提醒。
