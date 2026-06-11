# Learnings

> **2026-05-13 — promotion sprint**: Many entries below have been distilled into:
> - `~/.claude/CLAUDE.md` (Engineering Gotchas section) — cross-project generic rules
> - `rivendell/.claude/CLAUDE.md` (Rivendell Operations section) — platform-meta rules
>
> Originals are kept here for history. New **generic** learnings should go to
> `~/.claude/learnings/LEARNINGS.md` (cross-project staging). New **rivendell-meta**
> learnings stay here or get promoted directly to `rivendell/.claude/CLAUDE.md` if
> they're a rule. See `reports/learnings-promotion-sprint-2026-05-13.md`.

## 2026-06-08 — Dashboard「Port 對應」頁資料源錯：讀 docker-compose.yml，但 rivendell 是 launchd 原生跑

- **Category**: best_practice（"信 ground truth 不信 derived/cached state" 的又一例，見 global CLAUDE.md Engineering Gotchas）
- **Seen in**: Peter 問「port 對應的部分應該是錯的」。`/api/ports`（`dashboard-next/api/server.py:1871`）只 parse `docker-compose.yml` 當 SoT，前端頁腳也寫「資料源：docker-compose.yml」。
- **真相**: rivendell 服務全是 launchd 原生 process，**根本沒走 docker**（與 `.claude/CLAUDE.md`「dashboard-next is launchd-managed」一致）。實測：
  - compose 宣告 8000/3000 → 實際是 native `python3.1`(8000)/`node`(3000)，非容器
  - compose 宣告 8001/3001/8501/8002/3002/3004 → **全沒在跑**
  - 實際在聽的 3100/8011/8100 → **compose 沒宣告**
  - 機器上唯二真容器 5433(spms-postgres)/5434(chimesflow-db) → **是別專案的**，不在 rivendell compose
- **Rule**: 任何「服務狀態/port 對應」頁要以**實際 listening sockets**（`lsof -nP -iTCP -sTCP:LISTEN` 或 `psutil`）為 SoT，docker-compose 宣告只能當「期望值」疊上去標 drift。死設定檔不等於執行現況。
- **Fix 方向（未實作）**: 改 `/api/ports` 掃實際 listener + 疊 compose 宣告，狀態分 `live符合宣告` / `live野生(未宣告)` / `drift(宣告沒跑)`。

## 2026-05-26 — 搬動 symlink 部署的技能 repo 後，跑它自己的 relink，別手改 symlink（gstack = `bin/gstack-relink`）

- **Category**: knowledge_gap（iCloud detach 殘留第三例，見 [[同源 sk undeploy orphan-symlink 條]]）
- **Seen in**: rivendell dashboard「Skill 總覽」少了 gstack —— Peter 問「gstack 為什麼不在 skills 總覽」
- **Context**: dashboard `dashboard/lib/skills.py:list_skills` 掃 `~/.claude/skills/`，每個 entry 要 `SKILL.md.is_file()` 為真才算。gstack 五月初部署時（SKILL_PREFIX=true）建了 47 個 `~/.claude/skills/gstack-<name>/SKILL.md` symlink 指向當時的 `~/Documents/Projects/gstack/<name>/SKILL.md`。iCloud detach 把 gstack 搬到 `~/code/gstack` 後，umbrella `~/.claude/skills/gstack` symlink 有更新、但這 47 個 per-skill symlink **全部 dangling**（指舊路徑）→ `is_file()` False → list_skills 靜默全跳過，總覽只剩 umbrella `gstack` 1 個。`/api/issues` 的 dangling 檢查也抓不到（它只看頂層 entry 是不是斷 symlink，這裡頂層是真目錄、斷的是裡面那層 SKILL.md）。
- **Rule**:
  1. **搬動以 symlink 部署技能/工具的 repo 後，跑該 repo 自己的 relink/deploy，不要手改 symlink**。gstack 是 `~/code/gstack/bin/gstack-relink` —— 冪等、會自動偵測 `~/.claude/skills/gstack`、讀 `gstack-config get skill_prefix` 重建前綴 symlink、**不需 bun、不重建二進位**（比 `./setup` 輕）。
  2. `./setup` 有 dirname 陷阱：`INSTALL_SKILLS_DIR=dirname(gstack dir)`，直接跑 `~/code/gstack/setup` 會算成 `~/code`（錯）；要透過 symlink 路徑 `~/.claude/skills/gstack/setup` 跑。`gstack-relink` 沒這問題（明確偵測 `~/.claude/skills/gstack`）。
  3. relink 的 skip 清單**故意排除 `browse`**（跟 browser 二進位綁一起，由 `./setup` 另外處理）→ `gstack-browse` 要完整 `./setup`（需 bun）才會通。
  4. relink 不清理「來源已移除」的舊技能殘留目錄（如 `gstack-checkpoint`），那種 dangling 要手動 `rm`。
- **Promote when**: 此規則 gstack 專屬，留 history 即可；若再有第二個 symlink-deployed repo 搬家踩到，promote 一行通則到 `~/.claude/CLAUDE.md`（已有 iCloud detach 段落可掛）。

---

## 2026-05-23 — `sk-setup-agents` PROJECTS_DIR 寫死舊 iCloud 路徑；重跑會把全部 plist 倒回壞路徑

- **Category**: knowledge_gap
- **Seen in**: rivendell — 加 `disk-monitor` agent、要載入 plist 時才發現
- **Context**: `bin/sk-setup-agents:22` 仍是 `PROJECTS_DIR="$HOME/Documents/Projects"`（iCloud detach 前路徑）。iCloud detach 已把 17 個 repo 搬到 `~/code`、各 agent 的 plist 也（手動/遷移）更新成 `~/code`，但 setup-agents **本體沒改**。重跑 `./bin/sk-setup-agents` 會用 `$PROJECTS_DIR/$project_rel` 重新生成**所有** plist → 全指向不存在的 `~/Documents/Projects/...` → 整個 agent fleet 壞掉。這也是 `ssot-drift` plist 自 2026-05-20 加入後一直沒被載入的根因（跑 setup-agents 會炸，所以沒人跑）。
- **Rule**:
  1. 修好前，**新增 agent 一律手動建 plist + `launchctl bootstrap gui/$(id -u) <plist>`**（mirror 既有已載入的，如 `com.sk.agent.rivendell.doctor.plist`，路徑用 `~/code`）。disk-monitor 已這樣處理。
  2. 正解：`PROJECTS_DIR` 改 derive — e.g. `PROJECTS_DIR="${SK_PROJECTS_DIR:-$(cd "$(dirname "$REPO_DIR")" && pwd)}"`（repo 的上層目錄），符合 `~/.claude/CLAUDE.md`「never hardcode the repo/project name / path」。
  3. 修完後重跑一次正式納管 `ssot-drift` + `disk-monitor`，並 verify `grep -L /code ~/Library/LaunchAgents/com.sk.*.plist` 為空。
- **Promote when**: 修好 derive 後 → 把「never hardcode PROJECTS_DIR；未修前新 agent 走 manual bootstrap」併進 `rivendell/.claude/CLAUDE.md` Rivendell Operations。相關：[[同日 sk undeploy orphan-symlink 條]]（同屬 iCloud detach 搬遷殘留）。

---

