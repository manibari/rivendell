本次從 7 個 session 中只抽出 1 個新 entity、3 筆事實：Verdandi-AutoML 專案的 agentic-driver 進入 Phase 4「domain templates」，動機是自動分析報告缺 domain 知識，並確認知識庫要吃 PDF/Word/Excel/CSV。其餘 session（冰機一句提問、sales-assistant 兩個 scraper 排程、rivendell token 日報）都是操作指令或暫時狀態，不記。詠鋐只在 vault 路徑出現、身分不明，未另建 company entity。summary 已重生，`kg.py verify` 通過。

- projects/verdandi-automl | verdandi-automl-001 | Verdandi-AutoML 的 agentic-driver 於 2026-09-03 進入 Phase 4「domain templates」：把領域 playbook（問題定義、資料清單、特徵配方、效益公式）當 MCP resource 餵給 agent，內容放在 vault 詠鋐/products/，定位為「建模知識庫」
- projects/verdandi-automl | verdandi-automl-002 | 自動分析報告品質差被歸因於缺乏 domain 知識，決定在 Verdandi-AutoML 專案中加入領域知識庫來補（2026-09-03）
- projects/verdandi-automl | verdandi-automl-003 | 知識庫要給其他用戶使用時，輸入不能只接受 markdown，需支援使用者上傳 PDF、Word、Excel、CSV（2026-09-03 提出的產品需求）

一點補充：`kg.py add` 的 `--source` 只接受 conversation / manual / inference 三個固定值，本次全用 conversation。
