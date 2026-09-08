新增 4 筆，全部來自「Vault/Peter-Work」那段客戶對話：一個新客戶實體 **立積（Richwave）**，Tukey AI 平台已部署在其內網，正在談「AI 問開工單 → 寫內網 SQL DB → 客戶自寫 RPA 開 SAP」這條線，以及 Power Automate 跨 OS 的卡點與回覆定調。其餘三個 session（PTI-ARES 找圖／下載 pb0027、crm-projection 執行、token 日報）都是純操作指令，沒有可留存的實體事實。

- companies/richwave | richwave-001 | 立積（Richwave）是 Tukey AI 平台已部署於其內網的客戶；2026-09-08 提出新需求：AI 對話問出開工單欄位（料號、數量、晶圓批號、封測廠）→ 寫入內網 SQL DB → 客戶自寫 RPA 開 SAP
- companies/richwave | richwave-002 | 回覆定調：內網 SQL DB 由我方控制，可用顧問點數協助串接，但要同時說明導入流程
- companies/richwave | richwave-003 | Power Automate 卡點：平台在 Linux、客戶是 Windows desktop 版；正規走 Cloud，desktop 只能「按鈕→寫 DB→RPA 輪詢」且未驗證，建議平台＋DB 部署後再測
- companies/richwave | richwave-004 | 內部方向：用現有 AI agent + RPA flow 取代 Power Automate flow，並請立積開測試環境

沒有與既有 fact 矛盾，無 supersedes。summary 已重生成（`companies/richwave/summary.md`）。

一點需要你確認的：摘要只出現中文「立積」，我以 slug `richwave` 建檔（立積電子 = Richwave Technology，且情境是 fabless IC 設計 + 封測廠開工單，吻合）。如果這其實是別家「立積」，跟我說一聲我改 slug。
