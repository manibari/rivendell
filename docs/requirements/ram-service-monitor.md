# Requirement: RAM Service Monitor

**Feature:** `ram-service-monitor`  
**Status:** approved  
**Date:** 2026-08-18  
**Approved:** 2026-08-18  
**Location:** `dashboard-next` → Sidebar「系統健康」→「記憶體」→ `/health/memory`

## 需求摘要

在 rivendell dashboard 新增一個唯讀的 RAM 監控頁，回答：

> 這台電腦現在是否有記憶體壓力？具體是哪個服務，以及服務底下哪個 process 在使用 RAM？

第一版聚焦「現在」：提供系統總覽、依服務彙總的排名、可展開的 process 明細，以及依證據產生的節省建議。歷史趨勢、告警、遠端主機與直接從 UI 終止 process 不納入 MVP。

## Why now / 問題定義

目前 dashboard 已能查看磁碟容量、排程、錯誤與 port，但 RAM 使用情況仍是盲區。發生記憶體壓力時，使用者必須離開 dashboard，以 Activity Monitor 或多個 CLI 指令查 PID，再自行推斷 PID 屬於哪個 launchd service、Docker container 或開發服務。

單純列出 process 不足以回答問題：例如一個 Next.js 或 agent service 可能衍生多個 child process。需求必須同時提供：

1. 系統是否真的有記憶體壓力；
2. 哪個「服務群組」使用最多 RAM；
3. 該群組內是哪個 PID / process 貢獻最多。

## 目標使用者

Peter — 這台 macOS 電腦與 rivendell 的單人維運者。

## 成功定義

- 使用者在一個頁面、10 秒內找出目前 RAM 使用量最高的服務與主要 process。
- 頁面不會把「無法取得資料」顯示成 0，也不會把無法歸屬的 process 猜成某個服務。
- 自動更新期間，排序、展開狀態與錯誤狀態可理解，不需要重載整頁。

## 資訊架構

- 導覽位置：Sidebar 的「系統健康」群組內。
- 導覽名稱：「記憶體」。
- 路由：`/health/memory`。
- 層級：與「磁碟容量」、「SSOT 漂移」、「排程健康」、「最近錯誤」、「Git 衛生」同層。
- 不新增 Sidebar 頂層入口，也不放在「Port 對應」下。

## 核心定義與決策

### D-1: 「服務」是 process 群組，不等於單一 process

畫面第一層為 service group，第二層為 process。MVP 的歸屬優先序：

1. Docker container / Compose service（若本機可取得 container 與 host PID 對應）；
2. launchd label（至少涵蓋 `com.sk.*`，並將同一服務的 child processes 合併）；
3. 可辨識的 process tree root；
4. 無法可靠判定時歸入「未歸類」，保留原始 command 與 PID。

同一 PID 只能計入一個 service group，避免重複加總。服務名稱屬推導資料，API 必須回傳 `group_source`，讓 UI 能區分 `docker`、`launchd`、`process_tree`、`unclassified`。

### D-2: MVP 排名指標採 RSS，並清楚標示限制

MVP 使用作業系統可由一般使用者取得的 per-process RSS（resident set size）做 process 排名與 service group 加總。RSS 適合回答「目前誰佔得多」，但 shared memory 可能在多個 process 重複計入，因此：

- service 列表的數值標為「Process RSS 合計」；
- 不宣稱所有 service RSS 相加會等於系統「已使用記憶體」；
- 系統壓力與 swap 為獨立指標，不用 RSS 合計反推。

若後續找到穩定、免 root 且成本可接受的 macOS physical footprint 資料源，可另案替換排名指標，不阻擋 MVP。

### D-3: 「監控」第一版是 live snapshot，不是長期時序資料

頁面載入後立即取樣，預設每 5 秒自動更新；使用者可暫停或手動重新整理。API 回傳取樣時間與耗時。MVP 不寫入資料庫或檔案，不保留跨頁面或跨重開機歷史。

### D-4: Docker limit、container usage 與 host VM footprint 必須分開

