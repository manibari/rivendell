---
name: context-journal
loop: platform
pdca: do
description: Auto-append a per-turn work-log to disk so context can be recycled without losing the thread — /compact (and built-in auto-compact) become lossless, and past a heavier threshold the session can be CLOSED and continued in a fresh one via a handoff note that the next session picks up automatically. A two-tier reminder nudges you to /compact first, then to hand off and restart. Installs three Claude Code hooks (Stop + SessionStart + UserPromptSubmit). TRIGGER when user says /context-journal, "自動記錄工作日誌", "減少前文/token 浪費", "compact 前留紀錄", "自動提醒 compact", "提醒我關閉 session", "換手接續", "交接單", "另開 session 繼續", "安裝 session log hook". DO NOT TRIGGER for one-shot "save my work" snapshots (use gstack-context-save), post-compaction git-based recovery (use context-recovery), or end-of-day cleanup with commits and progress.md (use session-wrap).
when_to_use: when the user wants token savings from recycling context — set up or manage the auto-appended work-log, tune the compact/restart thresholds, or write the handoff note before closing a session and continuing in a new one.
version: 1.1.0
tags: [workflow, session-management, context, hooks, tokens, handoff]
languages: all
---

# Context Journal

自動把「每回合做了什麼／調了什麼／改了哪些檔」逐筆追加到磁碟上的 log，讓**回收 context**
這件事變成無損操作 —— 不管是壓縮（`/compact`）還是換手（關掉 session 另開一個），被丟掉的
前文都不再是唯一記憶來源。

**核心：模型／skill 本身既不能 `/compact` 也不能關 session**（兩者都是 harness 的動作）。
所以這個 skill 不「幫你」做這兩件事，而是：(a) 讓它們變安全，(b) 在該做的時候提醒你，
(c) 準備好接續所需的東西。

## 兩層門檻：先壓縮，再換手

| 前文量 | 建議動作 | 為什麼 |
| --- | --- | --- |
| < 300k | 什麼都不用做 | — |
| ≥ 300k（`.compact-threshold`） | `/compact` | log 已落地，壓縮無損；省下之後每回合重載肥前文的 token |
| ≥ 600k（`.restart-threshold`） | 產交接單 → 關掉 session → 另開 | 到這個量級 compact 不划算：它是**有損摘要**，而且會讓整份 **prompt cache 失效**。乾淨新 session + 一頁交接單起手約 5k tokens；compact 完常常還留 50k+ 的摘要殘渣 |

門檻是估的，不是實測值 —— 依專案調（見下方設定）。

## 運作機制（三個 hook，零手動）

```
每個 turn 結束
   └─ Stop hook (journal-stop-hook.sh)
        → 追加一筆到 ~/.claude/session-logs/<專案>/<session_id>.md
          · 時間戳 · 觸發該回合的請求 · 這回合新增的 git 改動 · 該回合摘要

每次送出 prompt
   └─ UserPromptSubmit hook (journal-compact-reminder-hook.sh)
        → 讀最後一筆 assistant usage 的精準 context tokens
          (input + cache_read + cache_creation)
        → 超過 tier 1 → 提醒「可無損 /compact」
        → 超過 tier 2 → 改為提醒「產交接單並換手」
        （有 cooldown 不連環叫；升級到 tier 2 會立刻說，不等 cooldown）

/compact 或 auto-compact 觸發（前文被壓縮）
   └─ SessionStart hook, source=compact|resume
        → 把 log 尾段 (~5KB) 以 additionalContext 自動注回

新 session 啟動
   └─ SessionStart hook, source=startup
        → 若 HANDOFF.md 存在且夠新（預設 240 分鐘內）→ 整份注回，然後歸檔
        → 沒有交接單就什麼都不注 —— 新 session 預設是乾淨的
```

- **log 存在 repo 外**（`~/.claude/session-logs/`），不進 git、不觸發 auto-stage hook。
- **per-turn 差異化**：`git status` 只記「這回合相對上一筆的新增」，不重複整棵工作樹。
- **per-project 分目錄**：hook 掛在全域，但 log 依專案 slug 分開。
- Hook 一律 `exit 0`、吞掉所有錯誤 —— 絕不會弄壞 session。

## 換手：`/context-journal handoff`

當使用者說「換手」「交接單」「我要關掉重開」，或被 tier 2 提醒觸發時：

**Step 1 — 產骨架**（只抓機械事實：branch、未 commit 檔案、近期 commit、work-log 尾段）

```bash
bash ~/.claude/skills/context-journal/scripts/session-handoff.sh seed
```

**Step 2 — 填語意部分。** 骨架裡有五個 `TODO(claude):` 區塊，逐一改寫 —— 這部分只有
當前 session 知道，腳本抓不到：

