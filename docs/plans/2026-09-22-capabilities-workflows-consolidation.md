---
feature: capabilities-workflows-consolidation
date: 2026-09-22
status: implemented-with-legacy-compatibility
scope: platform architecture and migration plan
---

# 技能庫與工作流程整合計畫

> 一句話：`skills/` 保留技能包本體；平台以 `capabilities/catalog` 管技能索引，以 `capabilities/workflows` 管角色、工作、步驟與技能引用，Dashboard 只讀同一組平台資料。
>
> 依 2026-09-22 程式碼實查。本文件記錄遷移方向與執行狀態；現行結構請看 [Repository layout](../architecture/repository-layout.md)。

## 目前執行狀態（2026-09-22）

- `platform/capabilities/catalog/` 與 `workflows/` 已落地，舊實體路徑以 symlink 相容；Compose、Docker COPY、dashboard lib 入口已切新位置。
- 11 角色、44 工作、PDCA 與缺口已成為 `definitions/` 中的 JSON；四頁 playbook 已成為 `playbooks/*.json`，前端不再硬編流程內容。技能 chip 的補充說明在 `catalog/playbook-skill-details.json`。
- `/api/skills/roles` 從新定義投影，與原 Markdown 解析結果逐欄相同。`sk check workflows` 檢查 ID、引用、125 支本地技能覆蓋與角色文件漂移；技能詳細 API 可反查所屬工作。
- 舊 `/api/workflow` GET/PUT 與 `workflow-map.json` 保持獨立相容資料，**不寫入新定義**。舊 `skillMeta` 的 49 個非本地名稱中，39 個屬 gstack，10 個是舊名稱或未分類；未人工確認的舊 domain/situational 流程不匯入。
- 此機器目前的 `~/.claude/CLAUDE.md` 沒有「Development Workflow」段落；新 playbook 無法與該段作漂移比對，也不改動使用者環境檔案。
- 角色文件的表格仍須人工同步，但檢查命令會擋住定義與文件不一致。保留原有敘述與圖；表格自動生成器和舊 PUT 使用者盤點仍是後續收斂工作。

## 1. 現況與問題

| 資料 | 現在的主人與讀取者 | 已確認的內容 |
|---|---|---|
| `skills/*/*/SKILL.md` | 技能作者寫；`platform/skill_catalog/skills.py` 與 `sk` 讀 | 125 支本地技能；`name`、描述、`loop`、`pdca` 等資訊的來源 |
| `docs/skills-by-role.md` | 人工維護；`platform/workflows/roles.py`、`/api/skills/roles`、`sk check` 讀 | 11 個角色、44 件工作；125 支本地技能皆至少出現一次；含 45 個明示缺口與人工敘述 |
| `apps/dashboard-web/src/app/projects/[name]/workflow/playbook-data.ts` | 前端人工維護；`FlowView` 讀 | Rivendell 的 UI、Backend、Slide、Maintenance 四頁 playbook；目前頁面的實際資料來源 |
| `platform/workflows/workflow-map.json` | `/api/workflow` GET/PUT 讀寫；目前前端未讀 | `skillMeta` 123 筆、2 條 track、14 條 domain flow、19 組 situational；與現有技能命名有漂移 |
| `~/.claude/CLAUDE.md` | 使用者環境中的執行規則；前端 playbook 宣稱與其對照 | 不在 repo 內，不能由本次搬檔直接變更 |

實查舊 JSON 的 `skillMeta` 缺 51 支現有本地技能，另有 49 個鍵不是現有本地技能；引用集合中有 50 支本地技能沒有被引用。這些數字混有外部 gstack、改名與過期內容，**不能將差集直接判作缺陷，也不能把舊 JSON 整份當作新主檔**。`docs/skills-by-role.md` 的角色映射完整，但較細的 playbook 步驟散在 TypeScript 與外部執行規則中。

