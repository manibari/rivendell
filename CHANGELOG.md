# Changelog

All notable changes to the rivendell platform are recorded here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

**Versioning = ISO week** (one iteration per week, closed at `workflow-retro`).
The `[Unreleased]` section collects changes mid-week; it is promoted to a dated
`## [YYYY-Www]` heading when the iteration closes. Kept aligned with
[ROADMAP.md](ROADMAP.md) by the `doc-drift-sync` skill.

## [Unreleased]

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
