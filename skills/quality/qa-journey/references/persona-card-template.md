# Persona Card Template

Persona cards are **product assets**: one card per audience per product, saved in the
target project at `docs/personas/<name>.md` — never inside this skill. One card feeds
multiple consumers (qa-journey, user-flow, future agentic workers); each consumer reads
only its own projection plus the shared core.

Design rule: **the rule layer (規則層) is the contract; the narrative layer (敘述層) is
color**. Consumers act only on the rule layer — LLM 對敘述形容詞的服從度低，對可判定
規則的服從度高。When creating a card, spend the effort making rules concrete and
checkable; keep the story short.

Copy everything below the line into `docs/personas/<name>.md` and fill it in.

---

```markdown
---
name: <kebab-case-persona-id>
product: <which app/product this persona uses>
schema_version: 1
updated: YYYY-MM-DD
---

# <顯示名稱，例：不熟軟體的會計主管 阿芳>

## 敘述層（背景，供理解，消費者不得當指令用）

一段話：這個人是誰、在什麼情境下打開這個產品、他的一天長什麼樣。

## 規則層 — core（所有消費者共用）

### 目標（任務語言，不是功能語言）
- 任務：<一句話，例：把 6 月的發票整理好寄給會計>
- 完成判定：<可驗證條件，例：會計信箱收到含附件的信 / 系統顯示已送出>

### 知識邊界
- 知道：<例：自己的帳號密碼；產品首頁網址；Excel 基本操作>
- 不知道：<例：任何內部 URL 路徑；功能的內部名稱；「匯出」藏在哪個選單>

### 耐心閾值（數值，不是形容詞）
- 同一目標找不到入口，掃描畫面 N 次後記 LOST：N = <預設 2>
- 同一路徑嘗試 N 次後放棄（DEAD_END）：N = <預設 3>

### 在乎什麼（friction 嚴重度加權）
- <例：怕按錯把資料弄丟 → 破壞性操作沒有確認 = 高嚴重度>
- <例：時間壓力大 → 多餘步驟的嚴重度調高>

## Projections（各消費者專屬區塊，只有該消費者可改）

### qa-journey
- 進入點 URL：<唯一允許直接前往的網址>
- 裝置/視窗：<desktop 1440 寬 / mobile 390 寬>
- 額外禁止事項：<例：不用鍵盤快捷鍵；不開第二個分頁>

### user-flow（佔位，接上時再填）
- 此角色可見的分支/權限：

### agentic-worker（佔位，未實作 — 等第一個真實 worker 案子再定欄位）
- 預期對映：知識邊界 → tool/資料存取範圍；耐心閾值 → retry/escalation 政策；
  在乎什麼 → 自主決策準則。在那之前不要填。
```

---

## Creating a card interactively (qa-journey Step 0 fallback)

Ask the user only these three questions, then draft the full card yourself and show it
for confirmation:

1. 這個使用者是誰？（職務 + 對這類軟體的熟悉度）
2. 他這次要完成什麼任務？（做完的判斷標準是什麼？）
3. 他從哪裡進來？（首頁？某個連結？通知？）

Fill 耐心閾值 with defaults (2 / 3) unless the user says otherwise. Derive 不知道 from
the tech-savviness answer — err on the side of knowing LESS: a persona that knows too
much silently disables the whole point of journey QA.

## Evolving the schema

- Adding a new projection block = non-breaking; old consumers ignore it.
- Changing core fields = bump `schema_version`; consumers that find an older version
  or missing fields must report「待補」and stop, not guess values.
