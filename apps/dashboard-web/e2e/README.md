# Dashboard E2E

## 怎麼跑

在 `apps/dashboard-web` 執行：

```sh
npx playwright test
```

測試會執行 `npm run build:e2e` 建置網頁，啟動網頁 `127.0.0.1:3005` 與 API `127.0.0.1:8005`。第一次要先建置網頁。可用 `E2E_WEB_PORT`、`E2E_API_PORT` 改測試埠，但不可使用 3000、8000。

每次首次載入設定時，會複製 `fixtures/seed` 到 `.tmp/run-<時間>-<程序>/`，以 API 的 Python 執行 `lib.db.init_db()`，再新增一筆 `tester` 的 `agent_runs`。Playwright worker 沿用同一個資料夾；重置 fixture 時也會重建 schema 與資料。只保留最新三個執行資料夾。資料表測試也使用 API 的 Python，因為它一定與初始化時使用的直譯器相同，無須依賴系統安裝 `sqlite3` CLI。

## 隔離了什麼

下表的「fixture」表示 `.tmp/run-*` 下的複本；「錄製」表示命令由 `recorders/bin` 攔截、寫入 `recorder.jsonl`；「唯讀」表示仍從工作樹讀取，不會修改原檔。由使用者輸入或專案設定導出的路徑，測試資料必須指向 fixture，否則不應在測試中呼叫該寫入端點。

| 路由檔 | 資料來源、子程序或路徑 | 隔離方式 |
| --- | --- | --- |
| `routes/overview.py` | agent、hook、skill、project、token 用量庫 | `HOME` fixture；token JSONL、專案檔、agent plist 與資料庫皆在 fixture |
| `routes/agents/api.py` | agent plist、執行紀錄 SQLite、專案資料 | plist 與 SQLite fixture；agent 編輯只落在 fixture |
| `routes/agents/api.py` | `launchctl list`、agent stdout 與 artifact 路徑 | `launchctl` 錄製；工作目錄、plist 與 log 由 fixture 提供 |
| `routes/agents/presenter.py` | `Path.home()/Library/Logs/sk-agent` | fixture HOME 的 log 目錄 |
| `routes/projects.py` | `~/.claude/projects.json`、專案 repo 與 git 記錄 | 專案目錄 fixture；git 命令錄製 |
| `routes/collaboration.py` | agent 工作目錄的 `.learnings/ERRORS.md` | 工作目錄由 fixture plist 指向 fixture；唯讀 |
| `routes/skills.py` | `REPO_DIR/docs/skills-by-role.md`、`REPO_DIR/docs/**` | 真實工作樹文件，唯讀 |
| `routes/skills.py` | `Path.home()/.claude/projects`、`Path.home()/.claude/skills` | fixture HOME；讀寫都留在 fixture |
| `routes/skills.py` | skill 摘要、session log、skill 清單 | `RIVENDELL_SKILL_SUMMARIES`、`RIVENDELL_SESSION_LOGS`、`RIVENDELL_SKILLS_DIR` 指向 fixture |
| `routes/workflows.py` | `REPO_DIR` 的 workflow 預設檔 | `WORKFLOW_MAP_FILE` 改指 fixture，可讀寫 |
| `routes/workflows.py` | `Path.home()/.claude/skills` | fixture HOME |
| `routes/workflows.py` | `lib.capabilities` 的角色、工作與 playbook 定義 | 真實工作樹定義，唯讀 |
| `routes/harvest.py` | `REPO_DIR/reports`、`.harvest-decisions.json` | `REPORTS_DIR` 指向 fixture，可讀寫 |
| `routes/harvest.py` | `REPO_DIR` 的 skill 來源、`Path.home()/.claude/skills` | `HARVEST_SKILLS_ROOT` 與 fixture HOME，寫入 fixture |
| `routes/deployment.py` | `lsof` 掃描 TCP 監聽埠 | PATH 優先找到 `lsof` 錄製器，回傳空表頭 |
| `routes/deployment.py` | `Path.home()/projects/ops/monitors.toml`、健康 URL | fixture HOME 無監控清單，因此不連外 |
| `routes/deployment.py` | `tail` 讀監控 log | `tail` 錄製器；fixture 無監控 log |
| `routes/deployment.py` | `docker ps`、`docker inspect` | `docker` 錄製器，inspect 回傳空陣列 |
| `routes/deployment.py` | `Path.home()`、port 設定庫 | fixture HOME；`RIVENDELL_PORTS_CONF` 指向 fixture |
| `routes/deployment.py` | `__file__` 推導的 `docker-compose.yml` | `COMPOSE_FILE` 指向 fixture；缺檔時回傳空服務 |
| `routes/monitoring/overview.py` | `__file__` 推導的 repo、`sk check` 子程序 | `SK_CHECK_COMMAND` 指向錄製器；repo 僅作 cwd |
| `routes/monitoring/disk.py` | `__file__` 推導的磁碟快照路徑與命令 | `DISK_TREE_FILE` 指向 fixture；`DISK_SNAPSHOT_COMMAND` 指向錄製器 |
| `routes/monitoring/git.py` | `__file__` 推導的 repo 父層、`git` 子程序 | `GIT_HEALTH_ROOT` 指向 fixture projects；`git` 錄製 |
| `routes/monitoring/issues.py` | `REPO_DIR.parent` 的專案 `.env.example` | `ISSUES_PROJECTS_DIR` 指向 fixture projects，唯讀 |
| `routes/monitoring/issues.py` | `REPO_DIR/skills`、`Path.home()/.claude/skills` | 真實 skill 來源唯讀；部署目標為 fixture HOME |
| `routes/monitoring/issues.py` | agent 工作目錄的 `.learnings/ERRORS.md` | 工作目錄來自 fixture，唯讀 |
| `routes/monitoring/errors.py` | `__file__` 推導的 `reports` | `REPORTS_DIR` 指向 fixture，唯讀 |
| `routes/monitoring/token_watch.py` | `REPO_DIR/reports` | `REPORTS_DIR` 指向 fixture，唯讀 |
| `routes/monitoring/usage.py` | token JSONL 與 token SQLite | fixture HOME 與執行資料庫，唯讀 |
| `routes/monitoring/usage_quota.py` | 額度快取與帳號資料 | fixture HOME，唯讀 |
| `routes/monitoring/usage_timeline.py` | token 時序資料庫與 JSONL | fixture HOME，唯讀 |
| `routes/monitoring/sensors.py` | 系統感測器與歷史資料庫 | 感測器為即時系統讀取；歷史資料庫使用 fixture HOME；此頁不納入 smoke |
| `routes/agents/api.py` | 使用者提交的檔案路徑 | 只以 fixture 路徑測試；檔案操作維持在 fixture |

