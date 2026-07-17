# Deployment Inventory — 這台機器上到底在跑什麼

**Status:** draft
**Date:** 2026-07-17
**Feature name:** `deployment-inventory`

## Why now

`/api/overview` 目前回報 `total_projects: 0`、`running_agents: 0`、`enabled_hooks: 0`。三個數字全錯：這台機器上有 7 個 repo、20 個 running 容器，而 dashboard 的 api/web 自己就在跑。

錯的原因不是功能沒做 — metric 和 UI 都已經接好了。錯的原因是 **它讀的那個檔不存在**：`dashboard/lib/projects.py:13` 讀 `~/.claude/projects.json`，那個檔在 Mac → Windows → WSL 搬遷中沒跟上來。檔案一不見，數字就變 0，而且 UI 一臉正常地顯示 0。

這是整份需求的核心教訓：**讀手維護的設定檔，會安靜地說謊。**

## 現況：四個互相矛盾的 SSOT

| SSOT | 宣稱 | 實際 |
|---|---|---|
| `~/.claude/projects.json` | dashboard 唯一真正讀的來源 | **不存在** → 0 |
| `profiles/profiles.conf` | 6 個 project | 部分指向不存在的 repo |
| `agents/agents.conf` | 19 個 agent/service | 6 個指向這台機器沒有的 repo |
| `docker-compose.yml` | 5 個 service | **0 個在跑**，路徑寫死 `/Users/manibari/code` |

而真正在跑的東西，四個檔案沒有一個知道：

```
mops_databases   8/8 up      chimesflow      4/4 up
family-fiscal    4/4 up      iihi            4/4 up
pti-ares         1/1 up      news            0/1 (dead)
agent_company    0/2 (dead)  (standalone)    1/3
rivendell        systemd — 不在任何 compose 裡
```

## 目標使用者

Peter — 單人維運這台 WSL 機器上的全部專案。需要一眼看出「現在有什麼在跑、什麼死了、什麼還沒搬 docker」。

## 核心設計決策

### D-1: 探測，不要讀設定檔

盤點資料一律來自 **self-truthing 來源**：

- `docker ps -a --format '{{.Label "com.docker.compose.project"}}'` — 涵蓋全部 compose project，不只 rivendell 的
- `systemctl --user list-units 'com.sk.*'` — 經由 `svc_list`，不要直接呼叫

**理由**：設定檔會過期而且不會告訴你它過期了（`total_projects: 0` 就是活證據）。`docker ps` 不會 — 它就是現況本身。附帶好處：搬遷進度自動反映，不用另外維護一份對照表。

設定檔仍可用來標示 **「預期存在但沒在跑」**（例如 agents.conf 有、systemd 沒有 → 顯示為 missing）。但預期絕不能冒充現況。

### D-2: rivendell 自己留在 systemd — 這是官方例外，不是待辦

dashboard 不只是觀察者，是**宿主控制器**：

| 行為 | 位置 |
|---|---|
| 寫入 `~/.claude/skills/`（部署 skill） | `api/server.py:1640`, `:1774` |
| `Popen` 啟動 agent | `api/server.py:2095` |
| `launchctl list` | `api/server.py:398` |
| 對各 repo 跑 git | `api/server.py:2154` |
| 對整個 `$HOME` 跑 `du` | `api/server.py:2067` |
| 讀 `~/.claude/settings.json` | `dashboard/lib/hooks.py:12` |

容器化它需要掛載 `~/.claude` 可讀寫 + `docker.sock` + systemd user socket + 全部 repo 目錄。到那個程度容器對宿主已有完全控制權 — **容器邊界買的是隔離；一個工作內容就是控制宿主的工具，從隔離得不到任何東西，卻付出全部代價。**

→ 寫進 `.claude/CLAUDE.md` 作為明確例外，避免未來有人「順手」想搬。

### D-3: `docker-compose.yml` 是負債，需要處置（本輪不做）