## 2026-05-23 — `_sk_exec_record_run` 是 11-arg；cron 用 3-arg 會死在 `$4: unbound variable`

- **Category**: knowledge_gap
- **Seen in**: rivendell — 寫 `sk-disk-monitor-cron` 照抄 `sk-ssot-drift-cron` 時踩到
- **Context**: `bin/sk-exec-lib` 的 `_sk_exec_record_run` 真實簽名是
  `project agent start_epoch end_epoch exit_code log_path [commit files qa branch pr]`（11 參數，正確用法見 `bin/sk-harvest-cron:114`）。但 `bin/sk-ssot-drift-cron` 用了自創的 3-arg 形式 `_sk_exec_record_run "ssot-drift" "clean" ""` → 在 `set -u` 下函式內引用未傳的 `$4` 直接 fatal，且 `|| true` 救不回（unbound var 在 set -u 下終止 shell）。所以只要 `_sk_exec_record_run` 有被 source 進來，ssot-drift cron 就會在記錄 run 那行死掉、寫不出 drift 報告。
- **Rule**: 新 cron 要記 run，**照抄 `sk-harvest-cron:114` 的 11-arg 形式**，別自創簽名：
  `_sk_exec_record_run "$PROJECT_NAME" "<agent>" "$start_epoch" "$end_epoch" "$run_exit" "" "" "" "" "" ""`。`sk-disk-monitor-cron` 已用對；`sk-ssot-drift-cron` 仍壞，待修。
- **Promote when**: 修掉 ssot-drift cron 後屬一次性 bug，不需 promote；但「cron 記 run 用 11-arg」可考慮寫進 agent-observability skill。

---

## 2026-05-23 — `bin/sk undeploy` 只認 current `$REPO_DIR` 為主的 symlink；舊路徑 symlink 是 orphan

- **Category**: knowledge_gap
- **Seen in**: 2026-05-22 iCloud detach migration — 搬完 rivendell 到 `~/code/rivendell` 後，`~/.claude/skills/*` 還是 94 個 dangling symlinks 指向 `~/Documents/Projects/rivendell/skills/...`
- **Context**: `cmd_undeploy` 的核心邏輯（`bin/sk` 接近行 113）：
  ```bash
  if [[ "$link_dest" == "$REPO_DIR"/* ]]; then rm "$target"; fi
  ```
  只 unlink「target 指向 *當前 REPO_DIR*」的 symlink。Rivendell 搬到新路徑後，`$REPO_DIR` 變成 `~/code/rivendell`，但所有 dangling symlinks 還指 `~/Documents/Projects/rivendell` — 不匹配 → 視為「不是我管的」→ 不刪。`sk deploy` 接著跑時看到「target 已存在（symlink）」就 skip → **94 個 dangling 永遠清不掉**。
- **Rule**:
  1. **rivendell repo 整體搬路徑時必加一個 manual cleanup 步驟**：
     ```bash
     for l in ~/.claude/skills/*; do
       [ -L "$l" ] && [ ! -e "$l" ] && rm "$l"
     done
     ./bin/sk deploy
     ```
  2. 或者在 `cmd_undeploy` 加個 `--orphans` flag：清掉任何 dangling symlink，不檢查 target 是否屬於 current REPO_DIR
  3. 注意：deploy hook 預設的「skip if already linked」會把 dangling 也當成「linked」— `if [ -L "$target" ]` 對 dangling symlink 仍 returns true
- **Promote when**: 若加 `sk undeploy --orphans` flag → 直接 promote 為 rivendell `.claude/CLAUDE.md` 內 Rivendell Operations section 的 rule（取代手動 for-loop）。

---

## 2026-05-13 — dashboard-next is launchd-managed; rebuild requires bootout/bootstrap, not `kill` + manual `next start`

- **Category**: correction (followed by user "現在還是沒跑出來" + "畫面的 css 壞了")
- **Context**: User reported overview page stuck on "載入中..." with broken CSS. First-pass fix: killed the stale `next-server` (PID 3194, running since prior Saturday), `mv .next .next.broken-* && npm run build && npx next start -p 3000`. Looked healthy via curl + headless probe (data rendered) so I called it done. But the user kept seeing 載入中 + unstyled. Investigation showed `/_next/static/chunks/*.css` 404 even though file was on disk, and stderr was full of `Cannot find module '../chunks/ssr/[turbopack]_runtime.js'` — Next 16 Turbopack runtime path issue.
- **Real root cause**: dashboard-next is managed by **launchd** (`~/Library/LaunchAgents/com.sk.dashboard.web.plist`, label `com.sk.dashboard.web`, `KeepAlive=true`). When I `kill`ed the next-server, launchd respawned it (via `start-web.sh`). My `npx next start` race-collided with launchd's respawn → live next-server process loaded a half-rebuilt `.next/` (Turbopack runtime path went stale), then served partial 500s/404s. Sister service: `com.sk.dashboard.api` (currently unloaded; I started API manually instead).
- **Correct fix sequence**:
  1. `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.sk.dashboard.web.plist` (stops respawn)
  2. Verify port 3000 freed: `lsof -iTCP:3000 -sTCP:LISTEN`
  3. `mv .next .next.broken-$(date +%s) && npm run build && touch .next/.build-complete`
  4. `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.sk.dashboard.web.plist`
- **Rule**: Before touching `dashboard-next/.next/` or restarting frontend, **always check `launchctl list | grep dashboard` first**. If service is loaded, drive it through `launchctl bootout`/`bootstrap`, never `kill`. Same logic for `com.sk.dashboard.api` and `com.sk.dashboard.watchdog`. start-web.sh is a launchd payload, not for direct invocation when launchd owns the service.
- **Debug trick that nailed it**: `tail /Users/manibari/Library/Logs/sk-agent/com.sk.dashboard.web-stderr.log` revealed the Turbopack MODULE_NOT_FOUND that curl/probe didn't show. Always check launchd-managed service stderr logs when behavior is inconsistent with on-disk state.

## 2026-05-07 — Long-running `next-server` (production) on port 3000 won't pick up source edits; QA new code on a different dev port

- **Category**: knowledge_gap (gotcha discovered while QAing dashboard-next)
- **Context**: After landing Stage 1 (fonts + tokens + Logo + Sidebar refactor + workflow page rebuild), tried `pnpm dev` to QA the new code. Port 3000 was occupied by `next-server (v16.1.6)` PID 4668 running since 9:48AM — turned out to be a long-running `next start` (production server) the user had launched earlier in the day. Curl on port 3000 returned the OLD prerendered output (`x-nextjs-prerender: 1`, `x-nextjs-cache: HIT`) — Sidebar still had `bg-zinc-50 dark:bg-zinc-950`, project switcher still had `🌐 全部專案`, description was the old "Skills library agent dashboard". Production servers serve baked artifacts; they do not hot-reload source edits.
- **Other ports were also taken**: 3001 had a "News Stock" project's node process. Free port found at 3020.
- **Rule**: For QA after source changes on a project that may already have a long-running server somewhere, **never assume port 3000 is the right place to look**. Always:
  1. `lsof -i :3000` and inspect the COMMAND — `next-server` (no `dev`) means production, will serve stale.
  2. Find a free port: `for p in 3010 3020 3030; do ! lsof -i :$p >/dev/null 2>&1 && echo "FREE: $p" && break; done`
  3. Start `pnpm next dev -p <free-port>` and curl that port.
  4. **Do NOT auto-kill** the long-running production server — it's the user's daily dashboard, killing disrupts their tooling. Verify on a side port and tell them to rebuild + restart at their convenience.
