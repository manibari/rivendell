# Rivendell Roadmap

> Living roadmap for the rivendell skills library + automation platform.
> **Reviewed every iteration** (weekly, ISO week) at `workflow-retro`. Kept in
> sync with [CHANGELOG.md](CHANGELOG.md) by the `doc-drift-sync` skill — a Done
> item here must have a CHANGELOG entry.
>
> Iteration cadence: 1 week = 1 retro = 1 doc-alignment pass. See
> `skills/meta/doc-drift-sync/SKILL.md` → "The iteration cycle".

## Now (in flight)

- **Version/roadmap/iteration system** — this ROADMAP + CHANGELOG + `doc-drift-sync`
  skill; anchor doc hygiene to the weekly retro.
- **Telegram ops-bridge** (infra under `~/.claude`, `~/.config`, `~/.local/share`):
  session-completion notifier with one-tap **Continue / Wrapup / Commit&Push**
  buttons; owned `ops-bot`; `ask-telegram` MCP tool for remote choice-questions
  with a 5W1H "都不對" escape hatch. (MCP server registration — 待補)

## Next

- ~~Retire `knowledge-graph` skill~~ → **翻案 (2026-08-29)**: 0 triggers 的根因是
  零資料 + recall 未啟用，非 skill 無用。已啟用：`scripts/kg.py` 寫入 API +
  `bin/sk-facts-cron`（daily 21:30，從 session 抽 durable facts）+
  `~/.claude/CLAUDE.md` recall 區塊。知識庫定位：個人助理三角（skills 能力 /
  知識庫記憶 / SaaS 資料進出）的記憶層。
- **知識庫投影層：行事曆 + to-do list** — facts.jsonl 是機器記憶，人看的介面
  是行事曆與待辦（「這樣比較像是人的理解」）。投影 agent 讀知識庫 →
  Google Calendar / Tasks（走 SaaS OAuth）或 dashboard 頁面；Telegram
  ops-bridge（見 Now）作提醒通道。依賴：知識庫先累積資料。
- **Avatar 後續** (2026-08-30)：神經語音 TTS（demo 給客戶前必換，瀏覽器內建太機器）；
  gateway 對外前先加 auth（現綁 127.0.0.1 不可 tunnel）；avatar 對話 transcript
  落地供 facts-cron 抽取；VRM 模型質感升級（自製/購入）。
- **訊息軟體整合** — Telegram 讀取（正式 API，併 ops-bridge 一起做，含建議回覆）；
  Slack user token 可讀；LINE/WhatsApp 無個人 API 且有封號風險 → 只做半手動
  （貼對話/截圖 → 知識庫輔助建議回覆）。(2026-08-29)
- **Rightek-CRM 實際寫入** — dispatch 的 `crm` 路由已就緒（graceful fail 留 retry）；
  等 Rightek-CRM 服務啟動（FastAPI :8100，agent 讀 openapi.json 即知接口）。(2026-08-29)
- **Root-cause agent exit-1 dual-state** — `harvest` / `material-health` report
  failure while producing output (W22 action 2).
- **`doe-ml-analysis` skill** — DOE/process ML EDA (heatmap→PCA→regression R²);
  harvest-rated Strong, hits the known 製造運營 domain gap.
- **`bin/sk index`** — INDEX-first tiered skill discovery to cut per-session token
  cost (FEATURE_REQUESTS 2026-05-08).

## Later

- **`presales-poc-scoping`** mother-skill — domain-agnostic PoC acceptance scoping
  (n≥3 across poc-to-product-audit / data-poc-scoping / cv-poc-acceptance-criteria;
  watch item from W22).
- **Domain skill gaps** (抽 when a real case lands): 商業洞察 (市場調研/配給/庫存/通路),
  製造運營 (視覺檢測 AOI/SPC, 排程/產能), 工安治理 (EHS), 法務 (RFP/NDA/MOU)
  (FEATURE_REQUESTS 2026-05-18).
- **DFM 知識 reference skill** — PCB CAM/DFM domain knowledge loader over the Vault
  SoT (knowledge→skill library pattern, instance #1).

## Done

- chimesflow-design + app-ops-baseline gate skills (`ff8ea85`).
- sk-setup-agents PROJECTS_DIR landmine + ssot-drift cron fix (`8007c6d`).
- dashboard Git 衛生 panel — uncommitted/unpushed across ~/code repos (`7523816`).

---

_Add items as they surface; move between sections at each weekly retro. Don't
fabricate completed work — a Done entry needs a real commit/CHANGELOG line._