它描述 0 個實際在跑的 service，路徑寫死 macOS。它是「應用有四種定義」的元兇之一。處置方式（修 or 刪）另案決定 — 但在 D-1 之下，盤點頁不會讀它，所以它不再阻擋本需求。

## User Stories

### US-1: 看見這台機器上所有在跑的應用

**As a** 單人維運者
**I want to** 在一頁看到所有 compose project 及其容器狀態
**So that** 我不用手動 `docker ps` 再自己心算哪個專案缺了什麼

**Acceptance Criteria:**
- [ ] Given 這台機器有 8 個 compose project，when 開啟盤點頁，then 8 個全部列出，各自顯示 `running/total`
- [ ] Given 某容器不屬於任何 compose project，when 盤點，then 歸類為 `(standalone)` 而非隱藏
- [ ] Given `agent_company` 2 個容器都 exited，when 盤點，then 顯示為 `0/2` 且視覺上標記為 dead，不與 running 混淆
- [ ] Given docker daemon 沒在跑，when 盤點，then 顯示「Docker 無法連線」而非 `0 apps`（**絕不可把「測不到」顯示成「零」— 那正是本需求要修的病**）

### US-2: 看見 rivendell 自己的 systemd 服務

**As a** 單人維運者
**I want to** 在同一頁看到 systemd 管的服務（dashboard api/web + agents）
**So that** docker 與非 docker 的東西不會有一半是隱形的

**Acceptance Criteria:**
- [ ] Given api/web 正在跑，when 盤點，then 顯示 running 與 PID/uptime
- [ ] Given 服務被 `kill -9`，when 幾秒後重新盤點，then 顯示 running 且 PID 已更換（`Restart=always` 生效）
- [ ] Given 這是宿主機而非容器，when 盤點，then 標示為「host service」以區別 D-2 的例外
- [ ] Given 在 macOS 上執行，when 盤點，then 經由 `svc_list` 取得 launchd 資料，不寫死平台判斷

### US-3: 看見「該在跑但沒在跑」的東西

**As a** 單人維運者
**I want to** 看出設定檔宣稱存在、但實際不存在的服務
**So that** 我能發現搬遷遺漏，而不是被一個漂亮的綠色畫面騙過去

**Acceptance Criteria:**
- [ ] Given `agents.conf` 有 6 個 agent 指向這台機器沒有的 repo，when 盤點，then 標示為 `missing: repo not found` 並附上預期路徑
- [ ] Given 預期與現況有落差，when 顯示，then 兩者視覺上分離 — 預期絕不可冒充現況
- [ ] Given `~/.claude/projects.json` 不存在，when 盤點，then 明講「SSOT 檔案不存在」，而非顯示 0

## Scope

| In Scope | Out of Scope |
|---|---|
| 唯讀盤點頁（docker + systemd + 落差） | 從 UI 啟停服務 |
| 經由 `docker ps` / `svc_list` 探測 | 修 `docker-compose.yml`（D-3，另案） |
| 標示 missing / dead | 真的把服務搬進 docker |
| 修正 `/api/overview` 那三個假數字 | 重建 `~/.claude/projects.json` |
| 把 D-2 例外寫進 CLAUDE.md | 容器化 dashboard |
| | `sk-watchdog` 移植（仍是 launchd-only） |

## 已知風險

- **`docker ps` 需要 docker group 權限**：dashboard 以宿主使用者身分跑，目前可存取。若日後改以他人身分執行需重新評估。
- **`svc_list` 目前只認 `com.sk.*`**：非 sk 的宿主服務不會出現。本輪可接受（rivendell 只管自己的）。
- **盤點頁本身會變成第 5 個「應用」定義**：D-1 靠探測降低此風險，但仍需在頁面上明講資料來源，否則又是一個沒人信的數字。

## 相關

- WSL port 進度與 `svc_generate_raw` / keepalive 修正 — 見 memory `rivendell-wsl-port`
- `sk check ssot` 已在做 agents.conf ↔ projects.json 的落差比對，US-3 應盡量重用而非另寫一套