路由間接使用的 legacy 模組資料庫由 `RIVENDELL_LEGACY_DB_PATH`、`RIVENDELL_DB_PATH`、`RIVENDELL_DB_DIR` 指向同一執行資料夾。`routes/monitoring/sensors.py` 的即時感測器會碰到實機硬體，所以此 E2E 不呼叫它。

## 環境變數

「預設」是未設值時的路徑或埠；`—` 代表正式 API 未定義此變數，僅供測試使用。

| 變數 | 預設 | 讀取檔案 |
| --- | --- | --- |
| `E2E_WEB_PORT` | `3005` | `playwright.config.ts` |
| `E2E_API_PORT` | `8005` | `playwright.config.ts` |
| `DASHBOARD_API_PYTHON` | `apps/dashboard-api/.venv/bin/python` | `e2e/support/store.ts` |
| `E2E_RUN_ROOT` | 首次載入時建立 `.tmp/run-*` | `e2e/support/store.ts` |
| `HOME` | 作業系統家目錄 | `playwright.config.ts` 設為 fixture；各 route 與 legacy 模組的 `Path.home()` 讀取 |
| `PATH` | 父程序 PATH | `playwright.config.ts` 前置 `e2e/recorders/bin` |
| `E2E_RECORDER_LOG` | — | `e2e/recorders/record.py` |
| `NEXT_DIST_DIR` | `.next` | `next.config.ts`；`playwright.config.ts` 設 `.next-e2e` |
| `API_PROXY_TARGET` | `http://127.0.0.1:8000` | `next.config.ts`；`playwright.config.ts` 設測試 API |
| `REPORTS_DIR` | repo 的 `reports/` | `routes/harvest.py`、`routes/monitoring/errors.py`、`token_watch.py` |
| `WORKFLOW_MAP_FILE` | `platform/capabilities/workflows/workflow-map.json` | `routes/workflows.py` |
| `RIVENDELL_LEGACY_DB_PATH` | legacy `data/rivendell.db` | `apps/dashboard-legacy/lib/db.py`、`e2e/support/store.ts` |
| `RIVENDELL_DB_PATH` | `apps/dashboard-legacy/data/rivendell.db` | `platform/monitoring/usage/token_usage.py` |
| `RIVENDELL_DB_DIR` | `apps/dashboard-legacy/data` | `platform/monitoring/evidence/execution_evidence.py`、`platform/monitoring/system/history.py` |
| `RIVENDELL_SESSION_LOGS` | `~/.claude/session-logs` | `platform/monitoring/evidence/execution_evidence.py` |
| `RIVENDELL_SKILLS_DIR` | repo 的 `skills/` | `platform/capabilities/catalog/skills.py`、`platform/capabilities/workflows/model.py` |
| `RIVENDELL_SKILL_SUMMARIES` | `platform/capabilities/catalog/skill-summaries-zh.tsv` | `platform/capabilities/catalog/skills.py` |
| `RIVENDELL_PORTS_CONF` | repo 的 `data/ports.conf` | `platform/deployment/port_registry.py` |
| `HARVEST_SKILLS_ROOT` | repo 根目錄 | `routes/harvest.py` |
| `DISK_TREE_FILE` | repo 的磁碟快照 | `routes/monitoring/disk.py` |
| `DISK_SNAPSHOT_COMMAND` | repo 的 `bin/sk-disk-snapshot` | `routes/monitoring/disk.py` |
| `SK_CHECK_COMMAND` | repo 的 `bin/sk` | `routes/monitoring/overview.py` |
| `GIT_HEALTH_ROOT` | repo 父層 | `routes/monitoring/git.py` |
| `ISSUES_PROJECTS_DIR` | repo 父層 | `routes/monitoring/issues.py` |
| `COMPOSE_FILE` | repo 的 `docker-compose.yml` | `routes/deployment.py` |