Docker Desktop 在 macOS 上透過 Linux VM 執行。`docker stats` 顯示的 `x GiB / 39.1 GiB` 中，後者是 VM 可用上限，不是已使用或已快取的 RAM。頁面不得把 limit 畫成 usage，也不得把三種數字混為一談：

- **Configured limit**：Docker VM 最多可使用多少；
- **Container usage**：各 container 目前由 Docker/cgroup 回報的使用量；
- **Host VM footprint**：macOS 觀察到 Docker Virtual Machine process 的實際 footprint/RSS。

若三者不能以同一口徑比較，UI 必須分區並標示資料來源，不計算誤導性的「差額」。

### D-5: 先分類原因，再提出節省方式

「Docker 使用 38GB」不是單一問題，處置取決於記憶體的性質。頁面必須先分類，再顯示建議：

| 原因 | 判斷證據 | 建議處置 | 風險 |
|---|---|---|---|
| 單一 container workload 實際使用高 | container usage 排名與 process 明細 | 停止非必要 container、調低 service memory limit，或調整該服務 workload | 中；可能中斷服務或 OOM |
| Linux page cache / 可回收 cache | VM/container 指標能可靠取得 reclaimable cache | 顯示可回收估計；優先等待壓力下自動回收，不建議手動 drop cache | 低；cache 通常會自動回收 |
| Docker VM 保留記憶體未還給 macOS | container usage 已下降但 host VM footprint 長時間維持高 | 建議重啟 Docker Desktop，並說明會中斷所有 containers | 高；全數服務中斷 |
| Configured limit 過高但 actual usage 低 | limit 高、usage 與 pressure 正常 | 可選擇調低 Docker Desktop memory limit；明講這是預防上限，不是立即回收量 | 中；過低可能造成 OOM |
| 不明或資料口徑矛盾 | container total、VM footprint、pressure 無法合理解釋 | 顯示「無法安全判定」，提供診斷資料，不給一鍵操作 | 無直接變更 |

節省量只能在有可靠證據時顯示，並標為「estimated reclaimable」。不得以 `limit - usage` 當作可釋放 RAM。

## User Stories

### US-1: 查看系統記憶體狀態

**As a** 單人維運者  
**I want to** 看到實體記憶體、使用量、可用量、swap 與 memory pressure  
**So that** 我能先判斷目前是否真的有 RAM 壓力，而不只看到一個很大的 process

**Acceptance Criteria:**

- [ ] Given API 可取得系統資料，when 頁面載入，then 顯示 total、used、available、used percentage、swap used/total 與 pressure status
- [ ] Given 系統 pressure 正常，when RAM cache 使用偏高但仍可回收，then UI 不僅因 used percentage 高就誤標為 critical
- [ ] Given pressure 或 swap 資料無法取得，when 其他資料仍可用，then 個別欄位顯示「無法取得」，服務排名仍正常顯示
- [ ] Given 整個取樣失敗，when 頁面載入，then 顯示錯誤原因與最後嘗試時間，不顯示 0 GB

### US-1A: 從系統健康導覽進入

**As a** dashboard 使用者  
**I want to** 從 Sidebar 的「系統健康」找到記憶體功能  
**So that** RAM 診斷與其他本機健康檢查集中在同一處

**Acceptance Criteria:**

- [ ] Given Sidebar 已載入，when 展開「系統健康」，then 顯示「記憶體」項目，且與其他健康功能同層
- [ ] Given 使用者點擊「記憶體」，when 導覽完成，then 進入 `/health/memory`
- [ ] Given 使用者位於 `/health/memory`，when 查看 Sidebar，then「系統健康」保持展開且「記憶體」顯示 active state
- [ ] Given API 暫時不可用，when 使用者點擊 Sidebar 項目，then 仍能進入記憶體頁並看到頁面錯誤狀態，不因導覽失敗而留在原頁

### US-2: 依服務找出 RAM 使用大戶

