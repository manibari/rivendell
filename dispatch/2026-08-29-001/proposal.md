# Dispatch 2026-08-29-001

**指令/事件**：幫我約光泉的窗口下週三下午開會討論 BI 看板改版

**理解**：與客戶光泉的窗口敲定 2026-09-02（下週三）下午的會議，主題為 kuangchuan-bi 看板改版討論；屬客戶會議，交接 CRM 處理並由人工確認。

## ❓ 待釐清（sk dispatch answer）

- 下午的具體時段與時長（例如 14:00–15:00）？
- 會議形式：線上（附連結）或實體（地點）？
- 光泉窗口的姓名與聯絡方式，若 CRM 內無現成資料請提供

## 任務

### t1 — 交接 CRM：安排與光泉窗口的 BI 看板改版會議（2026-09-02 下午）  `crm` `external` `pending`
- 依據：依 kuangchuan-001，光泉為合作客戶；客戶會議屬業務行為，依規則一律以 crm 型交接（Rightek-CRM 目前 unreachable，仍以此型留存待執行），不得自行用 email/calendar_event 發出邀請
- 確認等級：simple approve（交接 CRM）

```json
{
 "brief": "約光泉窗口於 2026-09-02（週三）下午開會，議題：kuangchuan-bi BI 看板改版（現部署於 phyra.uk，含銷售預測模型與 auto-deploy poller）。具體時段、形式（線上/實體）與窗口聯絡資訊待人工確認後由 CRM 流程發出邀請。",
 "client_slug": "kuangchuan",
 "event_context": {
  "proposed_date": "2026-09-02",
  "proposed_period": "afternoon",
  "timezone": "Asia/Taipei",
  "topic": "BI 看板改版",
  "related_project": "kuangchuan-bi"
 }
}
```

### t2 — 會前準備：整理 kuangchuan-bi 看板現況與改版討論素材  `agent_task` `internal` `pending`
- 依據：依 kuangchuan-bi-001（repo: manibari/kuangchuan-bi，部署於 phyra.uk，含銷售預測模型與 auto-deploy poller）與 kuangchuan-001（光泉提供銷售資料包供看板使用），會前先盤點現況可提升會議效率
- 確認等級：自動/simple
