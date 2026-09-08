# User Flow: RAM Service Monitor

**Feature:** `ram-service-monitor`  
**Status:** draft  
**Date:** 2026-08-18  
**Route:** `/health/memory`  
**Entry:** Sidebar → 系統健康 → 記憶體  
**Source:** `docs/requirements/ram-service-monitor.md`

## Flow 1: 進入頁面並判斷是否有記憶體壓力

```mermaid
flowchart TD
    A[展開 Sidebar 系統健康] -->|點擊記憶體| B[進入 /health/memory]
    B -->|立即請求| C[顯示頁面骨架與載入狀態]
    C -->|API 回應| D{Snapshot 可用程度}
    C -->|API 無回應或非 2xx| E[顯示無法取得記憶體資料與重試]
    E -->|點擊重試| C
    E -->|前往其他功能| Z((離開記憶體頁))

    D -->|完整| F[顯示系統摘要與服務排名]
    D -->|部分可用| G[保留可用資料並標示 unavailable 欄位與 warnings]
    D -->|完全不可用| E

    F -->|讀取 pressure| H{Memory pressure}
    G -->|pressure 可用| H
    G -->|pressure 不可用| I[顯示狀態無法判定但保留服務排名]

    H -->|normal| J[顯示正常狀態與 snapshot 時間]
    H -->|warning| K[顯示警告並引導查看 RAM 大戶]
    H -->|critical| L[顯示嚴重壓力並引導查看節省建議]
    H -->|unavailable| I

    J -->|完成判讀| M((知道目前無明顯壓力))
    K -->|繼續排查| N[進入服務排名]
    L -->|繼續排查| N
    I -->|仍可排查| N
```

## Flow 2: 找出是哪個服務與 process 使用 RAM

```mermaid
flowchart TD
    A[查看依 RSS 排序的服務列表] -->|調整顯示| B{Top N 或搜尋}
    B -->|Top 10 / Top 25 / 全部| C[套用顯示數量]
    B -->|輸入名稱或 PID| D{有匹配結果}
    D -->|有| E[顯示匹配 service 與 process 上下文]
    D -->|無| F[顯示篩選無結果]
    F -->|清除搜尋| A
    C -->|選擇服務| G[展開 service row]
    E -->|選擇服務| G
    A -->|選擇服務| G

    G -->|讀取明細| H[顯示 PID PPID process RSS 佔比及遮罩後 command]
    H -->|檢查來源| I{Service group source}
    I -->|launchd| J[顯示 launchd label 與 process tree]
    I -->|Docker| K[顯示 container 與 Docker 記憶體區塊]
    I -->|process tree| L[顯示推導的 root process]
    I -->|unclassified| M[明標未歸類且不猜測服務名稱]

    K -->|比較口徑| N[分開顯示 container usage VM limit host VM footprint]
    N -->|完成判讀| O((知道 Docker 用量來自哪些 containers))
    J -->|完成判讀| P((知道服務內的 RAM 大戶 process))
    L -->|完成判讀| P
    M -->|完成判讀| P

    H -->|自動更新時 process 消失| Q[更新或移除 row 並顯示非阻斷提示]
    Q -->|返回最新列表| A
```

## Flow 3: 在 Docker 使用量高時取得節省建議

```mermaid
flowchart TD
    A[Docker 實際用量高或 memory pressure 告警] -->|開啟節省建議| B{資料足以分類原因}
    B -->|否| C[顯示無法安全判定與診斷資料]
    C -->|手動重新整理| A
    C -->|不採取動作| Z((保留現況))

    B -->|是| D{主要原因}
    D -->|單一或少數 container workload| E[依可釋放量列出主要 containers]
    D -->|可回收 page cache 且 pressure 正常| F[說明 cache 可由系統自動回收]
    D -->|container usage 已降但 VM footprint 持續高| G[建議重啟 Docker Desktop]
    D -->|只有 configured limit 高| H[說明 limit 不是 usage並建議視需要調低]

    E -->|選擇某 container| I[顯示停止服務或調低 limit 的影響與 OOM 風險]
    I -->|MVP 唯讀| J[提供受影響服務與建議操作但不直接執行]
    G -->|檢視風險| K[標示所有 containers 都會中斷]
    K -->|MVP 唯讀| J
    H -->|檢視風險| L[標示過低可能造成 container OOM]
    L -->|MVP 唯讀| J
    F -->|pressure 維持正常| M((無需立即處理))
    J -->|使用者自行決定| N((取得可執行且有風險說明的建議))
```

## Auto-refresh 與資料新鮮度分支