**As a** 單人維運者  
**I want to** 依 RAM 使用量排序查看服務  
**So that** 我能直接知道是哪個服務造成負擔，不必手動把 PID 拼回服務

**Acceptance Criteria:**

- [ ] Given 目前有多個服務在執行，when 取樣完成，then service groups 依 RSS bytes 由高到低排序
- [ ] Given 一個 service 有 parent 與多個 child processes，when 顯示 service RSS，then 所有不重複的成員 PID 都納入一次
- [ ] Given process 可可靠對應至 launchd 或 Docker，when 顯示，then 列出 service name、來源、RSS、佔實體 RAM 百分比、process count 與最大 process
- [ ] Given process 無法可靠歸屬，when 顯示，then 放入「未歸類」或獨立 process-tree group，不猜測為已知服務
- [ ] Given process 在取樣途中結束，when 收集器讀不到其後續欄位，then 跳過該 PID 或標示已結束，整次取樣不失敗
- [ ] Given service RSS 相加與 system used 不一致，when 顯示總覽，then UI 附註 shared memory / kernel / cache 等原因，不把差額標為錯誤

### US-3: 展開服務查看 process 明細

**As a** 單人維運者  
**I want to** 展開某個服務查看其 process 與 PID  
**So that** 我能判斷是主程式、worker、child process 或意外殘留程序在吃 RAM

**Acceptance Criteria:**

- [ ] Given service group 有一個以上 process，when 點擊該列，then 顯示每個 process 的 PID、PPID、名稱、RSS、佔比與經過遮罩的 command
- [ ] Given process command 含 token、password、secret、authorization 或敏感 query value，when API 回傳資料，then 值在 server 端被遮罩，原始 secret 不送到 browser
- [ ] Given process 數量很多，when 展開，then 預設依 RSS 降冪顯示且不改變 service group 的排序
- [ ] Given 自動更新時該 service 仍存在，when 新 snapshot 到達，then 已展開狀態保留且數值更新
- [ ] Given 自動更新時該 service 已結束，when 新 snapshot 到達，then 該列移除並以非阻斷提示說明資料已更新，不造成頁面錯誤

### US-4: 持續更新並辨識資料新鮮度

**As a** 單人維運者  
**I want to** 讓頁面自動更新，也能暫停觀察某次 snapshot  
**So that** 我可以觀察 RAM 變化，同時避免閱讀時列表一直跳動

**Acceptance Criteria:**

- [ ] Given 頁面保持開啟且 auto refresh 啟用，when 每 5 秒到期，then 背景取得新 snapshot 並更新畫面，不做整頁 reload
- [ ] Given 前一次請求尚未完成，when 下一個更新週期到達，then 不啟動重疊請求
- [ ] Given 使用者按下暫停，when 更新週期到達，then 數值與排序維持不變，並清楚顯示「已暫停」及 snapshot 時間
- [ ] Given auto refresh 失敗但已有舊 snapshot，when 顯示錯誤，then 保留舊資料並標示 stale，不清空列表
- [ ] Given browser tab 不可見，when 自動更新，then 可暫停或降頻；回到頁面後立即重新取樣

### US-5: 快速縮小排查範圍

**As a** 單人維運者  
**I want to** 搜尋服務/process 並控制顯示範圍  
**So that** 在 process 很多時仍能快速找到目標

**Acceptance Criteria:**

- [ ] Given 使用者輸入 service name、process name 或 PID，when 篩選，then 只顯示符合的 service groups，並保留匹配 process 的上下文
- [ ] Given 使用者選擇 Top 10、Top 25 或全部，when 切換，then 列表依目前 snapshot 的 RSS 排名套用限制
- [ ] Given 搜尋無結果，when 顯示空狀態，then 說明是篩選無匹配，不誤導為本機沒有 process

### US-6: 看懂 Docker Desktop 的記憶體

**As a** 使用 Docker Desktop 的開發者  
**I want to** 分辨 Docker 的上限、容器用量與 VM 在 macOS 上的 footprint  
**So that** 我不會把 `39.1 GiB` 上限誤認為 Docker 已吃掉 39.1 GiB

