# SYSTEM-MONITOR-MEMORY：在系統監控加入 RAM

**狀態：已完成** · 開票：2026-09-30 · 完成：2026-09-30

## 老闆原話

「所以系統監控也要同時包含 ram 啊」

## 問題

現有「系統監控」只顯示 CPU、GPU、溫度、功耗與電池。只看 CPU 使用率無法判斷 RAM 壓力、記憶體壓縮或 swap 是否正在增加系統負載。

## 範圍

在既有系統監控頁及其五秒常駐採樣資料中加入 macOS 系統層級記憶體讀數：實體總量、使用量、可用量、壓縮量、swap 使用量與記憶體壓力。頁面呈現即時摘要並沿用既有歷史趨勢。不可讀取的指標須顯示為不可用，不得以 0 代替。

此票不實作既有 RAM 服務監控需求中的 process/service 排名、Docker 分類或節省建議；那些能力另按 `docs/requirements/ram-service-monitor.md` 管理。

## 驗收條件

- [x] 系統監控頁同時呈現 RAM 實體總量、使用／可用量、壓縮、swap 與壓力狀態。
- [x] 記憶體指標由常駐採樣器持續記錄，支援既有歷史查詢及趨勢線。
- [x] 單一指標無法取得時，其餘系統讀數仍可用，且 UI 清楚標示缺資料。
- [x] RAM 採樣沿用既有週期，監控本身不增加額外輪詢程序。

## 驗證

2026-09-30 實測（重啟 collector / api / web 之後）：

- **API**：`GET /api/health/sensors` 的 `memory` 回 `status: ok`，含總量 48 GiB、已用、可用、壓縮、swap（24.9 / 26 GiB）與 `pressure_level: normal`。
- **歷史**：`/api/health/metrics/history?range=15m` 出現 `mem.used_gib`、`mem.available_gib`、`mem.compressed_gib`、`mem.swap_gib`、`mem.available_pct`、`mem.pressure` 六個鍵，collector `running: true`。
- **負向測試**：`sysctl` 失敗時整塊仍為 `ok`，swap 與壓力為 `null`，history 不寫這兩鍵；`vm_stat` 失敗時整塊 `unavailable` 並附原因，history 不寫任何 `mem.*`。兩者都沒有寫成 0。
- **Build**：`tsc --noEmit` 通過；`start-web.sh` 重建後，新程式已在 `.next` bundle 裡；本機 headless Chrome 截圖確認頁面上有四張 RAM 卡片和壓力標示。

實作時修掉的問題：launchd 服務的 PATH 裡沒有 `/usr/sbin`，`sysctl` 讀不到，swap 和壓力在 API 裡是 `null`（直接跑命令列時正常）。已改成用絕對路徑呼叫。

已知限制：`memory_pressure -Q` 的可用率只到整數百分比，所以已用／可用的趨勢線每一格是 0.48 GiB（48 GiB 的 1%），自動縮放後看起來像方波。要更平滑，得改從 `vm_stat` 的分頁數推算；這不在這張票的範圍內。

設計補記：`docs/design/2026-09-18-observability-data-layer-sd.md` §10。