目前 `skills/workflow/` 是「工作流程與 Session」類別的**技能包**，不是平台流程定義的存放處；保留其分類。

## 2. 目標邊界與統一語言

| 名詞 | 定義 | 穩定識別碼 |
|---|---|---|
| Skill／技能包 | 可被觸發的單一能力；指令、驗收與專用工具在 `SKILL.md` 所屬目錄 | `source:name`；本地例如 `rivendell:requirement`，外部例如 `gstack:gstack-review` |
| Catalog／技能目錄 | 從技能包、外部安裝資訊及平台清單建立的索引與狀態 | Skill ID |
| Workflow／工作流程 | 一件工作如何完成；由有順序的步驟組成，步驟可引用零到多支技能 | `workflow_id`；既有角色工作沿用 `1a`、`1b` 等 job ID |
| Step／步驟 | 具體動作、條件、驗收與技能引用；**可以沒有 skill** | workflow 內唯一的 step ID |
| Role／角色 | 對工作與驗收負責的帽子；不是一份技能複本 | 既有角色 ID `1` 至 `11` |
| Run／執行紀錄 | 某次工作實際跑到哪一階段 | 沿用現有 `job`、`stage` 遙測欄位；不存進流程定義 |

`catalog` 回答「有哪些技能、從哪裡來、能否使用、如何觸發」；`workflows` 回答「這件工作先做什麼、何時使用哪支技能、誰驗收」。流程只持有 Skill ID，不複製技能描述或 `SKILL.md` 內文。助理的 `assistant/dispatch` 是行動核准流程，其他專案的業務流程由各專案擁有，均不併入此模組。

## 3. 目標資料夾與寫入權責

```text
rivendell/
├── skills/<category>/<name>/SKILL.md       技能包唯一來源；既有部署路徑不動
├── platform/capabilities/
│   ├── catalog/
│   │   ├── skills.py                       本地／外部技能索引
│   │   ├── hooks.py                        hook 與安裝狀態
│   │   ├── routing-tests.json              觸發路由測例
│   │   └── ...                             既有 catalog 清單與工具
│   └── workflows/
│       ├── definitions/
│       │   ├── roles.json                  角色 ID、名稱與職權
│       │   └── jobs/<job-id>.json          角色工作、PDCA、步驟與技能引用
│       ├── playbooks/<id>.json             UI／Backend／Slide／Maintenance 細節
│       ├── model.py                        讀取、驗證與查詢
│       └── projections.py                  舊 API／角色文件／前端讀取形狀
├── apps/dashboard-api/routes/               HTTP adapter，保持現有入口
├── apps/dashboard-web/src/app/skills/        技能總覽、流程、角色、Harvest
└── docs/skills-by-role.md                    人讀的角色說明與圖；結構化段落由定義產生
```

實作時 `platform/skill_catalog`、`platform/workflows` 可先保留相容入口；先更新 import、Compose、Docker COPY、CLI 與測試，再移除舊路徑。`platform` 不能作 Python import package 名，因為會撞 Python 標準函式庫；目前的 `lib.*` 相容層也需逐項遷移。

| 資料落點 | 唯一寫入者 | 讀取者 | 不變式 |
|---|---|---|---|
| `skills/*/*/SKILL.md` | 技能作者／既有技能建立流程 | Catalog、部署器、驗證器 | 技能名稱唯一；描述與觸發規則從此讀取 |
| `capabilities/workflows/definitions/*`、`playbooks/*` | 工作流程編輯入口，走同一個驗證器 | API、文件產生器、Dashboard、`sk check` | role/job/step ID 唯一；每個技能引用可解析或標明外部來源 |
| `docs/skills-by-role.md` 的結構化區塊 | Workflow 文件產生器 | 使用者、API 文件頁 | 與定義檔內容一致；人工撰寫的角色說明、接縫敘述與圖保留在非生成區塊 |
| `routing-tests.json` 與 hook manifest | Catalog 管理入口 | `sk check`、部署器 | 路由測例與 hook 宣告不由工作流程頁私自改寫 |
| `agent_runs`、`tasks.jsonl` | 既有執行紀錄產生者 | Workflow 遙測投影 | 只記執行事實；不反向改流程定義 |

