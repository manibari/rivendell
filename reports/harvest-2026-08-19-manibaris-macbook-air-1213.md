# Session Harvest 報告 — 2026-08-19

## 一、Session 摘要

| # | 專案 | 訊息數 | 關鍵活動 | 產出檔案 |
|---|------|--------|----------|----------|
| 1 | Vault/Peter-Work（光泉專案） | 70 | 準備待用簡報：說明資料/建模方式有大改，被追問「最後應用的準確度多少」，改跑地端 Verdandi AutoML 對實際資料驗證一次，取得準確度數字並產圖 | daily.png, daily2.png, map.png, run_verdandi_weatherfix_item.py, run_verdandi_三天後訂購量_models.py |
| 2 | Verdandi-AutoML | 41 | 「今天有很多 bug」，動手修之前先盤點今天光泉專案改了什麼（瀏覽器查了某個頁面/看板） | — |
| 3 | sales-assistant | 1 | 執行既有 `crm-projection` skill（query nx_client → 抓 deal pipeline → cross-reference） | — |

**已排除、非新 skill 需求**：#3（`crm-projection` skill 本身已存在，這就是它被排程/手動觸發的正常執行，不是新工作流程）。

---

## 二、Skill 候選

### 🟡 Moderate：`automl-slide-benchmark`（簡報前跑地端 AutoML 驗證出圖）

- **用途**：客戶簡報前，針對「資料/建模方式有大改」的質疑，改跑地端 Verdandi AutoML 對真實資料做一次驗證，取得準確度數字，並把結果轉成簡報用的圖（時序圖、地圖等），而不是空口報數字。
- **觸發時機**：要為客戶/主管簡報做資料或模型相關的準確度佐證、被追問「這個準確度多少」「有數據支持嗎」。
- **涵蓋步驟**：定位對應的地端測試腳本（`run_verdandi_*.py`）→ 對實際資料跑一次 → 讀輸出的準確度指標 → 產出視覺化圖檔（daily/map 等）→ 交給簡報使用。
- **分類建議**：`docs`（緊鄰 `iot-factory-report`／`chart-design`，同屬「跑分析 → 出簡報素材」）或 `business`。
- **來源**：Session #1，Bash(42)/Read(15)/Edit(4)/Write(1) 圍繞著跑 `run_verdandi_weatherfix_item.py`、`run_verdandi_三天後訂購量_models.py` 並產出三張圖檔，明顯是「驗證 → 出圖 → 簡報」的完整循環。
- **現有相似**：`ml-eval-quality` 是 Verdandi-AutoML 的評估指標**知識參考**（怎麼算 CV/R²/drift），不是「跑一次驗證並轉出簡報素材」這個操作性流程；`iot-factory-report` 出圖模式類似但領域是 IoT 時序而非 AutoML 準確度驗證。兩者互補不重疊。
- **為何列 Moderate 而非 Strong**：目前只有 1 次出現（N=1），digest 看不到準確度指標具體是什麼（R²/MAPE/其他）、圖檔內容細節、以及腳本是否為光泉專案特有的一次性腳本或可重用模板。建議下次「簡報前驗證準確度」需求再出現時，讀完整 transcript 確認腳本可重用程度，再決定要不要做成獨立 skill 或併入 `ml-eval-quality`。

---

## 三、未列入候選的原因

- **#2（Verdandi-AutoML 盤點今日變更）**：「先盤點今天改了什麼再修 bug」的做法，方向已被 `gstack-investigate`（root cause first）涵蓋，且本次證據太薄（digest 只看到 2 次瀏覽器 navigate/computer 呼叫，看不出查的是哪個看板、盤點了什麼），貿然歸納會是空口猜測，不構成新 skill 缺口。
- **#3**：`crm-projection` skill 已存在，這是它的正常執行，非新工作流程。

---

**建議下一步**：本批訊號偏薄（3 個 session，其中 1 個是既有 skill 的正常執行，1 個證據不足以歸納）。唯一候選 `automl-slide-benchmark` 卡在 N=1，暫不建議動手。若下次光泉或其他 AutoML 專案再出現「簡報前跑驗證出圖」的需求，直接讀完整 transcript 確認腳本/圖檔的可重用結構，再評估是否值得獨立成 skill。