- **Diagnostic markers when curl returns stale**:
  - `x-nextjs-prerender: 1` header — production prerender, not dev
  - `x-nextjs-cache: HIT` — cache layer
  - `_next/static/chunks/c04b94ce13225456.css` style-of hash that doesn't match new build's `src_app_f288d514._.css` — different artifact set
- **Generalization**: Same trap exists for any framework with build-mode vs dev-mode (Next.js, Vite, Remix, Astro). If a port responds with HTTP 200 but shows old code, check whether that's actually `dev` or a long-running `start`/`preview`/`build` server.

## 2026-05-07 — /gstack-autoplan ROI threshold: when reviewer has full plan context already, 4-phase dual-voice review mostly reproduces what's already known

- **Category**: best_practice
- **Context**: After running requirement → design-consultation (4 iterations) → mockup → planning-with-files for the dashboard-next redesign, recommended `/gstack-autoplan` for plan review. The user picked it. Before launching, did a reality check: 491-line plan across 4 docs, full design context still in head from earlier in same session, 3 real architecture decisions, plan is reversible (not shipping to customers). Estimated cost: 30-45 min wall clock for 4 phases × dual voices (codex + Claude subagent) × full sections; large context burn. Pushed back honestly with 4 options. User picked "Tight single-pass eng review" instead.
- **Outcome**: Tight review (~5 min) caught 9 concrete fixes including: Tailwind v4 already configured (obsoletes the Strategy A/B in findings.md), `next/font/google` already wired (so use `next/font/local` for self-host, not raw @font-face), Sidebar component already exists (refactor not build), workflow API already returns typed data (don't freeze to JSON SSOT in Stage 1), React Flow's value is drag/edit not readonly view (defer to parking lot). Net Stage 1 scope ~25-30% smaller. Surfaced 2 real taste decisions, auto-decided 7 mechanical fixes, all logged in plan review report.
- **Diagnostic for "is autoplan worth it?"**: Three signals push toward TIGHT review instead of full autoplan:
  1. **Reviewer holds the full plan context already** — same session as planning, no compaction yet
  2. **Plan size + risk profile is bounded** — < 1000 lines, single component, reversible decisions, no customer-facing surface
  3. **Real architecture decisions are countable on one hand** — when there are 1-3 clear "fork in the road" choices, surface them directly; don't ask 4 reviewers to find them
- **When autoplan IS worth it**: large plans (>2000 lines plan), multi-component blast radius, customer-facing surface, fresh-context reviewers (cross-session resume, code you didn't write), security/compliance involved, plan that already had 1+ revision cycles and needs adversarial scrutiny.
- **Generalization**: Same pattern applies to other "full vs tight" review skills (e.g. /gstack-cso vs /gstack-review). The cost/benefit isn't just plan complexity — it's the **delta between what the reviewer knows and what the review would produce**. When delta is small, tight review wins. When delta is large (fresh reviewer, gnarly code), full review wins.
- **Anti-pattern (avoided this time)**: blindly recommending the heaviest review skill because "more rigor = better". Flag when /gstack-autoplan would mostly reproduce in-context knowledge. Pre-compute the user's likely cost before recommending the skill, not after.

## 2026-05-07 — Logo-first beats full aesthetic redesign for personal dev tools; user reframe rescued 4 iterations of mythic-library overengineering

- **Category**: best_practice (user-converged after burning 4 visual iterations)
- **Context**: User asked to redesign rivendell dashboard ("醜且亂", workflow map needs tree). Ran `/gstack-design-consultation`. Iterated v1 dark industrial → v2 light + charts → v3 Mythic Library (Tolkien parchment + Cormorant Garamond + scroll cards + Bezier connectors) → v3.1 Mythic with toned-down typography. Each iteration the user gave more specific feedback. At v3.1 the user asked: "Rivendell 是不是換個 logo 就好？" — which reframed the entire problem.
- **Reframe**: rivendell character does not need to be carried by every surface of the dashboard. Logo + a single accent color (forest green) + one footer ornament gets you 90% of the brand identity for 10% of the cost. Vercel, Linear, Raycast all do this — their dashboards are neutral; their identity lives in the logo + brand color.
- **Why I missed it earlier**: I treated the design problem as "what aesthetic should the dashboard adopt" instead of "where should brand identity live, and how cheaply can we put it there". The skill itself biases toward full-stack proposals (aesthetic + decoration + layout + motion), so without explicit pushback toward minimalism, you escalate decoration. ROI question was never asked until the user asked it.
- **Rule**: Before iterating on an aesthetic proposal beyond v2, surface the question: "is the dashboard chrome the right place for brand identity, or should the logo carry it?" — especially for **internal / personal / dev tools** where chrome is supposed to disappear into the work.
- **Diagnostic**: If you find yourself proposing parchment textures, custom serif typography, hand-drawn connectors, or any "decorative layer" on a dashboard for a single user with no marketing surface, stop and ask the lever question. The lever is almost always the logo + 1 accent color, not the entire surface.
- **Generalization**: Same trap exists for B2B SaaS dashboards (where brand consistency matters but admins care about function), DX surfaces like CI dashboards, and internal admin tools. Marketing sites and consumer products are the opposite — chrome IS the brand. Calibrate by user-type.
- **Final outcome**: v4 = light neutral dashboard + twin-leaves logo in forest green + Geist + Geist Mono + ❦ footer ornament + one Tolkien-flavored line. Design system written to `dashboard-next/DESIGN.md`, logo SVGs to `public/logo.svg` and `public/logo-mono.svg`, scoped CLAUDE.md to `dashboard-next/CLAUDE.md`.

## 2026-05-07 — Storyline-first hard gate is intentionally NOT enforced via hook; slide-workflow Gate 0 + flow doc is the right level

- **Category**: best_practice (deliberate "stop here" decision — recording so it doesn't get relitigated)
- **Context**: After adding the Slide / Deck Building flow to ~/.claude/CLAUDE.md (A) and making slide-workflow the orchestrator (B), considered a third step C: enforce storyline.md `status: signed-off` as a hard gate via PreToolUse hook on Skill calls to pitch-deck / sales-material / iot-factory-report / generation tools. Decided NOT to do it.
- **Decision**: Stop at B. The cd63836f / 光泉 deck failure mode (5 wasted edit cycles because storyline was figured out during slide work) was a **D-path** deck — exactly slide-workflow's territory — and slide-workflow Gate 0 already catches that case with an override-with-warning soft gate. Hard hook is over-engineering.
- **Why A/B/C deck types don't need the gate**:
  - `pitch-deck` has its own discovery interview built in — storyline is an internal artifact, not a precondition
  - `sales-material` assembles from a materials library; storyline is implicit in the customer-intel report
  - `iot-factory-report` is data-driven (time-series → charts); there is no storyline concept
  - Adding a storyline gate to these would solve a problem that doesn't exist and would block legitimate fast-path uses
- **Why hook-based enforcement is wrong here**:
  - PreToolUse hook would have to decide: is CWD a deck context? does this storyline.md belong to THIS deck or a sibling project? what about monorepos? — high false-positive risk
  - Debugging hooks is painful; misfires create silent friction
  - The cost is paid every Skill call, the benefit only fires for the rare D-path deck without storyline — bad cost/benefit ratio
  - Memory note `deck_building_workflow` says storyline is a leverage point; "leverage point" is a discipline rule, not an OS-level lock
- **Re-evaluation trigger**: If the wasted-edit-cycle failure mode recurs ≥2 times in next 1-2 weeks, look at WHICH entry-point bypassed Gate 0 and patch THAT specific path — don't add a global hook.
- **Generalization**: When evaluating "should this be a hard gate?", check (a) does the failure mode actually appear at multiple entry-points, or just one? (b) do the other entry-points have their own equivalent preflight? (c) what's the false-positive cost of the hard gate? If the failure is concentrated at one entry-point AND the others have their own preflight AND the hard gate has high false-positive cost, the answer is "leave it as a soft gate at the one entry-point". This is the same logic that makes us prefer ESLint warnings over compile errors for stylistic rules — enforcement strength should match how often the rule is actually right.

## 2026-05-07 — Skill audit ≠ skill orchestration audit: a "should we add a skill?" question is often a "is the workflow written down?" question in disguise

- **Category**: correction
- **Context**: User asked「目前的 skills 是不是有值得建立的，尤其是在簡報端？」. I read harvest-2026-05-06-followup.md + skill-audit-2026-05-06.md, found the slide ecosystem has 11 overlapping skills (slide-workflow, slide-office-hours, pitch-deck, sales-material, slide-template-extractor, office-pptx, gdoc-report-builder, iot-factory-report, customer-intel, metadata-workshop, de-slopify) and concluded "no new slide skill needed, audit just shows description-sync issues". User pushed back:「重點應該是要怎麼在建立簡報的 flow 中把不同的 skills 組合再一起吧 / 所以其實是 skills workflow 簡報建置的設計問題」.
- **Mistake**: I treated the question as a coverage/gap question (what's missing?) when the actual problem was orchestration (how do these compose?). The skill ecosystem was already mature — the missing artifact was the **flow document**, equivalent to the existing `### UI Feature / New Page` section in ~/.claude/CLAUDE.md but for decks.
- **Diagnostic**: When the user asks "do we need a new skill for X?" and the audit shows ≥3 overlapping skills already in that domain, the answer is almost never "add another skill". The right next question to surface is: **is there a written flow that says when each one fires?** Check ~/.claude/CLAUDE.md for a `### X Flow` section. If absent, that's the actionable gap, not a new skill.
- **Rule**: Before recommending skill creation, check whether ~/.claude/CLAUDE.md has a flow section covering the work-type. A documented flow (gating questions, skill chain, hard gates like signed-off storyline) is higher leverage than another single-purpose skill, because it forces routing to be explicit and reduces "工人智慧 selecting the right skill mid-task".
- **Generalization**: Same trap will appear for any domain with many small skills (presales pipeline, customer research, deployment, QA). The signal is description-overlap warnings in skill-audit (`[docs,workflow]: ... — 建議檢查邊界是否清楚`) — those overlaps are evidence of an undocumented flow, not necessarily of skill bloat. Fix the flow doc first; only consolidate skills if the flow doc itself can't disambiguate them.
- **This-session fix**: Added `### Slide / Deck Building` section to ~/.claude/CLAUDE.md mirroring the structure of `### UI Feature / New Page` — deck-type routing question first (A/B/C run their own skill's internal flow, D follows generic 8-step pipeline), with `slide-office-hours` as a hard gate (storyline.md needs `status: signed-off` before generation). Did NOT create any new skill.

## 2026-05-05 — Some Claude Code skills are built into the binary, not file-based — invisible to rivendell skill audits

- **Category**: knowledge_gap
- **Context**: User asked which skill helps reduce permission prompts. `fewer-permission-prompts` is in the available-skills list but `find skills/ -name fewer-permission-prompts` returns nothing in rivendell, `~/.claude/skills/`, or `~/.claude/plugins/`. User asked「為什麼 rivendell 查不到」.
- **Root cause**: Claude Code ships ~9 skills compiled directly into the `claude` binary as JS. Confirmed via `strings $(which claude) | grep fewer-permission` — the skill registration call (`T$({name:"fewer-permission-prompts", description:"...", userInvocable:true, ...})`) is in the bundled JavaScript, not on disk anywhere.
- **Full inventory of built-in skills (Claude Code circa 2026-05)** — 15+ items split across THREE registration mechanisms:
  - **Category A — `T$({name:...})` skill registrations** (11): `batch`, `claude-api`, `claude-in-chrome`, `debug`, `dream`, `fewer-permission-prompts`, `keybindings-help`, `loop`, `schedule`, `simplify`, `update-config`
  - **Category B — `{type:"prompt", source:"builtin"}` slash commands** (5): `/commit`, `/init`, `/init-verifiers`, `/insights`, `/review`
  - **Category C — plugin-bundled** (varies per install): `/security-review`, etc.
- **Feature-gated subset**: only some appear in any given session's available-skills system reminder. On this machine (2026-05-05), `batch`, `claude-in-chrome`, `debug`, `dream`, `/commit`, `/init-verifiers`, `/insights` were NOT advertised — they're gated by feature flag, env var, or version. Run `strings $(which claude) | grep -oE 'T\\\$\\(\\{name:"[a-z][a-z0-9-]+"' | sort -u` (and the equivalent for category B) after each Claude Code upgrade to see the full set, then probe the gated ones (e.g. type `/insights` and see if it resolves) to discover what's actually invocable.
- **Most-missed-by-rivendell-users**: `update-config` (only way to set hooks — memory cannot enforce automated behavior; the harness needs settings.json), `fewer-permission-prompts`, `/insights` (per-session usage analysis), `/init-verifiers` (auto-create verifier skills, complements rivendell's QA tooling). Tell new colleagues about these — they're invisible in the rivendell skill audit.
- **Implications**:
  - Skill audits (`bin/sk audit`, README catalog generator) only see the rivendell tree and won't list these. That's correct — rivendell isn't responsible for them — but a maintainer might wrongly assume the audit is exhaustive.
  - Skill counts in dashboards and catalogs reflect rivendell-managed only. Add a footnote when reporting "total skills" if precision matters.
  - Built-in skills auto-update with Claude Code version bumps. No deploy / symlink-fix needed for them.
  - You **can't override or modify** a built-in skill's prompt without overshadowing it via a same-name rivendell skill — but that splits the namespace and is rarely worth it.
- **Diagnostic recipe**: To check if a skill is file-based or built-in:
  ```
  find ~/Documents/Projects/rivendell/skills ~/.claude/skills ~/.claude/plugins \
       -maxdepth 5 -type d -name "<skill-name>" 2>/dev/null
  # if empty: probably built-in; verify with
  strings $(which claude) | grep '"<skill-name>"'
  ```
- **Generalization**: Skills in Claude Code come from **three sources** (rivendell, plugins, built-in). When a skill name doesn't match the rivendell tree, it's not a missing skill — check the other two before chasing the file.

## 2026-05-05 — `~/.claude/stats-cache.json` is no longer maintained by Claude Code; dashboards depending on it get stale

- **Category**: knowledge_gap (Claude Code behavior change discovered while debugging dashboard)
- **Context**: User reported「tool call 紀錄是不是有期限？感覺怪怪的」. Investigation found `~/.claude/stats-cache.json` had `lastComputedDate: 2026-02-16` and file mtime stuck at 2026-02-18 — **77 days frozen** on an active machine. Meanwhile `~/.claude/projects/*.jsonl` had 27 files modified in the last 2 days (active). Claude Code clearly stopped writing to stats-cache.json at some point in early 2026 (probably a CLI version upgrade) but kept writing JSONL session logs as before. The dashboard's `tokens.py` still treated stats-cache as the primary source, supplemented by `_parse_recent_sessions()` which filtered JSONL files by **mtime ≥ lastComputedDate** and attributed each entry's date to the **file's mtime, not the per-line timestamp**. Result: a multi-week black hole in the daily breakdown (entire month of March 2026 invisible) plus mis-attributed dates for sessions whose JSONL file was rewritten on a different day than the original work.
- **Rule**: For Claude Code telemetry/usage dashboards, **trust `~/.claude/projects/*.jsonl` only**. `stats-cache.json` is on the deprecation glide path and silently freezes when a CLI version no longer writes it. Per-line `entry.timestamp` is the only reliable date attribution — `path.stat().st_mtime` lies because the JSONL file gets rewritten on session-resume.
- **Symptoms the same trap will produce in other places**:
  - Daily activity charts with month-shaped gaps
  - Token totals frozen at some past date despite active CLI usage
  - "Earliest date" stuck on a past month while everything else is current
  - Per-day model breakdown that's empty or zero-token for recent days
- **Fix pattern (this session)**: Refactored `dashboard/lib/tokens.py` so `get_daily_usage`, `get_model_summary`, `get_total_stats` all delegate to `get_filtered_usage()` (which already parses JSONL with per-line timestamps correctly). Added a 60-second TTL in-process cache (`_cached_full_usage()`) since full parse is ~1.1s for 500MB / 1108 files — fast enough not to need anything fancier. Deleted dead helpers `_parse_recent_sessions`, `_parse_one_session`, `_parse_one_session_for_project`, the `STATS_CACHE` constant, and `_read_stats_cache`.
- **JSONL retention is a hard floor**: Claude Code rotates old session JSONL files. On this machine the JSONL horizon was **2026-03-31** (today is 2026-05-05). Anything earlier is unrecoverable from JSONL alone. If a dashboard truly needs deeper history, it has to **persist its own aggregated copy** during the JSONL retention window rather than re-parse on demand.
- **Generalization**: Any rivendell tool that today reads `stats-cache.json` (search the codebase for `STATS_CACHE` / `stats-cache`) is at risk of the same silent freeze. Check on each repo audit. The `audit_importer.py` in this same dashboard imports a non-existent `upsert_usage` from tokens.py — likely also a casualty of an earlier refactor; flagged but not touched in this fix.

## 2026-05-03 — Storyline review IS the leverage point for deck-building (slide-office-hours = red-team gate, not generator)

- **Category**: best_practice (user-converged through 5 rounds of refinement)
- **Context**: Designing slide-office-hours skill from cd63836f session evidence. Through iteration the user converged on: 力成 deck ran smoothly because **storyline was clear before动工**; 光泉 deck wasted 5 edit cycles because storyline was being figured out *during* slide work.
- **Rule**: For deck-building, the storyline review/establishment process IS the leverage point. Everything downstream (slide layout, copy expansion, PPTX export, spacing) runs cheap when storyline is locked, expensive when it isn't.
- **Implications for skill design**:
  - slide-office-hours must be a **review gate**, not a generator. User writes storyline.md → skill red-teams it against known failure modes → reject / accept.
  - AI must NOT propose storyline content. Default AI voice = 公開資料 voice = exactly the failure mode this skill exists to catch. AI's job is challenge, not creation.
  - The skill is upstream of slide-workflow (which already does outline → content → generate). slide-office-hours produces the signed-off storyline.md that slide-workflow consumes.
  - Workflow chain: customer-intel (AI市調) → user writes storyline.md → slide-office-hours (red-team review) → slide-workflow (AI generates slides) → visual收尾 (AI spacing tweaks)
- **Review checklist structure (3 layers)**:
  - Universal failures: 公開資料 voice anywhere; exit criteria missing/vague; organizing structure absent/inconsistent; 5 fact-check items missing or unsourced; solution = capability雜燴 with no focused angle
  - Stage-specific: first-call needs ≥3 operator猜題; post-discovery needs "Discovery learned X, proposal changed to Y"; proposal needs scope紅線+退場機制; final-pitch needs explicit competitor differentiation
  - Profile-specific: 大型科技廠 (力成) operator猜題 must be backed by cross-customer pattern + must name differentiation target (同業/顧問/雲端商/自建); 傳產中小 (光泉) needs ≥3 operator猜題; 公部門 needs法規+預算科目+首長對象
- **Generalization**: This review-gate pattern applies to other "creative output" skills where AI's default voice is the failure mode (pitch-deck, sales-material, sow-writer's narrative sections, internal-comms). The skill's value comes from refusing to do the part AI is bad at, while ruthlessly catching that part when human introduces it.

## 2026-05-03 — Presales deck content edge: operator-level猜製程/業務流程 > 公開資料合理推測

- **Category**: best_practice (user-validated, contradicted my initial framing)
- **Context**: Analyzing the cd63836f session (光泉 first-call deck, 2026-04-29 → 04-30) for slide-office-hours skill design. From the last 30 edits I proposed splitting deck content into "fact-based (公開資料推測) vs speculative (猜題)". User immediately corrected: **「公開資料合理推測 目前效果都不好，我自己猜生產製程跟業務流程得到的結果反饋通常會更好」.**
- **Rule**: For B2B first-call / pitch decks, the content edge comes from **operator-level guesses about the customer's 生產製程 / 業務流程**, not from公開資料推測. The latter is actively bad — it signals you didn't think specifically about this customer.
- **Why公開資料推測 underperforms**:
  - Generic — customer can't tell you've thought specifically about them
  - 「你 google 一下也寫得出來」— no demonstrated edge
  - Gets polite acknowledgement, never moves the conversation
  - Framing the slide as「依公開資料合理推測」literally tells customer you didn't go deeper
- **Why operator-level猜測 wins**:
  - Demonstrates you've thought like someone who runs their floor / pipeline
  - If wrong → customer corrects you = free Discovery data + customer feels heard (correcting feels good)
  - If right → instant credibility (「你怎麼知道？」)
  - Either outcome makes the deck distinctive in the room
- **cd63836f evidence supporting this**: Cycle 1 (05:58) created the「光泉潛在議題」slide framed as「依公開資料 + 食品業趨勢初步設想」. Cycle 4 (07:11–07:18) rewrote it with operator猜測（酪農 SOP / 飼料 GenAI / 配貨預測 / 跨通路 SKU mix / 自家牧場 vs 契作酪農 distinction）. The rewrite was the upgrade — and cycle 4's content is what should have been in cycle 1.
- **Implications for slide-office-hours skill design**:
  - DO NOT include a "fact-based vs speculative" forcing question — the binary is wrong.
  - DO include: 「對這個客戶的生產製程 / 業務流程最大膽的 3 個 operator 猜測是什麼？(不准抄公開資料)」
  - Fact-check question stays, but reframed: 「最不能搞錯的 5 個基本事實是什麼？」— these are table stakes (own-goal prevention), separate from the content edge
  - Reserve公開資料 only for: market sizing, regulatory context, basic company facts. Never for the議題 / 解法 slides.
- **Generalization**: Applies to all rivendell skills that touch presales decks — pitch-deck, sales-material, presales-pipeline, slide-workflow, and the proposed slide-office-hours.

## 2026-04-28 — Diff-before-replace when "fixing" symlinks against pre-existing real directories

- **Category**: best_practice
- **Context**: While building `bin/sk-deploy-symlink-fix` to repair the 11 missing-symlink WARNs in tester reports, discovered that the targets in `~/.claude/skills/` weren't *missing* — they were real directories (Apr 7-14 timestamps), pre-symlink-convention copies. A naive symlink-fix script would either (a) skip them all because "something exists" (the v1 of my script did this), leaving the WARN unresolved, or (b) clobber them, potentially losing local edits the user had made post-copy.
- **Pattern**: When a maintenance script wants to enforce "this path should be a symlink to X", and the path is currently a real directory, run `diff -rq <repo_dir> <target_dir>`:
  - **No output** → byte-identical, safe to `rm -rf` and replace with symlink. Log as `CONVERTED`.
  - **Any output** → diverged, leave alone and log as `DIVERGED, manual review`. Never auto-clobber divergence — the user may have made intentional edits in the deployed copy.
- **Verification**: All 11 in this case were byte-identical (recursive diff returned nothing for SKILL.md and bundled subdirs alike), so they all converted cleanly. The script is idempotent — re-running it on healthy state produces zero output and zero changes.
- **Generalization**: This applies to any "switch from copy-deployment to symlink-deployment" migration. The diff is the safety check; without it you have to choose between leaving stale state forever or risking clobber of user edits.

## 2026-04-27 — Half-built `.next` (BUILD_ID present, chunks missing) makes Next.js 500 on every request — watchdog restart can't fix it

- **Category**: best_practice
- **Context**: After deploying the watchdog, web 500'd with `Cannot find module '../chunks/ssr/[turbopack]_runtime.js'` from `.next/server/app/page.js`. The watchdog correctly detected and `kickstart -k`'d the service, but the kickstart didn't fix it — the artifact on disk was broken, so every restart failed the same way.
- **Root cause**: `dashboard-next/start-web.sh` only rebuilds when `.next/BUILD_ID` is absent **or** sources are newer. It does not detect a half-finished build. If an earlier `npm run build` was killed mid-flight (SIGKILL from launchd grace expiry, OOM, disk full, Cmd+C), Next.js may have already written `BUILD_ID` and some output files but not all turbopack runtime chunks. `start-web.sh` then sees BUILD_ID, assumes the build is good, and runs `next start` against a poisoned cache.
- **Fix in this session**: `cd dashboard-next && rm -rf .next && npm run build && launchctl kickstart -k gui/$UID/com.sk.dashboard.web`. Web back to 200.
- **Prevention pattern**: Two-phase build — `npm run build` to a temp dir or with `--out-dir`, only `mv` it into place after success. The presence of `.next/BUILD_ID` should be a *commit point*, not something writable mid-build. Or: keep a sentinel like `.next/.build-complete` that's `touch`ed only after `npm run build` exits 0, and let `start-web.sh` check that instead of `BUILD_ID`.
- **Why the watchdog can't see this class of bug**: an HTTP-probe watchdog can detect the symptom (500) but `launchctl kickstart -k` only re-runs the same start script against the same broken artifact. Bad caches need cache invalidation, not process restart. Detection-and-restart is necessary but not sufficient.

## 2026-04-26 — `launchd KeepAlive` only catches process death, not hung processes — pair it with an HTTP-probe watchdog

- **Category**: best_practice
- **Context**: User reported "rivendell 又掛了" (the dashboard intermittently goes unresponsive). Both `com.sk.dashboard.api` and `com.sk.dashboard.web` already had `KeepAlive: true` in their plists, yet the dashboard was still going dark from the user's POV. At time of investigation both processes were live (PIDs 2086 and 2077) and the ports were listening, but the user had been seeing recurring outages.
- **Why `KeepAlive` alone is insufficient**: `launchd`'s `KeepAlive: true` only restarts a service when the process **exits**. It cannot detect:
  - A deadlocked event loop (port still listening, accept() never completes)
  - A frozen worker holding the only reqlock
  - A uvicorn that's still running but stuck in some library call
  In all these cases the process is "alive" by every signal launchd watches, so it never restarts.
- **Pattern**: Add an external HTTP-probe watchdog. The one I built (`bin/sk-watchdog`) runs every 60s via launchd `StartInterval`, curls each service URL with `--max-time 5`, and on threshold-many consecutive failures calls `launchctl kickstart -k gui/$UID/<label>` to force-restart the stuck service. Three details that matter:
  1. **Threshold + grace period** — restart on N consecutive failures (avoids restarting on one transient hiccup), then ignore that service for `GRACE_SECONDS` after restart (avoids restart-loop while the new process is starting up).
  2. **State file** — `reports/.watchdog-state` keeps `<key>:<consecutive_failures>:<last_restart_ts>` per service across watchdog invocations (each invocation is a fresh process, so state must be on disk).
  3. **Silent on success** — only write `reports/watchdog.log` on FAIL/RESTART/RECOVER events. If everything is healthy the log stays empty, which makes anomalies obvious instead of buried in noise.
- **Integration with `agents/agents.conf`**: A new row `com.sk.dashboard.watchdog | rivendell | bin/sk-watchdog | interval | 60 | reports` plus a re-run of `bin/sk-setup-agents` was all that was needed — the existing `interval` schedule type just worked.
- **Verify**: `launchctl list | grep com.sk.dashboard.watchdog` should show the label loaded; manually invoking the script in a healthy state should produce no log output and no state file changes.

## 2026-04-23 — macOS "Failed to fetch" from browser but curl 200 = IPv4-only uvicorn being shadowed by a Docker IPv6 listener

- **Category**: best_practice (a debugging checklist, not a correction)
- **Context**: Dashboard web app showed `Error: Failed to fetch` on every page that hit the API. Even incognito windows failed. But every curl I ran from the terminal — including curls with `Origin: http://127.0.0.1:3000` + `Content-Type: application/json` headers that simulated the exact React fetch — returned `200 OK` with correct CORS headers. I spent significant time chasing browser-state theories (cache, service workers, extensions, DevTools offline toggle) because curl was "proving" the server was fine.
- **Actual root cause**: A forgotten Docker container `sk-dashboard-api` (started 2 weeks prior, image `rivendell-dashboard-api`) had `0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp` port mappings. It was running an OLD build of the FastAPI server — specifically one missing the `http://127.0.0.1:3000` entry in `allow_origins` that I'd added on 2026-04-20.
  - Our macOS uvicorn bound only `127.0.0.1:8000` (IPv4).
  - Docker's userland proxy bound BOTH `0.0.0.0:8000` (IPv4) AND `[::]:8000` (IPv6). Docker "won" IPv6 uncontested.
  - macOS `/etc/hosts` has `::1 localhost` alongside `127.0.0.1 localhost`.
  - Browsers' Happy Eyeballs (RFC 8305) prefers IPv6 when available. They resolved `localhost` to `::1`, connected via Docker's proxy, reached the stale container uvicorn, got `400 Disallowed CORS origin` on preflight, and reported "Failed to fetch" to the React app.
  - Curl's Happy Eyeballs behavior defaults to IPv4-first on most macOS builds (or connects to whichever address responds first, which was the fast-local 127.0.0.1). That's why curl kept reaching the good uvicorn and saying "looks fine."
- **Debug checklist when a browser sees "Failed to fetch" but curl sees 200**:
  1. `lsof -nP -iTCP:<port> -sTCP:LISTEN` — list **every** listener, not just one. Look for separate IPv4 and IPv6 rows; they may be different processes.
  2. `curl -v http://[::1]:<port>/...` AND `curl -v http://127.0.0.1:<port>/...` with the **same** headers as the failing browser. If responses differ, you have two servers.
  3. `docker ps -a --format '{{.Names}} {{.Ports}}' | grep <port>` — Docker Desktop keeps port-published containers running invisibly; they survive across macOS reboots if "Start Docker Desktop when you log in" is on.
  4. When the browser shows `Failed to fetch` (not `CORS error`), it's often the **preflight** failing. A simple GET can succeed while OPTIONS fails. Always test OPTIONS too.
  5. `access-control-max-age: 600` means a failed preflight is cached per-tab for 10 min. Browser reloads alone don't clear it; close the whole tab/window.
- **Fix**: `docker stop sk-dashboard-api`. Follow-up: `docker rm` the stopped duplicates, or decide whether the whole docker-compose setup should be taken down — per the user's 2026-04-20 instruction, rivendell is no longer meant to run in Docker.

## 2026-04-22 — Bash `git log | head` under pipefail dies with exit 128 on empty-HEAD repos

- **Category**: best_practice
- **Context**: `sk maintain` (and therefore the launchd agent `com.sk.agent.rivendell.maintain`) was silently exiting 128 with zero output on stdout and stderr. Root cause: `bin/sk` has several lines of the form `"$(git -C "$proj_dir" log -1 --format='%s' 2>/dev/null | head -c 60)"`. The `2>/dev/null` hides git's "fatal: your current branch does not have any commits yet" message but does NOT mask the exit code. When git log fails (e.g. rakucamp had 22 dirty files and no commits), it exits **128** (git's fatal-error convention). Under `set -o pipefail`, that 128 propagates as the pipeline's exit. `$(…)` captures it. `set -e` then trips and the script dies — but since stdout/stderr are redirected to per-day log files, the error never reaches the launchd-visible stderr. The result is a mysterious exit 128 with empty logs.
- **Rule**: Any `$(git … 2>/dev/null [| …] )` pipeline under pipefail must end with `|| echo ''` (or similar fallback) to guarantee the command substitution produces a usable empty string. One sibling on line 2722 had the guard; the neighbors on 2723 and 2775 did not — exactly the two sites that broke.
- **Debugging tip**: When a launchd job exits 128 with no log output, run `bash -x ./script > /dev/null 2>/tmp/trace.err` and `tail /tmp/trace.err` — the last traced command will pinpoint the bail-out site, even when normal stderr is silent.

## 2026-04-21 — Auto-stage PostToolUse hook silently adds files to staging; always check `git diff --cached --name-only` before commit

- **Category**: correction
- **Context**: This repo runs a PostToolUse hook that auto-git-stages files after Claude edits/writes them. During `/qa` fix + commit flow, the hook had already staged unrelated files like `reports/harvest-2026-04-20.md` (created by a scheduled agent on the same day). When I ran `git commit` expecting to ship only my one-line change to `server.py`, the commit swept in the pre-staged harvest reports.
- **Recurrence**: Happened **3 times** across two sessions on 2026-04-21/22. Even after writing a learning entry (session 1), the mistake repeated in session 2 — the lesson doesn't stick as a passive rule; it needs a mechanical step.
- **Rule (hardened)**: Make staging inspection a SEPARATE Bash call before each `git commit`, never chained with `&&`. Structure:
  1. Run `git diff --cached --name-only` on its own → read the output → decide.
  2. If anything unintended is staged, `git restore --staged <path>` FIRST, then re-run step 1 to confirm.
  3. Only then run `git commit`.
  The intermediate `&&`-chained "check-then-commit" pattern fails because a multi-line pipeline runs too fast to meaningfully review.
- **Special note on `reports/*`**: Per the user's standing instruction, files under `reports/` (harvest-*.md, skill-audit-*.md, test-*.md, maintain-*.log, `.harvest-*.json`) are always kept out of repo-cleanup commits — they're scheduled-agent output the user curates manually.
- **Recovery recipe**: `git reset --soft HEAD~1` → `git restore --staged <unwanted>` → re-commit. Leaves the working tree identical, rewrites only the most recent commit.

## 2026-03-18 — Repo rename breaks all agents and dashboard if not done systematically

- **Category**: best_practice
- **Context**: Renamed repo from `skills-test` to `rivendell`. Hardcoded repo name strings were scattered across LaunchAgent plists, agent cron scripts, dashboard lib, and projects.json. Dashboard also had a venv with stale absolute-path shebangs.
- **What breaks if rename is done manually without scanning**:
  - LaunchAgent plists (`~/Library/LaunchAgents/com.sk.agent.skills-test.*`) still point to old path → agents silently fail to run
  - Dashboard plists (`com.sk.dashboard.api/web.plist`) still point to old path → dashboard can't restart after reboot
  - `bin/sk-*-cron` scripts record runs under old project name → dashboard shows no history
  - `dashboard/lib/agents.py` still labels live agents as old project → dashboard UI shows wrong project
  - venv shebangs in `dashboard-next/api/.venv/bin/*` embed absolute paths → pip/uvicorn break after move
  - `~/.claude/projects.json` still points to old path → Claude Code can't find project
- **Resolution protocol** (must follow in order):
  1. `launchctl unload` all affected agents
  2. Rename/move the folder
  3. `grep -r "old-name" ~/Library/LaunchAgents/ ~/Documents/Projects/<repo>/bin/ ~/Documents/Projects/<repo>/dashboard/` to find all references
  4. Update all plist files (Label + ProgramArguments + log paths)
  5. Update all cron scripts (`_sk_exec_record_run` project arg)
  6. Update `dashboard/lib/agents.py` project fallback
  7. Update `~/.claude/projects.json`
  8. Delete and recreate venv (shebangs are not relocatable)
  9. `launchctl load` new plists
  10. Rename GitHub repo last (redirect keeps old URL working)
- **Also breaks (easy to miss)**:
  - **Other repos** that import from this repo (e.g. `news_stock/scripts/*.sh` sourcing `skills-test/bin/sk-exec-lib`) — must `grep -r "old-name" ~/Documents/Projects/` across ALL projects, not just the renamed one
  - `.next/` build cache embeds absolute paths — must `rm -rf .next` and rebuild
  - `package-lock.json` caches repo name
  - Skill SKILL.md files that reference repo name in docs
- **Rule**: When user asks to rename a repo/project, automatically scan ALL of the above locations **plus all sibling repos** before touching anything, present a complete change list, then execute in the correct order.

## 2026-03-18 — Never hardcode repo/project name in scripts; derive it dynamically

- **Category**: best_practice
- **Context**: After renaming `skills-test` → `rivendell`, cron scripts and `agents.py` still had the project name hardcoded as string literals. User also deploys the skills pack to multiple machines where the folder name may differ.
- **Root cause**: Using `"rivendell"` (or any literal name) instead of deriving from the repo path at runtime.
- **Fix pattern**:
  - Shell scripts: `PROJECT_NAME="$(basename "$REPO_DIR")"` then use `"$PROJECT_NAME"` everywhere
  - Python: `PROJECT_DIR.name` (since `PROJECT_DIR = Path(__file__).parent.parent.parent`)
  - Corollary: `REPO_DIR` / `PROJECT_DIR` itself must also be derived dynamically (`dirname "$0"` / `Path(__file__)`) — never hardcoded absolute path
- **What should NOT be hardcoded**: project name in `_sk_exec_record_run`, agent label prefix, DB query filters, dashboard project fallback
- **What is unavoidably machine-specific**: LaunchAgent plists (launchd requires absolute paths) — these must be generated per-machine via an install/setup script, not committed as static files
- **Rule**: Any string that would change on rename or cross-machine deploy must be derived at runtime, not written as a literal.

## 2026-03-17 — g0v PCC API brief.type is NOT the procurement method

- **Category**: knowledge_gap
- **Context**: Building tender-scraper skill, assumed `brief.type` from g0v API (`pcc-api.openfun.app/api/listbydate`) would contain the procurement method (招標方式) like "公開徵求"
- **Reality**: `brief.type` is always `"公開招標公告"` for all public tenders. The actual procurement method (公開招標 / 公開徵求 / 限制性招標) is only available in the **detail API** at `招標資料.招標方式`
- **Impact**: Cannot filter by 招標方式 at listing level — must fetch detail for each tender first, then filter. This significantly increases API calls needed per scrape run.
- **Resolution**: Updated scraper.md workflow to fetch-then-filter pattern at Phase 3

## 2026-03-24 — settings.local.json corrupted by one-time Bash permissions

- **Category**: best_practice
- **Context**: `.claude/settings.local.json` had accumulated ~50 one-time Bash commands as permission entries (git commit, python3 -c, find, etc.), plus missing commas in the array, making the file invalid JSON. Claude Code silently skipped the file.
- **Learning**: Periodically audit `settings.local.json` — one-time Bash approvals get saved as permanent permission patterns. Clean out entries that aren't reusable glob patterns (like `Bash(npm *)`) and keep only intentional permissions.

## 2026-03-24 — macOS TCC blocks /bin/bash from ~/Documents/ in launchd

- **Category**: knowledge_gap
- **Context**: Replacing compiled sk-agent-run binary with shell script caused "Operation not permitted" (exit 126) for all launchd agents accessing ~/Documents/
- **Learning**: macOS TCC (Transparency, Consent, and Control) protects ~/Documents/, ~/Desktop/, ~/Downloads/. When launchd spawns `/bin/bash`, it has no Full Disk Access. A compiled binary can be granted FDA individually. Shell scripts cannot.
- **Resolution**: Keep a compiled C launcher (`agents/sk-agent-run.c`), compile during setup, grant FDA once per machine.

## 2026-03-24 — Autoresearch discard must NOT use git clean

- **Category**: best_practice
- **Context**: `sk-autoresearch` discard step used `git checkout -- . && git clean -fd`. The `git clean -fd` deleted untracked files from other agents (subsidy data, client projections, tender cases) that were never committed.
- **Learning**: In multi-agent repos, NEVER use `git clean` for discard. Only `git checkout -- .` to revert tracked modifications. Untracked files belong to other agents' output.
- **Also learned**: Autoresearch metric commands must be local and deterministic — never depend on external API calls (rate limits make results non-reproducible).

## 2026-03-24 — Cross-project exec-lib sourcing needs export

- **Category**: best_practice
- **Context**: `SK_EXEC_REPO_DIR="$VAL" source exec-lib` worked during sourcing but the variable wasn't available when functions were called later under `set -u`
- **Learning**: Use `export SK_EXEC_REPO_DIR=...` before `source`, not inline `VAR=val source file`. The inline form may not persist for later function calls.

## 2026-04-01 — Always check port map before starting a dev server; ask before allocating new ports

- **Category**: correction
- **Context**: Started RTK dev server on port 3001 without checking the port map. Port 3001 was already allocated to news-stock Frontend. RTK had no entry in the port map at all.
- **Two mistakes**:
  1. Assumed port 3001 was free instead of reading the port map first
  2. Started a new project's server without first asking the user to assign it a port
- **Rule**: Before starting any dev server, (a) read `mockups/port-map.html` SERVICES array to find what's taken, (b) if the project has no assigned port, ask the user what port to use, (c) only then `lsof -i :<port>` to confirm it's actually free, then start.

## 2026-04-07 — launchd agents: source across ~/Documents/ intermittently fails with EDEADLK

- **Category**: best_practice
- **Context**: `sk-harvest-cron`, `sk-maintain-cron`, `sk-tester-cron`, `knowledge-sync.sh` all had bare `source sk-exec-lib` under `set -euo pipefail`. In launchd environment, sourcing files in `~/Documents/` (different project) intermittently fails with "Resource deadlock avoided" (EDEADLK), causing the script to exit early with a non-zero code (launchctl showed exit 78).
- **Learning**: Wrap any cross-project `source` with `set +e ... set -e` + `|| true`:
  ```bash
  set +e; source "$RIVENDELL_DIR/bin/sk-exec-lib" 2>/dev/null || true; set -e
  ```
  The main task still runs; only the optional dashboard recording is skipped.
- **Also**: Sales agent plists had label prefix `com.sk.agent.sales.*` but project dir name is `sales-assistant`. The `sk agent start` CLI derives label from dir name. Must match or `sk maintain` shows them as "unloaded". Fix: unload old plists, reinstall with `sk agent start --project sales-assistant`.

## 2026-04-07 — Docker API: Path(__file__).parent×N breaks when WORKDIR differs from local layout

- **Category**: best_practice
- **Context**: `dashboard-next/api/server.py` uses `Path(__file__).resolve().parent.parent.parent / "reports"` to find the reports dir. Locally this resolves to the repo root. In Docker, `server.py` is copied to `/app/server.py` so `.parent.parent.parent` = `/` and `/reports` doesn't exist (mounted at `/data/reports`).
- **Fix**: Use env var with fallback: `Path(os.environ.get("REPORTS_DIR", str(Path(__file__).resolve().parent.parent.parent / "reports")))`. Set `REPORTS_DIR=/data/reports` in docker-compose `environment:`.
- **Rule**: Any path that diverges between local dev and Docker must be an env var, not computed from `__file__`.

## 2026-03-24 — Dashboard must discover log paths from plist, not assume reports/

- **Category**: best_practice
- **Context**: Dashboard `/live` and `/files` only searched `reports/` but sales agents log to `materials/tenders/`, `materials/subsidies/`, etc.
- **Learning**: Read plist `StandardOutPath` to find correct log location. Added plist-based log discovery to `/live`, `/files`, `/file` endpoints.
