---
name: context-journal
loop: platform
pdca: do
description: Auto-append a per-turn work-log to disk so /compact (and built-in auto-compact) become safe — the durable record of operations and decisions survives outside the context window, is re-injected automatically after compaction, and an early tunable reminder nudges you to /compact once context crosses a threshold. Installs three Claude Code hooks (Stop + SessionStart + UserPromptSubmit). TRIGGER when user says /context-journal, "自動記錄工作日誌", "減少前文/token 浪費", "compact 前留紀錄", "自動提醒 compact", "安裝 session log hook", or wants a running log that makes compaction lossless. DO NOT TRIGGER for one-shot "save my work" snapshots (use gstack-context-save) or post-compaction git-based recovery (use context-recovery).
when_to_use: when the user wants token savings from compaction without losing continuity — set up, manage, or manually read the auto-appended per-turn work-log.
version: 1.0.0
tags: [workflow, session-management, context, hooks, tokens]
languages: all
---

# Context Journal

自動把「每回合做了什麼／調了什麼／改了哪些檔」逐筆追加到磁碟上的 log，
讓 `/compact`（與 Claude Code 內建的 auto-compact）變成**無損**操作：被壓縮掉的
前文不再是唯一記憶來源，log 檔留在 context window 之外，compact 後又自動注回。

**核心：模型／skill 本身無法觸發 `/compact`**（那是 harness 的動作）。所以這個 skill
不「幫你 compact」，而是讓 compact 變安全 —— 該留的操作紀錄先落地，你就能放心砍前文
（或讓內建 auto-compact 自己觸發），省下重複載入前文的 token。

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
        → 超過門檻 → systemMessage 提醒「可無損 /compact」（有 cooldown 不連環叫）

/compact 或 auto-compact 觸發（前文被壓縮）
   └─ SessionStart hook (source=compact) (journal-sessionstart-hook.sh)
        → 把 log 尾段 (~5KB) 以 additionalContext 自動注回新 context
```

**為什麼要早期提醒**：Claude Code 內建 auto-compact 觸發得很晚（實測近 776k–1M
tokens 才動）。因為 context-journal 已讓 compact 無損，早點壓縮是安全的，且能省下
之後每回合重載肥前文的 token。提醒只是 systemMessage（顯示給你看），不佔 context。

- **log 存在 repo 外**（`~/.claude/session-logs/`），不進 git、不觸發 auto-stage hook。
- **per-turn 差異化**：`git status` 只記「這回合相對上一筆的新增」，不重複整棵工作樹。
- **per-project 分目錄**：hook 掛在全域，但 log 依專案 slug 分開。
- Hook 一律 `exit 0`、吞掉所有錯誤 —— 絕不會弄壞 session。

## 與鄰居 skill 的分工

- `gstack-context-save` — 一次性快照「存檔」。本 skill 是持續累積的 running log。
- `context-recovery` — compact 後從 git/檔案**回推**。本 skill 主動**寫**專屬 log，
  回推更精準（有語意摘要，不只 git 狀態）。兩者可並用：journal 是寫端，recovery 是備援讀端。
- `session-wrap` — 收工才跑。本 skill 每回合都跑。

---

## 安裝 / 管理

```bash
S=skills/workflow/context-journal/scripts/install.sh

bash "$S" status              # 查目前掛載狀態（全域）
bash "$S" install             # 掛到全域 ~/.claude/settings.json（跨專案都記錄）
bash "$S" install --project   # 只掛到本 repo 的 .claude/settings.json
bash "$S" uninstall           # 移除 hook（log 檔保留）
```

- 冪等：重跑 `install` 不會重複掛載。
- 不動既有 hook（例如 rivendell 的 sync-readme PostToolUse）。
- 掛載後**新開的 session** 才生效（hook 在 session 啟動時載入 settings.json）。

## 手動讀回 log（`/context-journal` 或「看工作日誌」）

當使用者想在 compact 前後手動查看目前 session 的紀錄：

```bash
SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
DIR=~/.claude/session-logs/$SLUG
ls -t "$DIR"/*.md 2>/dev/null | head -5      # 列出最近的 session log
tail -n 80 "$(ls -t "$DIR"/*.md 2>/dev/null | head -1)"   # 讀最新那份的尾段
```

讀出後，用 2-3 句摘要「上次做到哪、待辦是什麼」，再問使用者要不要接續。

## Compact 提醒門檻設定

```bash
# 第一次提醒的 token 門檻（預設 300000）
echo 400000 > ~/.claude/session-logs/.compact-threshold
# 忽略後每再增加多少 token 才再提醒一次（預設 100000）
echo 150000 > ~/.claude/session-logs/.compact-step
```

- 門檻越低 → 越早提醒 → context 越精簡越省 token，但可能太頻繁壓縮。
- 全域共用一份門檻檔；提醒狀態依 session 分開（`<專案>/.compact-remind-<session>`）。

## 使用建議

- 平常什麼都不用做，log 自動累積、超過門檻自動提醒。
- 覺得前文太肥時，直接 `/compact` —— compact 後 SessionStart hook 會把 log 尾段塞回來。
- 想確認有記到東西：跑上面的「手動讀回」。
- log 檔會隨 session 累積；舊 session 的 log 可自行清理
  （`~/.claude/session-logs/<專案>/`），不影響任何流程。

## 注意事項

- 依賴 `jq` 與 `perl`（macOS 內建）。
- Stop hook 每回合會讀 transcript 尾段 500 行 + 跑 `git status`，成本極低（次秒級）。
- 若 log 未生成：確認 (a) 已 `install` 且**重開過 session**；(b) 該回合非「無改動且回覆極短」
  的瑣碎 turn（那種會被刻意略過）。
