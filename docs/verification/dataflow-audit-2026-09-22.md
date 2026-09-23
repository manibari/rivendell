# Rivendell 資料流實查：2026-09-22

## 範圍與書面宣稱

這次按 `qa-dataflow` 查三條主要資料流：平台能力讀取與執行紀錄、知識寫入與助理讀取、助理派工與執行。書面宣稱以 [repository-layout.md](../architecture/repository-layout.md) 及既有 [系統資料流圖](../assets/diagrams/rivendell-system-data-flow.mmd) 為準。部署、監控細項、外部工具的內部流程只列位置，未逐一反證。

## 反證預測（執行前記錄）

1. 若部署技能目錄缺少 `SKILL.md`，`list_skills()` 不會回傳該技能，即使索引 TSV 有該名稱；定義檢查仍以 repo `skills/` 為準。
2. 若角色執行紀錄的 SQLite 無法讀取，角色 API 仍回傳定義，該來源的執行次數顯示為零；不會標示「未知」。
3. 若助理讀取 entity facts 的子程序失敗且 stdout 為空，`build_prompt()` 仍產生 prompt，內容顯示「知識庫目前是空的」。
4. 若 Dispatch 任務未核准或核准後 payload 被改動，`cmd_execute()` 在建立結果檔與呼叫動作前拒絕。
5. 若用隔離目錄執行 `save_note.sh`，筆記與逐字稿寫入該目錄，索引作為衍生檔產生；此路徑不會自動寫入 entity facts。

## 實查結果

| 路徑 | 寫入者與實際儲存 | 讀取者與輸出 | 判讀 |
|---|---|---|---|
| 技能清單 | `skills/*/*/SKILL.md` 由 `sk deploy` 連到 `~/.claude/skills`；TSV 只補分類與摘要 | `platform/capabilities/catalog/skills.py:181-207` 從部署目錄枚舉，`apps/dashboard-api/routes/skills.py:17-34` 回傳清單 | 技能原始檔是 repo；執行時清單依賴部署。TSV 有名稱而部署目錄無 `SKILL.md` 時該項不顯示。另有 Claude 內建技能掃描，見 `skills.py:289-305`。 |
| 角色、工作與 playbook | `platform/capabilities/workflows/definitions/` 與 `playbooks/` JSON | `model.py:21-34,102-148` 組合角色與執行次數；API `routes/workflows.py:14-47`、`routes/skills.py:37-49`；前端讀 `/api/skills/roles` 和 playbook API | 定義是檔案，沒有落在 SQLite。`validate()` 只在工作清單端點呼叫，單筆工作與 playbook 端點直接讀檔。 |
| 執行紀錄 | `bin/sk-exec-lib:751-756` 把新 run 寫進 `dashboard/data/rivendell.db`；互動任務由 `task-tag.sh:28-43` 寫 `~/.claude/session-logs/*/tasks.jsonl` | `roles.py:96-142` 同時讀 `rivendell.db`、舊 `sk-dashboard.db` 與 session tags，合併在角色投影 | **新排程 run 的寫入已整合到一個 SQLite。** `sk-dashboard.db` 是歷史讀取相容路徑；這台機器查無該檔。互動 session 仍在 JSONL，讀取錯誤被略過而統計顯示 0。 |
| 舊 workflow map | `PUT /api/workflow` 直接覆寫 `workflow-map.json`，`routes/workflows.py:52-68,110-114` | `GET /api/workflow` 讀取同檔，`routes/workflows.py:71-107` | 與新 roles/jobs/playbooks 定義獨立；任意 JSON 可寫入，不能視為新流程的編輯入口。 |
| 影音知識 | `save_note.sh:25-30,53-87` 寫 `knowledge/videos/`；它是指向 `knowledge/content/videos/` 的相容連結 | 筆記、逐字稿、衍生 `INDEX.md` 供人工與技能查閱 | 不會自動進入 entity facts。索引重建失敗會被 `save_note.sh:87` 略過，筆記本身仍可成功落地。 |
| Entity facts | `bin/sk-facts-cron:50-85` 只取 `~/.claude/projects/*.jsonl`；透過 `kg.py add` 寫 `~/.claude/knowledge` | `kg.py:205-214` dump active facts；`apps/avatar-gateway/server.py:99-105` 放入 prompt | 這是獨立 Git repo 的資料；Gateway 不檢查 `kg.py` return code，失敗且無 stdout 時顯示「知識庫目前是空的」。影音筆記與 Gateway chat-log 都不是 facts-cron 的直接輸入。 |
| 對話與派工 | Gateway 在 `server.py:225-244` append chat-log，並以背景 `Popen` 啟動 `sk dispatch new`；`sk-dispatch-lib:57-61,120-140` 才真正建立提案與決定 | `/history` 讀 chat-log，`server.py:254-267`；Dispatch 讀 proposal/decisions，`dispatch_lib.py:86-100` | Gateway 啟動後就回覆「提案我開好了」，沒有等待背景程序完成。建立提案可能失敗，使用者仍看到成功字樣。 |
| 動作與結果 | `dispatch_lib.py:411-503` 檢查核准狀態、確認等級與 payload hash；內建動作寫 `results/*.json`。`sk-dispatch-lib:160-224` 的 agent/crm 分支寫 `results/*-agent.md` 後 mark | Dispatch 狀態、結果檔、通知 | 執行 gate 有效；結果格式依任務類型不同。`cmd_mark` 可改狀態，是否已有真實外部動作仍取決於執行器回報。 |

