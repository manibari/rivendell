# Session Harvest 報告 — 2026-08-20

## 一、Session 摘要

| # | 專案 | 訊息數 | 關鍵活動 | 產出/素材 |
|---|------|--------|----------|----------|
| 1 | Norns-ERP | 31 | 定義新功能：客戶商品進貨依編號/日期入庫，工人依日期出庫時用影像辨識箱子上的編號與日期，自動填寫型號/製造日/進貨日並出帳。使用者要求先更新 `task_plan.md` 再 commit | IMG_2921/2928/2929/2930.jpg（箱子照片）；AskUserQuestion 1 次 |
| 2 | PTI-ARES | 141 | 除錯：`enrich` 階段把帶屬性尾巴的字串丟進 `float()` → `ValueError: could not convert string to float: '1.0544;ID=66)'`；用本機樣本 `gdp_e3s_16_fab0_0616a.tgz`（`downloads/` 下）重現問題 | err_zoom.png, tok2.png, tok_zoom.png, photo_2026-08-20 14.34.29.jpeg；Bash 129 次 |
| 3 | ~/code（根目錄，跨專案） | 10 | 使用者想從「立積電」與「光泉」兩個案子裡找出共通規律：兩邊都需要一個前端控制中台，問要不要做一個平台來承接 | Bash 9 次（應為搜尋既有專案結構，非動工） |

**已排除、非新 skill 需求**：無明顯既有 skill 的「正常執行」個案（不像 08-19 那批有 crm-projection 排程執行）。

---

## 二、Skill 候選

本批 3 個 session 都能對應到既有 skill 或既有 memory 記錄，**沒有找到值得開新 skill 的缺口**。逐一說明：

### Session 1 → 已被 `ai-vision-extract` + `planning-with-files` 涵蓋（不開新 skill）

- 「拍照 → AI 辨識箱子編號/日期 → 填寫型號/製造日/進貨日 → 出帳」完全落在 `ai-vision-extract`
  的觸發詞範圍內（「拍照辨識」「label extraction」「用 AI 看圖抽資料」），且該 skill 已經把
  「identify → normalize → cache → generate → persist」的管線和成本/容錯考量寫清楚，可以直接套用。
- 「先更新 task_plan.md 再 commit」的流程對應 `planning-with-files`，也已存在。
- 判斷依據：digest 只看到 1 次出現（N=1），且是「定義需求」階段而非「已跑出一套可重複步驟」，
  沒有新資訊需要另開 skill 記錄。

### Session 2 → 屬於既有 `odb-dfm-reference` 的知識缺口，建議**更新既有 skill**而非開新 skill

- `odb-dfm-reference`（`skills/backend/odb-dfm-reference/SKILL.md`）本來就是 PTI-ARES 的
  ODB++ 解析陷阱參考，第 86-89 行已經寫了「Feature attribute values have two meanings」的
  gotcha（`;3=64` 是索引 vs `;5=0.000000` 是字面數值），但沒有涵蓋這次踩到的**新陷阱**：
  屬性值字串本身帶了尾巴（`'1.0544;ID=66)'`），在 `enricher.py` 直接 `float()` 轉型前
  沒有先切掉 `;ID=...` 這段附加屬性，才炸出 `ValueError`。
- 這是同一個 skill 底下「又踩到一個新的 attribute-parsing 變體」，不是新的工作流程，建議
  等這次除錯完整結束、確認修法後，把「轉 float 前必須先剝離 `;ID=`/其他附加屬性尾巴」補進
  該 skill 的 gotcha 清單（連同具體正規表達式或切法），而不是另開一個 skill。
- 未在本次直接動手更新的原因：digest 只看到錯誤訊息本身，看不到最終怎麼修的（是統一 regex
  剝離、還是針對某個 attribute 類型特判），貿然寫進 SKILL.md 可能記錯解法。下次處理同類問題
  時，建議直接讀完整 transcript 確認修法再回填。

### Session 3 → 已有 `fleet-infra-spine` memory 記錄，且屬於「思考/探索」階段，不該直接開 skill

- 「立積電、光泉都需要前端控制中台，要不要做一個平台」是產品層級的構想確認，屬於 CLAUDE.md
  Step 0 判斷裡的**思考/探索階段**，路由規則明講「產品構想、值不值得做 → 交給
  `gstack-office-hours`」，不是進 skill 開發或直接動工的訊號。
- 這個構想本身也不是新發現——`fleet-infra-spine` memory（2026-06-27 office-hours 結論）已經
  記錄「8+ 產品共用 infra spine，策略是 recipe-skills + greenfield starter skeleton，只從
  成熟產品的交集抽取」，跟這次的問題是同一件事的延續，不是新模式。
  也已經有 `spine-auth`、`spine-rbac`、`spine-schema-sync`、`spine-versioning` 等
  recipe-skill 在落地這個策略。
- 只有 10 則訊息、9 次 Bash（形態像是在查既有專案而非產出成果），證據量太薄，且方向已經
  被既有策略涵蓋，不構成新 skill。

---

## 三、結論與建議

本批 3 個 session **沒有 Strong/Moderate 候選**：
- Session 1、3 都命中既有 skill／既有 memory 的既定策略，屬於「正常使用」而非新缺口。
- Session 2 是既有 `odb-dfm-reference` 該補一條 gotcha，但目前證據不足以確定正確修法，
  建議下次處理完整個 PTI-ARES enrich bug 後，回頭把「屬性尾巴污染數值字串」的具體修法
  （regex/切法）補進 `odb-dfm-reference` 的 gotcha 清單。

**下一步**：無需新增 skill；PTI-ARES 這次除錯結束後回填 `odb-dfm-reference` 的既有章節即可。
