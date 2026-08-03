# 需求：共用專案工作空間（Project Workspace）

> Status: draft · 2026-08-03 · 待 Peter 修
> Step 0（需求驗證）：以 2026-08-03 對話取代 office-hours——痛點、現況、最窄楔子
> 都已在對話中壓過，且有實際案例（潤泰）當證據。若 Peter 認為結論不牢，再補跑
> `/gstack-office-hours`。

## 一句話

**把散在信箱、LINE、會議錄影、本機資料夾裡的專案脈絡，收進一個夥伴看得到、
也改得動的地方，讓「這個案子下一步是什麼」不再只存在某個人的腦裡。**

## 為什麼是現在

三個同時成立的觸發點：

1. **記憶會漂，而且是三天的量級。** 潤泰案的 `STATE.md` 由 Claude 維護，
   `Updated: 2026-07-31`，到 8/3 已經落後於實際檔案（deck v2 在 `~/Downloads/`，
   STATE 只記到 v1）。同一個病更早的病例：`Vault/Peter/PROJECTS.md`，
   最後更新 2026-04-25，寫著「每次 commit 前 Claude 會檢查並更新此檔」——
   那件事從未發生，三個月後整份路徑都是錯的。
2. **要跟夥伴共用資料。** 目前所有脈絡都在 Peter 的本機資料夾，夥伴看不到。
3. **輸入管道已經有一半實作。** 會議錄影的轉錄管線 2026-08-03 剛修好
   （音訊正規化 + 關 `condition_on_previous_text` + 重複迴圈偵測 + `(?)` 標記）。

## 誰用

| 角色 | 人數 | 主要動作 |
|---|---|---|
| **主持人**（Peter） | 1 | 開案、拍板、改 STATE、指派信件到專案 |
| **夥伴** | **3**（2026-08-03 確認） | 看專案現況、讀會議紀錄、**共同編輯**文件 |
| **不是使用者** | — | 客戶。客戶永遠不會登入這個系統 |

**總計 4 人，且要能協作編輯。** 這個數字決定了衝突處理的形狀：4 個人在專案文件上
不需要 Google Docs 式的即時游標，需要的是**不要互相覆蓋**。採悲觀鎖（誰在改就
標示佔用、可強制接手），不做 CRDT。依據 CLAUDE.md「Right-size infra」——
先問實際規模再決定架構。

## 輸入的四條管道，優先序已定

| # | 管道 | 自動化程度 | 為什麼是這個順序 |
|---|---|---|---|
| **1** | **信箱** | **可自動** | 唯一有真 API 的輸入。客戶承諾、報價、資料索取都在信裡。自動進來，專案記憶才不靠人記得回報 |
| 2 | 會議錄影 / 錄音 | 半自動（人上傳） | 轉錄管線已完成，只缺入口 |
| 3 | LINE 討論 | **只能匯入** | LINE 無法抓群組歷史：Notify 已於 2025 終止，Messaging API 只涵蓋自家官方帳號。唯一路徑是內建「傳送聊天記錄」匯出 `.txt` 再上傳 → UI 是上傳框，不是連動開關 |
| 4 | 手動筆記 / 文件 | 人工 | — |

## User Stories

### US-1: 一頁看懂這個案子現在到哪

**As a** 主持人或夥伴
**I want to** 打開一個專案就看到現況、卡點、待辦、最近動態
**So that** 不必翻信箱和資料夾重建脈絡

**Acceptance Criteria:**
- [ ] Given 專案有 `STATE.md`，when 打開專案頁，then 渲染其內容，並顯示最後更新時間與更新者
- [ ] Given `STATE.md` 超過 N 天沒更新，when 打開專案頁，then 明確標示「可能已過期」而不是安靜顯示
- [ ] Given 專案沒有 `STATE.md`，when 打開，then 提供以範本建立，不是空白頁

### US-2: 信箱自動歸入專案

**As a** 主持人或夥伴
**I want to** 把信 cc 到共用信箱，它就自動出現在對應專案下
**So that** 客戶說過什麼、答應過什麼，不需要有人轉寫進文件

**做法（2026-08-03 定）**：Outlook / Microsoft 365，走 **Microsoft Graph API**
（IMAP 基本驗證微軟已停用，Graph 是支援路徑）。開一個 **shared mailbox
`administratum@…`** 當收件匣，service 只讀那一個匣。