## 紀錄器

所有錄製器會把命令名稱、引數、工作目錄與時間寫進 `recorder.jsonl`。輸出刻意保持 API 可解析的形狀。

| `e2e/recorders/bin/` 命令 | 標準輸出 | API 為何需要 |
| --- | --- | --- |
| `launchctl` | 無；無參數的 `list` 輸出 `PID Status Label` 表頭 | agent 清單可解析空服務表；載入與卸載只記錄 |
| `docker` | `inspect` 輸出 `[]`，其他無 | 部署頁可解析空容器清單 |
| `git` | 無 | git 健康檢查不碰真實 repo |
| `lsof` | `COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME` 表頭 | 部署頁可解析空監聽埠表 |
| `tail` | 無 | 監控 log 回傳空內容 |
| `strings` | 無 | 不掃描實際二進位檔 |
| `disk-snapshot` | 無 | 磁碟快照觸發只記錄 |
| `sk-check` | `ssot`、`disk`、`agents` 各輸出固定 JSON；其他輸出 `{}` | 健康頁需要可解析的檢查結果 |

## 怎麼標葉子

新增覆蓋特定控制項的測試時，使用 `@leaf:<module>.<screen>.<control>.<case>` 標籤，例如 `@leaf:agents.list.schedule.edit`。標籤放在測試名稱或鄰近的測試註解；每個標籤對應一個可觀察的操作與結果。對照設計 §3.1 的葉子識別與 §4 檢查 3。

## 規則

- 絕不使用 3000 或 8000 埠。
- 絕不把真實 `HOME` 傳給 E2E API。
- 失敗的測試是 bug 回報；不要為了讓它通過而改測試。
