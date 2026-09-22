---
feature: repository-layout
date: 2026-09-21
scale: light
triggers: []
requirement: 本次 DDD 資料夾結構討論
mockup: 無 UI
status: in-progress
---

# Rivendell 功能邊界與目標資料夾

> 2026-09-22 更新：技能目錄與技能組成的工作流程將整合於 `platform/capabilities/{catalog,workflows}`。本文件原有 `skill_catalog/`、`workflows/` 樹為前一階段目標；後續細節以 [整合計畫](../plans/2026-09-22-capabilities-workflows-consolidation.md) 為準。

> 一句話：平台、個人助理、知識庫各有責任；平台內的部署、版本和監控各自成模組；能力包及工具按擁有者管理。
> 依 2026-09-21 程式碼實查與本次討論。這是目標結構；已搬移的路徑與相容入口見 [目前目錄](../architecture/repository-layout.md)。本輪無 schema 或 HTTP 契約變更，採 Light。

## §1 Scope

本次定義功能、工具、資料的歸屬與目標目錄。應用、設定與部分工具已搬移；服務與排程仍由舊入口相容。dispatch 與 generated reports 的資料檔保留原位，由各自寫入者在後續遷移。

現況問題：根目錄混放應用、領域資料、部署工具、產出及工作筆記；bin/sk 同時實作技能、Agent、派工、部署與監控；dashboard-next/api/server.py 同時提供多個功能的 API；dashboard/lib 與 scripts 也按技術形式混放不同責任。

## §2 資料模型

Light 檔略。第一階段維持 agents/registry、dispatch、reports、knowledge/videos、~/.claude/knowledge 和 dashboard/data/rivendell.db 的現有落點與寫入者。觀測資料層另見 2026-09-18-observability-data-layer-sd.md。

## §3 模組與職責邊界

平台功能是產品能力；模組是規則與資料的擁有者。部署與版本都是平台功能，也分別是模組。Dashboard、API 和 CLI 是入口。

| 模組 | 負責 | 不負責 | 現況來源 |
|---|---|---|---|
| 平台／技能目錄 | 能力包註冊、路由、部署、Harvest、使用情況 | 各 skill 的業務流程與產出知識 | skills、bin/sk、dashboard/lib/skills.py、catalog 腳本 |
| 平台／Agent fleet | registry、排程、啟停、執行 | 助理核准、Token 分析 | agents、bin/sk-*、dashboard/lib/agents.py、registry.py |
| 平台／專案管理 | 專案 metadata、mission、Git 狀態 | 服務部署、skill 編輯 | dashboard/lib/projects.py、bin/sk-projects-sync |
| 平台／部署 | profile、環境、服務部署與更新、port 宣告及盤點 | 版本規劃、Agent 執行結果 | profiles/profiles.conf、Compose、Dockerfile、bin/sk 部署命令、/api/ports |
| 平台／版本與發佈 | VERSION、Changelog、Roadmap、發佈規則 | 服務啟停與更新 | 根層三份文件；版本 API／面板尚未實作 |
| 平台／監控 | Agent、磁碟、SSOT、探針、錯誤、Git、Token 的讀取視圖與告警 | 改寫受監控模組的宣告 | /api/health、dashboard/lib/db.py、tokens.py、各 sk check |
| 平台／工作流程 | 平台工作流程定義與呈現 | skill 本體、助理提案 | data/workflow-map.json、/api/workflow |
| 個人助理 | 對話、persona、通道、提案、核准與動作 | 擁有知識庫資料或 skill 來源 | gateway、dispatch、郵件／日曆腳本 |
| 知識庫 | 內容摘要、實體事實、寫入驗證、索引與查詢 | 對話人格、派工核准、部署 | knowledge/videos、scripts/kg.py、~/.claude/knowledge |

監控是跨模組讀取面。Port 狀態可顯示於監控畫面，port 宣告仍由部署管理；Agent 健康頁讀 Agent 狀態，不直接改 registry。個人助理可依賴知識庫，知識庫不反向依賴助理。

### §3.1 能力包、工具與知識

| 物件 | 定義與放置 | 現有例子 |
|---|---|---|
| 能力包 | 任務觸發、流程和驗收；canonical source 為 skills/<分類>/<名稱>/SKILL.md | video-transcript、office-pptx |
| 專用工具 | 跟使用它的 skill 放在一起 | office-pptx/scripts/html2pptx.js |
| 領域共用工具 | 跟明確的領域主人放；遷移期保留舊入口 | knowledge/_shared 的 media_fetch.sh、save_note.sh |
| 平台工具 | 所屬平台模組實作，bin 保留穩定命令入口 | sk deploy、sk_exec、sk bootstrap |
| 外部依賴 | 由使用的能力宣告並檢查安裝狀態 | yt-dlp、FFmpeg、whisper.cpp、Playwright |
| 知識 | 完成任務後保存的內容或事實，由知識庫管理 | knowledge/videos、~/.claude/knowledge |

2026-09-21 本機只確認可發現性，未做功能測試：yt-dlp、ffmpeg、ffprobe、whisper-cli、claude、codex、Docker、Git、gh、Cloudflared 可在 PATH 找到；mlx_whisper 在預設 Python 及兩個應用 venv 均未找到；Playwright、PPTXGenJS、Sharp 有根層 package.json 宣告，但當時根層 Node 模組未安裝。文件提到工具不等於本機已可執行。

### §3.2 現況與目標目錄

現況根層有 agents、bin、dashboard、dashboard-next、data、dispatch、gateway、knowledge、profiles、reports、scripts、skills、dockerfiles、mockups、docs，以及 VERSION、CHANGELOG、ROADMAP、deploy.sh、Compose 等檔。目標按責任收斂為：