**收發分離**：`administratum@` 只負責「收」——夥伴把相關信件 cc 進來即歸檔，
這個位址內部可見即可。對外寄信（US-2b）用真人信箱或中性位址，因為寄件者是
客戶看得到的品牌接觸點，`administratum@` 對客戶而言語意不明。第一刀只做收。

**Shared mailbox 的兩個規格**：無 License 時容量上限 50GB（大附件會吃掉，
對應下方「附件不長存共用層」的約束）；帳號本身停用無法登入，但這不影響
Graph 的 application permission 存取與 `/users/{mailbox}/sendMail`。

**不做**：同步 4 個人的個人信箱。理由是隱私與歸屬一次解決——私人信件永遠進不來，
而「cc 進去」這個人為動作本身就是最準的專案歸屬訊號，比任何比對規則可靠。

**Acceptance Criteria:**
- [ ] Given 共用信箱收到新信，when 同步，then 該信主旨／寄件者／時間／內文摘要出現在對應專案時間軸
- [ ] Given 一封信無法判定專案，when 同步，then 進「未歸屬」清單等人指派，**絕不猜**
- [ ] Given 信件含附件，when 歸入專案，then 附件可下載，保留原始檔名與寄件時間
- [ ] Given service 以 application permission 存取，when 部署，then **必須套 `New-ApplicationAccessPolicy` 把範圍綁死在該共用信箱**——未綁定的 `Mail.Read` application permission 可讀取整個租戶的每一個信箱
- [ ] Given 需要對外回信，when 由 service 寄出，then 寄件者為共用信箱，且該封信同時記錄進專案時間軸

### US-2b: 從專案寄信

**As a** 主持人
**I want to** 在專案頁直接寄信給客戶
**So that** 寄出的內容自動留底，不必事後補記

**Acceptance Criteria:**
- [ ] Given 專案頁，when 寄出信件，then 以共用信箱寄出並寫入該專案時間軸
- [ ] Given 寄送失敗（權限／網路），when 發生，then 明確報錯並保留草稿，**不可靜默失敗**

### US-3: 會議錄影變成可搜尋的文字

**As a** 主持人
**I want to** 上傳會議錄影後自動得到逐字稿與摘要
**So that** 三個月後還查得到客戶當時說了什麼

**Acceptance Criteria:**
- [ ] Given 上傳音訊或影片，when 轉錄完成，then 逐字稿與摘要掛在該專案下，並標示可信度（manual / auto / asr）
- [ ] Given 錄音音量過低或轉錄跑進重複迴圈，when 轉錄完成，then **明確標示不可用**，不是安靜輸出通順的垃圾
- [ ] Given 逐字稿含推測的專有名詞，when 顯示，then 以 `(?)` 標記，並提示回聽確認再對外引用
- [ ] Given 原始影片很大，when 上傳完成，then 系統只保留轉錄稿與連結，**原檔不進共用儲存**

### US-4: 匯入 LINE 討論

**As a** 主持人
**I want to** 把 LINE 群組匯出的聊天記錄丟進專案
**So that** 討論裡的決定不會只留在手機上

**Acceptance Criteria:**
- [ ] Given LINE 匯出的 `.txt`，when 上傳，then 解析成帶時間與發話者的時間軸
- [ ] Given 檔案格式不是 LINE 匯出格式，when 上傳，then 明確報錯並說明如何取得正確檔案
- [ ] Given 同一份記錄重複上傳，when 解析，then 去重，不產生兩份

### US-5: 看與改文件

**As a** 夥伴
**I want to** 在網頁上讀專案的 markdown 文件，必要時直接改
**So that** 不需要 clone repo 或裝任何工具

**Acceptance Criteria:**
- [ ] Given 專案下的 `.md`，when 開啟，then 以渲染後的樣子顯示
- [ ] Given 有編輯權限，when 儲存，then 記錄修改者與時間
- [ ] Given 一人正在編輯，when 另一人開啟同一份，then 顯示佔用中與佔用者，可選擇強制接手
- [ ] Given 兩人仍同時改到同一份，when 後者儲存，then **不靜默覆蓋**——偵測衝突、保留兩版、要人決定

### US-6: 匯出 Word

**As a** 主持人
**I want to** 把文件輸出成 `.docx`
**So that** 能直接寄給客戶或送審

**Acceptance Criteria:**
- [ ] Given 一份 markdown，when 匯出，then 產生 `.docx`，標題階層與表格保留
- [ ] Given 文件含 `(?)` 標記或紅字 `▲` 待補記號，when 匯出，then 提醒這些是內部標記，需先處理