資料格式先採**每件工作一個 JSON 檔**，避免新增 YAML 依賴；API 提供前端所需的 JSON 投影。`roles.json` 與 job ID 沿用現值，避免既有 `task-tag.sh`、`sk run --job` 與歷史遙測失聯。Step 模型須包含 `id`、`order`、`action`、`stage`、`skill_refs`（`source`、`name`、`mode`）、`condition` 與 `gate`；`mode` 區分主線、視情況與自動。無技能動作與 `★` 缺口要能原樣表示。

## 4. 介面與畫面契約

第一階段**不改** `/api/skills`、`/api/skills/roles`、`/api/workflow` 的既有方法和回傳形狀，也不改 `/projects/rivendell/workflow/{ui,backend,slide,maintenance}` 的可到達性。先在 API 內加投影層，讓新定義可產生舊讀取形狀；兩份輸出對比通過後才切讀取來源。

切換後建議由 `/api/capabilities/workflows` 提供有版本的正規化讀取契約：

| 介面 | 輸入 | 成功 | 錯誤與重送 |
|---|---|---|---|
| `GET /api/capabilities/workflows` | 可選 `role_id`、`job_id` | 符合條件的 workflow 摘要與定義版本 | 未知 ID 回 404；重送無副作用 |
| `GET /api/capabilities/workflows/{id}` | workflow ID | 角色、工作、階段、步驟、技能引用及 Catalog 投影 | 未知 ID 回 404；技能不可用仍回定義，狀態標為 unavailable |
| 既有 `GET /api/skills/roles` | 無 | 維持 `SkillRolesData` 形狀、既有 job ID 與 telemetry | 定義檔損壞時明確回錯，不能靜默回空列表 |
| 既有 `GET/PUT /api/workflow` | 舊 JSON 形狀 | 遷移期維持相容 | PUT 目前可整份覆寫；切換前須查使用者並設計驗證、原子寫入及衝突處理，不能靜默改寫新主檔 |

新寫入介面若真的需要，另以 typed request、定義版本／ETag 做衝突檢查；驗證失敗回 422 並列出無效 ID 或技能引用，版本衝突回 409。相同版本與相同內容重送應冪等。這是**目標契約**，不表示現有 API 已具備這些防護。

Dashboard 的技能庫新增「工作流程」入口，現有四頁清單式 playbook 保持視覺與互動，資料改由 API 投影供應；角色頁仍能顯示 PDCA、缺口與遙測。舊專案路徑可在內容等價後轉到 `/skills/workflows/...`，維持書籤相容。技能詳細頁可列出「被哪些工作步驟使用」，從同一引用索引反查。

## 5. 遷移順序與完成條件

| 順序 | 工作 | 可驗收的產物 |
|---|---|---|
| 0. 基線與核對 | 匯出角色文件、四頁 TypeScript playbook、舊 JSON 與 `~/.claude/CLAUDE.md` 的差異；逐項判斷舊名稱、外部 skill、過期流程 | 對照表有「保留／合併／封存」決定；不自動聯集三套資料 |
| 1. 能力邊界 | 建 `platform/capabilities/{catalog,workflows}`，搬移管理程式與設定；保留舊 import／檔案入口 | `sk deploy`、`sk check routing`、Catalog API 與 Compose 均讀新主人；技能包目錄不變 |
| 2. 新流程模型 | 以角色文件匯入 11 角色、44 工作及 PDCA；以 TypeScript 匯入四頁細節；舊 JSON 只匯入人工確認的獨有流程 | Schema 驗證、ID 唯一性、技能引用解析、外部來源區分、缺口保留 |
| 3. 投影與文件 | API 同時從新舊來源產生讀取結果並比對；角色文件結構化區塊改由新定義產生，人工敘述保留 | `/api/skills/roles` 結構與 11／44／45 基線一致；125 支本地技能的角色覆蓋仍為 100% |
| 4. Dashboard 切換 | 四頁 playbook 與角色頁改讀 API；技能頁加入工作流程與反向引用 | 四頁內容、技能 chip、條件與 modal 操作逐頁對照；舊 URL 仍可到達 |
| 5. 收斂舊來源 | 核查 `/api/workflow` PUT 使用者後決定相容 adapter；舊 JSON 與 TypeScript 靜態資料封存，文件註明新來源 | 沒有第二個可寫流程主檔；CI 的 workflow 檢查失敗時不能通過 |