### 隔離反證

| 預測 | 做法 | 結果 |
|---|---|---|
| 部署技能缺 `SKILL.md` 不會進清單 | 暫存目錄放一個只有 TSV 項與空技能目錄，關閉內建技能掃描 | 符合；該技能未出現在清單。原本直接檢查「清單長度為 0」被內建技能干擾，改以該技能名稱是否存在判定。 |
| SQLite 損壞時仍顯示角色，次數為 0 | 暫存目錄放非 SQLite 的 `rivendell.db`，session 目錄留空 | 符合；回傳 11 個角色，總 run 為 0。 |
| KG 子程序失敗仍產生 prompt | 模擬 return code 1、空 stdout | 符合；prompt 含「知識庫目前是空的」。 |
| 未核准與 payload 改動會阻擋動作 | 暫存 dispatch 目錄建立 todo 提案，分別用 pending 與錯誤 hash 呼叫 `cmd_execute()` | 符合；均退出，無 `todos.md` 與 `results/`。 |
| 影音筆記只進隔離 vault | 用暫存路徑呼叫 `save_note.sh` | 符合；產生 1 份 `note.md`、1 份 `transcript.txt`、`INDEX.md`；無 `facts.jsonl`。 |
| 定義檢查涵蓋所有新 workflow API | 模擬 `validate()` 回傳錯誤，同時呼叫清單與單筆端點 | **不符合**；清單拒絕，單筆仍回傳資料。 |
| Gateway 確認提案成功才宣稱已建立 | 模擬派工背景程序啟動但不產出提案 | **不符合**；回覆仍宣稱提案已開，並寫入 chat-log。 |
| 舊 workflow PUT 會更新新定義 | 把寫入位置改為暫存目錄，PUT 任意 JSON，比對新定義檢查 | **不符合**；舊 JSON 接受寫入，新定義結果不變。 |

全部反證只碰暫存檔與 mock；沒有呼叫真實模型、寄信、日曆、CRM 或寫入現有知識庫、派工目錄。讀取端與隔離函式測試不能證明常駐服務的部署狀態；本報告描述目前程式碼路徑。

圖面以 Chrome 截成 1600×900 PNG 並目視檢查；`dataflow-stores-actual` 是另附的 Mermaid 儲存細節圖。`sk check workflows` 通過，回報 11 個角色、44 個工作、4 個 playbook、125 個本地技能。`git diff --check` 與新增文件的相對連結檢查通過。HTML 圖的機械檢查腳本因環境沒有 Playwright 而無法執行；圖面只宣稱完成截圖與目視檢查。

## 關卡與落差

| 關卡 | 目前強度 | 要處理的落差 |
|---|---|---|
| `cmd_execute()` 核准、確認等級、payload hash | 有效；隔離反證擋下兩種不合法狀態 | 保留，並把各任務型別的結果格式明確定義。 |
| 工作定義 `validate()` | 部分；清單端點會擋，單筆與 playbook 端點沒有同一個 gate | 共用一次載入與驗證結果，讓所有新 API 同樣回報定義錯誤。 |
| 角色執行紀錄 | 觀測，不是 gate；2026-09-23 起回傳 `ok / empty / unavailable` | 已處理，見下方「2026-09-23 平台執行證據」。 |
| Entity facts 讀取 | 非必要；錯誤被當成空知識庫 | 讓 Gateway 區分空資料和讀取失敗。 |
| 提案建立確認 | 無；背景啟動後即宣稱成功 | 取得提案 ID 並驗證落地後再回覆使用者。 |
| 舊 workflow PUT | 只寫舊檔；不驗證新定義 | 在 UI 與 API 說清楚相容用途，或完成遷移後收斂到新定義編輯流程。 |

