# Findings — Agent Registry v2

## sk-setup-agents 解析方式（Phase 2 生成器的對接點）
- `bin/sk-setup-agents:146`：`grep -v '^#' | while IFS='|' read -r label project_rel script sched_type sched_val log_dir_rel extra_args`
- 純 pipe 7 欄、註解行跳過。**生成器只要輸出同格式，bash 管線一行都不用改。**
- schedule 解析：`interval`（秒）、`calendar`（H:MM 或 W:H:MM）、`calendar_multi`（逗號分隔）、`keepalive`（dashboard 服務）。
- label 慣例：`com.sk.agent.<project>.<name>`；但 dashboard 服務是 `com.sk.dashboard.*` → schema 的 `label` 覆寫欄位必要。

## .claude/agents.json 實際內容與讀者（D2 證據）
- 欄位（dashboard/lib/agents.py:29-37 `AgentsJsonConfig`）：`description`, `merge_strategy`(auto|pr), `allowed_paths`, `forbidden_paths`, `max_files_changed`, `qa_pre_commit`(off|auto|script)
- 唯一讀者：`dashboard/lib/agents.py:144 read_agents_json()` → `dashboard-next/api/server.py:215` 出 API。
- 這些是**規則層治理欄位**（改動範圍/合併策略/預審），registry schema v2 目前沒有
  → 建議吸收進 registry（claude/ooda kind 適用），agents.json 淘汰。
- AgentInfo 另有 `role_badge`（從 name 猜 emoji）→ 之後可改由 registry `pdca_role` 決定。

## agents.conf 現況（Phase 3 轉檔清單）
- 條目數：rivendell 11（harvest/maintain/tester/doctor/symlink-fix/workflow-retro/janitor/token-snapshot/ssot-drift/disk-monitor/token-analysis）+ news_stock 2 + sales 4 + dashboard 2 + watchdog 1 = **20 有效 + 1 註解（autoresearch）**
- sales 4 隻的 project=sales-assistant → 已宣告 deprecated（memory: sales-assistant-deprecated）→ 轉檔標 `enabled: false`
- extra_args 只有 news_stock 兩隻在用（daily/weekly）— 同 script 不同參數 = 兩個 registry 檔，schema 允許。

## 既有先例可複用
- mission+metric 迴圈：`skills/workflow/autoresearch`（goal/metric/verify loop）
- frontmatter 解析：tester-cron 目前用 grep 淺驗 SKILL.md → registry 驗證要真 YAML 解析（python 端做，bash 只收 exit code）
- 執行紀錄：`bin/sk-exec-lib` `_sk_exec_record_run` — 品質官未來跑起來直接沿用

## 舊 planning 檔處置
- 2026-04-10 的 task_plan/findings/progress 是 workflow-map 頁任務（Phase 1-2 已上線、CRUD deferred），已覆寫；舊內容在 git history。