跨步驟 gate：每一階段都跑 API 與前端既有測試、`sk check`、Compose 建置／設定檢查；讀取切換前增加快照比對，驗證 role/job/stage/step/skill_ref 與四頁 playbook，避免只看數量相同。外部 gstack skill 仍由 gstack repo 提供，不搬入本 repo。

## 6. 風險與反證關卡

| 風險 | 防護與可反證條件 |
|---|---|
| 舊 JSON 與現有技能名稱漂移 | 先分類 51／49 差集；未分類引用阻擋匯入，不以名稱相似度自動改名 |
| 角色 Markdown 的人工敘述在生成時遺失 | 生成只作用於標記的結構化區塊；生成前後比較非生成區塊位元內容 |
| job ID 改動使歷史執行次數歸零 | 11 角色、44 job ID 作基線；遷移測試比對遙測 join，改 ID 必須有明確 alias |
| `PUT /api/workflow` 覆寫新定義 | 使用者盤點前不切寫入；新 adapter 必須驗證、原子寫入並處理版本衝突 |
| Dashboard 看似切換，仍暗讀 TypeScript 或舊 JSON | 靜態引用掃描與頁面資料測試；切換後移除前端硬編資料，只保留顯示元件 |
| `~/.claude/CLAUDE.md` 與 repo 定義不同步 | 它仍是外部執行規則；先做步驟與必經 skill 差異報告，不自動覆寫使用者檔案 |
| 模組搬深一層後 `__file__` 推算根路徑錯誤 | 更新 repo root 推算與容器 COPY／掛載路徑；在本機與 Docker 各驗一次 Catalog、角色文件和流程檔 |

## 7. 未決事項

| 問題 | 暫定處理 | 拍板者 | 必須決定的時點 |
|---|---|---|---|
| 舊 JSON 中 14 條 domain flow、19 組 situational 哪些仍有效？ | 逐項核對使用情境與 skill 名稱後匯入 | 專案維護者 | 第 2 階段匯入前 |
| `/api/workflow` PUT 是否有 repo 外的編輯者？ | 先保留既有行為與資料，查實際呼叫；無法證實無使用者前不刪 | 專案維護者 | 第 5 階段切寫入前 |
| `~/.claude/CLAUDE.md` 的執行 gate 是否由 repo 定義產生？ | 先做 drift report，不自動寫使用者環境 | 專案維護者 | 四頁 playbook 切換前 |
| `docs/skills-by-role.md` 的人工敘述如何標記保留範圍？ | 先設生成區塊標記、做非生成內容 diff，再遷移 | 專案維護者 | 第 3 階段文件產生前 |
| 誰可以從 API 編輯流程？ | 新寫入入口先不開放；確認使用者與權限模型後再設計 | 專案維護者 | 新寫入介面實作前 |

這份規劃確定了資料主人與順序；實作前再依 `system-design` 的 Full 檔位補正式 schema、目標資料流圖與 API 錯誤契約，供工程審查。這次先不搬資料、不更動技能包，也不改執行中的工作流程。