## 整合方向：按領域統一契約

1. **平台執行證據。** 以現有 `rivendell.db` 為唯一新 run 寫入點。定義 `execution_event` 的 `source_id` 與唯一鍵，把互動 `tasks.jsonl` 做可重跑匯入；歷史 `sk-dashboard.db` 只做一次核對與回填。角色與監控改讀同一個查詢服務，回傳 `ok / empty / unavailable`，不把錯誤折成 0。切換前比較各來源的筆數、job/stage 分布與最近時間。
2. **知識庫介面。** `knowledge` 保有自己的筆記 vault 與 entity facts repo。提供統一的寫入、查詢、來源欄位與健康狀態；從筆記提取 entity fact 應是可追溯的明確動作，包含來源、去重與覆核。助理讀取這個介面，並把不可用狀態呈現給使用者。
3. **助理派工。** Gateway 以可回傳 ID 的提交介面建立提案，收到持久化確認後才宣稱成功。Dispatch 繼續擁有提案、核准與結果；執行前 gate 保留。用一致的結果契約描述 JSON 與 agent Markdown 兩種結果檔。
4. **跨領域界線。** 平台、知識、助理以 API 或事件交換 ID 與狀態，不共同寫另一領域的資料檔。這是邏輯整合；實體儲存依領域維持分離。

## 2026-09-23 平台執行證據（整合方向 1 已實作）

- **儲存。** `rivendell.db` 新增 `execution_event`，唯一鍵 `(source, source_id)`：`agent_runs` 列以 `id` 為 `source_id` 並記錄匯入 cursor；`tasks.jsonl` 每行以「repo slug + 原始行」的 SHA-256 為 `source_id`，整檔重讀也不會重複。兩個寫入者（`sk-exec-lib`、`task-tag.sh`）不變。
- **查詢服務。** `platform/monitoring/evidence/execution_evidence.py`（API 經 `lib/evidence.py` 連結載入）的 `job_summary()` 先同步再只讀 `execution_event`，回傳 `status`、各來源狀態與筆數、每個工作的次數。任一來源不可讀即為 `unavailable`；壞行列在 `bad_lines`。
- **讀取端。** `roles._telemetry()` 與 `project_roles()` 改用此服務，回應多一個 `evidence` 欄位；不再讀已退役的 `sk-dashboard.db`。角色頁在 `unavailable` 時顯示「執行紀錄無法讀取」，不顯示 0。監控頁的單一 agent run 列表原本就以 `StoreUnreadable` 區分，未改動。
- **切換前核對。** `execution_evidence.py reconcile sk-dashboard.db.retired-2026-09-18`：舊庫 233 筆、最新 2026-09-18T03:30:04；新庫 264 筆、最新 2026-09-23T03:47:36；以 `agent_name + started_at` 比對，舊庫缺漏 0 筆。兩邊都沒有帶 job/stage 的 run，本機也沒有 `tasks.jsonl`，所以角色頁的 0 是 `empty`，不是讀取失敗。
- **隔離反證**（`apps/dashboard-api/tests/test_execution_evidence.py`，全在暫存目錄）：空庫回 `empty`；兩來源合併且重跑兩次結果相同、第二次匯入 0 筆；cursor 之後的新 run 會被匯入；非 SQLite 檔回 `unavailable`；無讀取權的 `tasks.jsonl` 使來源與整體為 `unavailable`；壞行被計入 `bad_lines`；reconcile 找出舊庫獨有列；角色投影在庫損壞時帶出 `unavailable`。後端 14 個測試通過，前端 `tsc`、`eslint` 通過。本機沒有 ruff，lint 未在本機驗證。
- **副作用。** 角色 API 每次讀取會對真實 `rivendell.db` 執行冪等匯入；既有 `test_workflows` 因此也會建立兩張新表。

目標圖是 [dataflow-stores-target-2026-09.html](dataflow-stores-target-2026-09.html)；它描述待實作契約，不代表現況。現況以 [功能關係圖](dataflow-functions-2026-09.html) 及 [實際儲存圖](dataflow-stores-actual-2026-09.mmd) 為準。