**Acceptance Criteria:**

- [ ] Given `docker stats` 回報 `5.6 GiB / 39.1 GiB`，when 顯示，then UI 分別標為「容器使用 5.6 GiB」與「Docker VM 上限 39.1 GiB」，不稱 39.1 GiB 為 usage/cache
- [ ] Given 多個 containers 在執行，when 顯示 Docker 明細，then 列出每個 container 的 memory usage、limit 與 percentage，並提供 container usage 合計
- [ ] Given macOS 可取得 Docker VM process footprint，when 顯示，then 另列「Host 上 Docker VM」數值並註明其口徑可能與 container cgroup usage 不同
- [ ] Given Docker daemon 無法連線，when 取樣，then Docker 區塊顯示 unavailable，其他 host processes 仍可正常顯示
- [ ] Given Docker Desktop limit 很高但 actual usage 與 memory pressure 正常，when 顯示狀態，then 不標示 RAM 告警

### US-7: 獲得可執行的節省建議

**As a** 單人維運者  
**I want to** 在 Docker 實際使用大量 RAM 時看到依原因排序的處置建議  
**So that** 我知道如何釋放記憶體，以及每個動作會中斷什麼

**Acceptance Criteria:**

- [ ] Given Docker actual usage 達到 38 GiB，when 開啟頁面，then 顯示主要 containers 的使用量、合計、系統 pressure，以及它們對 38 GiB 的貢獻
- [ ] Given Top containers 已解釋大部分用量，when 顯示建議，then 優先列出可停止的 container 與其預估可釋放量，而非先建議重啟整個 Docker
- [ ] Given container 設有 memory limit，when 用量接近 limit，then 顯示 OOM 風險；建議調低 limit 時同時說明可能造成服務被 kill
- [ ] Given actual usage 已下降但 Docker VM footprint 未下降，when 狀態持續超過可設定觀察期，then 建議重啟 Docker Desktop並標示「會中斷所有 containers」
- [ ] Given 數值主要是 reclaimable cache 且 pressure 正常，when 顯示建議，then 說明系統可自動回收，不把 cache 全部算成必須立即處理的浪費
- [ ] Given 系統 memory pressure 為 warning/critical，when 顯示，then 建議依「低風險且可釋放最多」排序，並把緊急程度與一般優化區分
- [ ] Given 無法可靠估算可回收量，when 顯示建議，then 使用「未知」而不是杜撰 GB 數字
- [ ] Given 任一建議可能中斷服務或造成 OOM，when 顯示，then 必須列出受影響的 container/service，且 MVP 不自動執行

## Scope Boundary

| In Scope (MVP) | Out of Scope |
|---|---|
| macOS 本機即時 RAM snapshot | Windows、Linux 或遠端主機 |
| Sidebar「系統健康」內的「記憶體」入口 | 新增 Sidebar 頂層入口 |
| 系統 memory / swap / pressure 摘要 | 長期歷史、趨勢圖、資料庫儲存 |
| 依 launchd、Docker、process tree 分組 | 保證辨識每個第三方 app 的產品名稱 |
| Docker VM limit、container usage、host VM footprint 分開呈現 | 將 Docker limit 當作實際 RAM 使用量 |
| Service RSS 排名與 process 明細 | PSS/USS/physical footprint 的跨平台精準歸因 |
| 5 秒 auto refresh、暫停、手動 refresh | 背景常駐採樣與通知告警 |
| 搜尋與 Top N 顯示 | 自訂 dashboard / 報表匯出 |
| 唯讀診斷與風險分級處置建議 | 從 UI kill、restart、調整限額或 throttle process/service |
| Server-side command secret redaction | 顯示完整 environment variables 或開啟檔案內容 |

## 建議資料契約

`GET /api/health/memory` 回傳單次 snapshot：