### US-7: 畫圖

**As a** 主持人
**I want to** 在專案裡畫 excalidraw 示意圖
**So that** 架構與流程的討論留在專案裡，不散在別處

**Acceptance Criteria:**
- [ ] Given 專案頁，when 新增圖，then 可編輯並存回專案
- [ ] Given 已存的圖，when 再開啟，then 可繼續編輯（保留可編輯格式，不只是圖片）

## 範圍邊界

| In Scope | Out of Scope |
|---|---|
| 專案清單 + 專案頁（STATE 為核心） | 客戶登入 / 對外入口 |
| 信箱同步（比對成功者） | 全信箱鏡像、信件搜尋引擎 |
| 會議轉錄稿與摘要 | 影音原檔的共用儲存、線上播放 |
| LINE 匯出檔匯入 | 與 LINE 即時同步（技術上不可行） |
| markdown 檢視 / 編輯 | 即時協作游標（Google Docs 式） |
| `.docx` 匯出 | PDF 排版、簡報生成（既有 skill 負責） |
| excalidraw | 其他繪圖格式 |
| 給夥伴的權限（讀 / 讀寫） | 完整 RBAC、稽核日誌、SSO |

## 硬約束

1. **影音原檔與文字分層存。** 會議錄影動輒 GB；`~/Vault` 在 iCloud 上（已知會產生
   `file 2.ext` 衝突副本），本機磁碟 2026-07-26 曾告警 96% CRIT。共用層只放
   轉錄稿與摘要，原檔留在本機／NAS，系統存連結與 checksum。
2. **隱私邊界：信箱是選擇性攝入，不是全同步。** 比對不到專案的信件不進系統。
   這同時是資安邊界——客戶資料與私人信件不該落在同一個共用空間。
3. **LINE 沒有歷史訊息 API。** 設計成「匯入」，不要留下「之後可以自動同步」的暗示。
4. **每個欄位都要有程式在讀。** 沒有消費者的欄位不要建。依據：本 repo 內
   `registry/`、`projects.json`、`knowledge/videos/INDEX.md` 都活著（有程式讀），
   `PROJECTS.md` 只給人看，三個月就死。

## 從哪裡出生

`~/code/product-skeleton`。ROADMAP Wave 3 第一條即為「第一隻真產品從
product-skeleton 出生」，且「骨架前端半邊（Next.js + 同源 proxy）—— 等第一隻真需求
再蓋」。**本需求就是那個真需求。**

可直接複用的既有實作：

| 功能 | 既有 |
|---|---|
| 轉錄 | `skills/media/_shared/scripts/local_transcribe.sh`（2026-08-03 修過） |
| Word 匯出 | `office-docx` |
| excalidraw | `excalidraw-diagram` |
| 信箱 | `imap-smtp-integration` · `oauth-token-vault` |
| 設計系統 | `chimesflow-design`（HARD GATE 的 SoT） |
| 通知 | `~/.config/claude-telegram/env`（已有三個消費者） |

## 已定 / 待答

**已定（2026-08-03）**
- 夥伴 3 人，共 4 人，要能協作編輯 → 悲觀鎖，不做 CRDT
- 信箱 = Outlook / M365，走 Microsoft Graph，**共用信箱**當收件匣，
  service 負責紀錄與寄信

**待答**
1. **共用信箱的位址與租戶** — 決定 app registration 掛在哪個 Entra ID 租戶
2. **`STATE.md` 多久沒更新算「可能過期」？** US-1 的 N 值
3. **跑在哪台**：Mac 還是那台有 GPU 的 Linux。（先前討論傾向 Linux；服務環境與
   地端模型都在那邊，且 Docker on macOS 無 GPU passthrough）
4. **夥伴的身分怎麼登入** — 既然已有 M365 租戶，最省的是走同一組 Microsoft 帳號，
   不要另建一套密碼

## 第一刀（lever-first）

不要七個 story 一起上。

```
第一刀   US-2 信箱同步 → US-1 專案頁
         信箱自動餵養,專案記憶才不靠人記得回報
第二刀   US-3 會議轉錄（管線已完成,只補入口）
第三刀   US-5 文件檢視/編輯 → US-6 Word
第四刀   US-4 LINE 匯入 · US-7 excalidraw
```

理由：US-1 沒有 US-2 就退化成「另一個要手動維護的地方」——那正是
`PROJECTS.md` 與 `STATE.md` 的死法。先把自動輸入接上，這一頁才有活著的理由。
