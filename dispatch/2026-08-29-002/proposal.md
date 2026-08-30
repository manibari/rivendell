# Dispatch 2026-08-29-002

**指令/事件**：決定了：rivendell 不掛 codex oauth，維持 claude 單引擎就好

**理解**：Peter 拍板：Rivendell 不掛接 codex oauth，維持 Claude 單引擎架構，需推翻知識庫中「評估掛接 codex oauth」的舊方向並同步相關文件。

## ⚠️ 方向衝突（需先 resolve）

- **#1** [projects/rivendell rivendell-001] 舊：Rivendell 的定位方向：透過 skills 搭配知識庫與 SaaS 服務運作成個人助理，並評估掛接 codex oauth
  新方向：不掛接 codex oauth，維持 Claude 單引擎
  說明：rivendell-001 記載「評估掛接 codex oauth」為進行中方向，本次指令明確終止該評估，屬決策更新而非新增事實，應以 supersede 方式取代舊 fact。
  → keep-new 將寫入：Rivendell 的定位方向：透過 skills 搭配知識庫與 SaaS 服務運作成個人助理；已決定不掛接 codex oauth，維持 Claude 單引擎架構

## 任務

### t1 — 清查 Rivendell 文件中 codex oauth 相關規劃並改為已否決  `agent_task` `internal` `pending`
- 依據：依據 rivendell-001，掛接 codex oauth 曾是評估中方向，可能已寫入 ROADMAP.md、CHANGELOG.md 或 docs/；決策翻案後需同步文件避免漂移。
- 確認等級：自動/simple
- ⛔ blocked by conflict #1

### t2 — 待辦：確認未來 SaaS 掛接需求一律走 Claude 單引擎前提  `todo` `internal` `pending`
- 依據：rivendell-001 顯示定位仍含 SaaS 服務掛接，決策後續評估任何外部引擎/服務時需以單引擎為前提，記一條待辦供下次 roadmap 檢視時參照。
- 確認等級：自動