- **在做什麼** — 一兩句話講目標與動機
- **已經決定 / 已完成** — 把拍板的決定寫進去，新 session 才不會重問使用者
- **下一步** — 具體到可以直接動手，不要寫「繼續處理」這種
- **雷區** — 試過但行不通的做法；沒有就寫「無」
- **關鍵檔案** — `path:line` 形式，只列真的要再打開的

寫的時候假設讀者是**完全沒有前文的自己**。所有 `TODO(claude):` 都必須被取代掉。

**Step 3 — 告訴使用者可以關了。** 說明新 session 開起來會自動吃到交接單（4 小時內有效），
不必手動貼。

其他子指令：

```bash
S=~/.claude/skills/context-journal/scripts/session-handoff.sh
bash "$S" path     # 印出交接單路徑
bash "$S" show     # 看目前待領的交接單
bash "$S" clear    # 取消換手（歸檔，不刪）
```

交接單被新 session 吃掉後會移到 `handoff-archive/`，不會重複注入。過期的（超過 TTL）
留在原地不注入，可以自己開來看。

## 與鄰居 skill 的分工

- `gstack-context-save` — 一次性快照「存檔」。本 skill 是持續累積的 running log。
- `context-recovery` — compact 後從 git/檔案**回推**。本 skill 主動**寫**專屬 log，
  回推更精準（有語意摘要，不只 git 狀態）。兩者可並用：journal 是寫端，recovery 是備援讀端。
- `session-wrap` — **收工**才跑（commit、歸檔 learnings、更新 progress.md）。
  handoff 是**換手**：工作沒結束，只是換個 context window 繼續，不 commit、不收尾。

---

## 安裝 / 管理

全域註冊由 rivendell 的 manifest 負責（`data/global-hooks.json`）：

```bash
sk hooks           # 看三支 hook 是否已註冊
sk hooks install   # 註冊（冪等）
```

或用 skill 自己的安裝器（兩者寫入相同的 deploy-symlink 路徑，跑哪個都行）：

```bash
S=skills/workflow/context-journal/scripts/install.sh

bash "$S" status              # 查掛載狀態 + 是否有待領交接單
bash "$S" install             # 掛到全域 ~/.claude/settings.json
bash "$S" install --project   # 只掛到本 repo 的 .claude/settings.json
bash "$S" uninstall           # 移除 hook（log 檔保留）
```

- 冪等：重跑 `install` 不會重複掛載；舊版只聽 `compact|resume` 的 SessionStart matcher
  會被就地修好（沒有 `startup` 就吃不到交接單）。
- 不動既有 hook（例如 rivendell 的 sync-readme PostToolUse）。
- 掛載後**新開的 session** 才生效（hook 在 session 啟動時載入 settings.json）。

## 手動讀回 log（`/context-journal` 或「看工作日誌」）

```bash
SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
DIR=~/.claude/session-logs/$SLUG
ls -t "$DIR"/*.md 2>/dev/null | head -5      # 列出最近的 session log
tail -n 80 "$(ls -t "$DIR"/*.md 2>/dev/null | head -1)"   # 讀最新那份的尾段
```

讀出後，用 2-3 句摘要「上次做到哪、待辦是什麼」，再問使用者要不要接續。

## 設定

全域共用一份設定，都放在 `~/.claude/session-logs/`：

```bash
echo 400000 > ~/.claude/session-logs/.compact-threshold   # tier 1 門檻（預設 300000）
echo 800000 > ~/.claude/session-logs/.restart-threshold   # tier 2 門檻（預設 600000）
echo 150000 > ~/.claude/session-logs/.compact-step        # 忽略後每再增加多少才再叫（預設 100000）
echo 480    > ~/.claude/session-logs/.handoff-ttl-min     # 交接單有效分鐘數（預設 240）
```

- 門檻越低 → 越早提醒 → context 越精簡越省 token，但可能太頻繁中斷。
- 提醒狀態依 session 分開（`<專案>/.compact-remind-<session>`），記錄「上次叫到第幾層、
  在多少 token」。
- TTL 的用途是防呆：三天前的交接單自動注回只會誤導。

## 注意事項

- 依賴 `jq` 與 `perl`（macOS 內建）。
- Stop hook 每回合會讀 transcript 尾段 500 行 + 跑 `git status`，成本極低（次秒級）。
- 若 log 未生成：確認 (a) 已 `install` 且**重開過 session**；(b) 該回合非「無改動且回覆極短」
  的瑣碎 turn（那種會被刻意略過）。
- 提醒只是 `systemMessage`（顯示給你看），不佔 context。