```mermaid
flowchart TD
    A[頁面已有 snapshot] -->|預設每 5 秒| B{頁面與更新狀態}
    B -->|可見且未暫停| C{前次請求完成}
    B -->|使用者已暫停| D[保留 snapshot 並顯示已暫停與時間]
    B -->|Browser tab 不可見| E[暫停或降低更新頻率]

    C -->|是| F[背景請求新 snapshot]
    C -->|否| G[略過本次週期避免重疊請求]
    G -->|下一週期| B

    F -->|成功| H[更新數值並保留仍存在服務的展開狀態]
    F -->|失敗且有舊資料| I[保留舊資料並標示 stale 與錯誤]
    F -->|失敗且無舊資料| J[顯示完整錯誤狀態與重試]

    D -->|點擊繼續| F
    D -->|點擊手動更新| F
    E -->|回到頁面| F
    I -->|下一週期或手動重試| F
    J -->|點擊重試| F
    H -->|等待下一週期| B
```

## Error & Edge Cases

| 情境 | 頁面行為 | 不可發生 |
|---|---|---|
| Dashboard API 無法連線 | 完整錯誤狀態、顯示最後嘗試時間與重試 | 顯示 0 GB 或空白頁 |
| Docker daemon 無法連線 | Docker 區塊 unavailable；host service 排名維持可用 | 整頁失敗 |
| Memory pressure 指標無法取得 | 該欄位 unavailable；不自行用 used % 猜狀態 | 誤標 normal |
| 單一 PID 在取樣中消失 | 忽略或標示已結束並加入 warning | 整次 snapshot 500 |
| Command 含 secret | API server 先遮罩再回傳 | Secret 曾送達 browser |
| Service 無法可靠歸屬 | 顯示 unclassified / process tree source | 猜成 launchd 或 Docker service |
| RSS 合計與 system used 不一致 | 顯示口徑說明 | 把差額標為 bug 或可回收量 |
| Docker limit 高但 usage 低 | 顯示為設定上限，不告警 | 稱為 Docker 已使用 RAM |
| Snapshot 更新後服務消失 | 移除 row、保留其他展開狀態並提示 | React error 或整表清空 |
| 使用者在閱讀時列表跳動 | 可暫停；展開狀態保持 | 強制每次回到列表頂部 |

## Screen / State Inventory

| # | Screen / State | Purpose | Key Elements |
|---|---|---|---|
| 1 | Sidebar — 系統健康展開 | 進入功能 | 記憶體 nav item、active state |
| 2 | 記憶體 — 初次載入 | 等待第一個 snapshot | Page title、summary skeleton、list skeleton |
| 3 | 記憶體 — 正常 live | 判斷系統狀態與 RAM 大戶 | Pressure、physical RAM、swap、sample time、auto-refresh control、service rank |
| 4 | 記憶體 — warning / critical | 強調需要排查 | Semantic status、主要大戶、節省建議入口 |
| 5 | 記憶體 — service 展開 | 查看 process 明細 | PID、PPID、name、RSS、percentage、redacted command、group source |
| 6 | 記憶體 — Docker 詳情 | 區分 Docker 三種口徑 | Container usage、configured VM limit、host VM footprint、container rank |
| 7 | 記憶體 — 節省建議 | 決定怎麼降低用量 | 原因、證據、estimated reclaimable、風險、受影響服務、唯讀建議 |
| 8 | 記憶體 — paused | 固定 snapshot 供閱讀 | 已暫停標籤、sample time、繼續、手動更新 |
| 9 | 記憶體 — stale | 保留舊資料並說明更新失敗 | 舊資料、stale label、錯誤摘要、重試 |
| 10 | 記憶體 — partial data | 部分資料源失敗仍可診斷 | Available sections、field-level unavailable、warnings |
| 11 | 記憶體 — full error | 沒有可用 snapshot | Error reason、last attempt、retry |
| 12 | 記憶體 — filter empty | 區分無匹配與無 process | Search term、clear-filter action |

## Wireframe Constraints

- 系統摘要與 memory pressure 必須先於 service ranking，先回答「是否有壓力」。
- Docker 的 `usage / limit` 不使用單一進度條暗示 limit 已被配置或保留；label 必須完整。
- 節省建議中的 risk 與 estimated reclaimable 必須同時出現，沒有估算依據時顯示 unknown。
- 頁面更新不得重置搜尋、Top N、pause 或仍存在 service 的展開狀態。
- MVP 所有 remediation controls 都是說明或複製指令入口，不是直接執行按鈕。