```json
{
  "sampled_at": "2026-08-18T06:00:00+08:00",
  "duration_ms": 84,
  "system": {
    "total_bytes": 34359738368,
    "used_bytes": 25769803776,
    "available_bytes": 8589934592,
    "used_percent": 75.0,
    "swap_total_bytes": 4294967296,
    "swap_used_bytes": 1073741824,
    "pressure": "normal"
  },
  "services": [
    {
      "id": "launchd:com.sk.dashboard.web",
      "name": "com.sk.dashboard.web",
      "group_source": "launchd",
      "rss_bytes": 734003200,
      "percent_of_physical_ram": 2.14,
      "process_count": 3,
      "processes": [
        {
          "pid": 1234,
          "ppid": 1,
          "name": "node",
          "rss_bytes": 524288000,
          "command": "next-server"
        }
      ]
    }
  ],
  "warnings": []
}
```

規則：

- 所有容量以 integer bytes 傳輸，由前端統一格式化。
- `sampled_at` 必須含 timezone。
- service `id` 在 process 未重啟時保持穩定，供 UI 保存展開狀態。
- `pressure` 至少支援 `normal | warning | critical | unavailable`；判定方式在實作計畫中以 macOS 可用資料驗證，不在 UI 端自行猜測。
- 部分資料源失敗時回傳可用資料並附 `warnings`；完全無法取樣才回傳非 2xx。

## 非功能需求

- **效能：** 在一般開發機 process 數量下，API p95 < 1 秒；前端更新不造成可感知 freeze。
- **採樣成本：** dashboard 自身的持續採樣平均 CPU < 1%，不得為監控 RAM 而造成顯著額外負擔。
- **安全：** 不要求 root；不回傳 environment variables；command line 在 server side 遮罩常見 secret pattern。
- **正確性：** 每個 PID 最多歸入一個 group；bytes 與 percentage 使用同一 snapshot；資料源失敗不得靜默轉成 0。
- **相容性：** 第一版明確只支援目前 dashboard 所在的 macOS host，並在不支援的平台回傳可辨識錯誤。
- **可測試性：** 分組、去重、secret redaction、排序及 partial failure 必須能以 fixture 測試，不依賴測試機當下的真實 process。
- **可觀測性：** API 回傳 sample duration 與 warnings；server log 不記錄未遮罩 command。

## 驗證場景

實作完成後至少驗證：

1. 啟動一個可控制的高記憶體 test process，確認其 service/process 排名上升，結束後消失。
2. 一個 parent 衍生兩個 children，確認三個 PID 只加總一次。
3. dashboard 的 launchd api/web 能分成正確 service group。
4. 若 Docker 正在執行，至少一個 container 的 host processes 能歸入正確 container/service；Docker 不可用時其餘資料仍可顯示。
5. command 含假的 `--token=secret-value`，browser payload 不含 `secret-value`。
6. 模擬取樣 command timeout、單一 PID 消失與部分資料源失敗，確認 UI 不顯示假 0 或白畫面。

## 已知風險與待確認

- macOS 對「app / service 實際佔用」存在 shared memory 與 compressed memory 歸因限制；MVP 的 RSS 是診斷排名，不是帳務級加總。
- Docker Desktop 在 macOS 上可能將 container 記憶體集中於 VM process；能否可靠拆到每個 container 需在 implementation spike 驗證。若不可行，MVP 必須將 Docker Desktop VM 顯示為一個 service，不能虛構 container 級數值。
- launchd label 到完整 child process tree 的映射方式需實測，尤其 service 重啟與 orphan process 情境。
- 本需求假設核心痛點是「當下找出 RAM 大戶」。若真正需求是追查數小時後才發生的 memory leak，下一版應優先加入歷史採樣，而不是先做更多即時 UI。

## 後續流程

Requirement 核准後：

1. `/user-flow`：定義 loading、live、paused、stale、partial failure 與 drill-down flow。
2. 技術 spike：驗證 macOS RSS / pressure、launchd tree 與 Docker Desktop 可取得粒度。
3. wireframe / mockup：依 `dashboard-next/DESIGN.md` 設計系統健康頁。
4. implementation plan + engineering review。