```text
rivendell/
├── platform/
│   ├── capabilities/        技能目錄與工作流程；細節見 2026-09-22 整合計畫
│   ├── agent_fleet/         registry、排程、執行
│   ├── projects/            專案資料
│   ├── deployment/          profiles、環境、服務、ports、Docker
│   ├── release/             version、changelog、roadmap
│   ├── monitoring/
│   │   ├── agents/          排程與執行健康
│   │   ├── disk/            容量與快照
│   │   ├── data_integrity/  SSOT 與活性探針
│   │   ├── errors/          最近錯誤
│   │   ├── git/             Git 衛生
│   │   └── usage/           Token 與成本
│   └── workflows/           平台工作流程
├── assistant/
│   ├── conversation/        對話規則
│   ├── personas/            persona 設定
│   ├── dispatch/            提案與決策狀態機
│   └── channels/            郵件、日曆等 adapter
├── knowledge/
│   ├── content/             摘要、逐字稿與索引；目前在 videos/
│   ├── entities/            實體事實介面；資料目前在 ~/.claude/knowledge/
│   ├── ingestion/           攝取與整理工具
│   └── retrieval/           查詢介面
├── apps/
│   ├── dashboard-web/
│   ├── dashboard-api/
│   ├── avatar-gateway/
│   └── dashboard-legacy/
├── skills/                  能力包 canonical source，含專用工具
├── bin/                     穩定 CLI／排程入口
├── artifacts/reports/       排程產出
├── docs/                    需求、設計、原型、已完成工作檔
└── README.md · AGENTS.md · package.json 等必要根層入口
```

skills 保留根層，因部署器與 CI 掃描 skills/*/*/SKILL.md；platform/capabilities/catalog 放管理規則，不複製能力包。bin 保留公開命令，實作逐步回到擁有者。沒有兩個獨立領域確實共用的程式，不新建全域 tools 目錄。

### §3.3 根目錄去向

| 現有項目 | 目標歸屬 |
|---|---|
| dashboard-next、dashboard、gateway | apps；dashboard/lib 中的規則依功能抽離 |
| agents | platform/agent_fleet |
| profiles/profiles.conf、data/ports.conf、dockerfiles、Compose、deploy.sh | platform/deployment；公開入口在遷移期保留 |
| VERSION、CHANGELOG.md、ROADMAP.md | platform/release 擁有；根層檔案在相關 consumer 更新前保持 canonical |
| dispatch、profiles/personas、data/persona.conf、data/chat-log | assistant |
| knowledge、scripts/kg.py | knowledge；實體資料仍在 repo 外的獨立 store |
| reports | artifacts/reports；由排程產生者遷移 |
| data/global-hooks.json、routing-tests.json、skill-summaries-zh.tsv | platform/capabilities/catalog |
| data/workflow-map.json | platform/capabilities/workflows（舊 API 相容資料） |
| scripts、bin/sk 的內部實作 | 依命令責任分回各模組；bin 保留薄入口 |
| mockups、根層 task_plan.md、findings.md、progress.md | docs；先處理 skill 對預設路徑的依賴 |

### §3.4 寫入權責

| 落點 | 目前寫入入口 | 目標主人 |
|---|---|---|
| skills/*/*/SKILL.md | skill 作者、建立與 Harvest 流程 | 平台技能目錄 |
| agents/registry/*.md | registry 管理流程 | 平台 Agent fleet |
| dispatch/<id>/decisions.json | scripts/dispatch-lib.py | 個人助理 dispatch |
| knowledge/videos/* | save_note.sh | 知識庫 content |
| ~/.claude/knowledge/*/facts.jsonl | scripts/kg.py | 知識庫 entities |
| dashboard/data/rivendell.db | sk-exec-lib、token snapshot、探針寫入者 | 各資料表所屬模組；共用 DB 檔不是同一聚合 |
| reports/* | 對應排程 agent | 各產生者；互動 session 不手改 |

## §4 介面契約

本輪沒有執行期契約變更。搬移時保持 ./bin/sk 命令、參數與 exit code，skills/*/*/SKILL.md canonical source，Agent registry 生成結果，既有 /api/*、/v1/chat/completions，以及資料庫、派工、報表的讀寫語意。所有 consumer 驗證後才移除舊入口。

## §5 關鍵流程

Light 檔略；此輪沒有執行期流程變更。

## §6 功能關係圖

Light 檔略。依賴方向：apps 與 bin 呼叫平台／助理模組；助理及能力包可呼叫知識庫；知識庫不呼叫助理或平台應用。

## §7 NFR 與反證關卡

Light 檔略。實作前檢查 __file__ 推算 repo root、launchd entry、Docker build context、CI working directory、skill deploy symlink、Node 模組解析和 generated reports 的產生者。逐階段確認資料沒有同時寫到新舊兩處。

## §8 未決事項與順序

| 問題 | 暫定 | 決定者 | 時點 |
|---|---|---|---|
| Streamlit 是否仍有使用者？ | 先列為 legacy app | 專案維護者 | 搬 dashboard 前 |
| VERSION 等根層發佈檔何時搬入 release？ | 先保持 canonical，與版本 gate、文件同批更新 | 專案維護者 | 實作 release 模組時 |
| 工具依賴如何安裝與驗收？ | 按使用能力列 manifest 與 doctor 檢查 | 專案維護者 | 各工具搬移或新增時 |

先對映純目錄與入口，再按模組逐一抽離 dashboard/lib、bin/sk 和 scripts 的邏輯；最後由資料擁有者遷移 dispatch、knowledge、reports 等落點。跨模組搬移時另出 Full 設計與驗收計畫。
