# 拆單一過長檔案

2026-10-04 由 `large-file-refactor`（2026-03 harvest 產生）併入：保留它的操作步驟，門檻與相容層
政策改成 D37 的口徑。門檻只在 SKILL.md 定義一次：超過 400 行黃燈、超過 800 行紅。

## 原則

- **按「什麼屬於一起」拆，不對半切、不按大小切。** 行數只說「看這裡」；搬動一段程式的理由是它本來就屬於別處
- 子檔沒有目標行數。拆完每支落在 200–400 行是常態，但一支 60 行的小檔只要意義完整就對
- 黃燈（401–800）不是必拆：先看裡面是不是混了兩件事，是才拆

## 步驟

### 1. 讀完整支，先列邊界再動手

找自然的切點，依優先順序：
1. **一段流程的不同階段**：例如回合的頭尾 vs 中間的分支（Yellow-Chick `handle.py`）
2. **領域 / 服務**：每段處理不同的概念（PTI-ARES 用 ast 算引用決定每個函式歸哪個服務）
3. **抽象層**：資料存取 vs 畫面 vs 工具函式
4. Next.js / 前端：頁面的各個區塊、子路由

把邊界和每段要去的檔名寫下來，再開始搬。

### 2. 沒有測試就先存基準

每個 endpoint / CLI / 頁面的輸出先存成 baseline，拆完逐筆比對。`import` 成功不代表行為沒變。
Python 搬完跑 `ruff check --select F821,F401` 抓漏掉的常數與名稱。

### 3. 一次抽一段，抽完就驗證

每一段：建目標檔 → 程式碼原樣搬（不順手改判斷）→ 補 import → 匯出父檔要用的名字 → 跑驗證。
驗證過了才抽下一段。

```bash
npx tsc --noEmit && npm run build          # TypeScript / Next.js
python -m pytest -x --tb=short             # Python
```

### 4. 舊 import 路徑：預設改呼叫端，不留轉出

D37 實務（PTI-ARES feature slices、Yellow-Chick 第二段）預設**同一個 commit 改完所有呼叫端**，
不留 re-export 殼——殼會讓「東西在哪」有兩個答案，也會把檔案數加回原資料夾。

例外，這時才留轉出（`X as X`、`index.ts` re-export、`__init__.py` 匯出）：
- joblib / pickle 檔、排程、外部消費者寫死了舊模組路徑（全域規則：搬模組要留相容 shim）
- 其他 session / lane 正在改呼叫端，現在改會衝突——留轉出並在 plan 記下何時拿掉
- 套件本來就有公開 API（`from app.secretary import handle_message`），讓公開名稱改指新位置

```typescript
// components/deals/index.ts —— 只在上述例外時使用
export { DealHeader } from "./DealHeader";
export type { DealPageProps } from "./types";
```

### 5. 收尾

原檔要嘛刪掉，要嘛只剩一支薄的協調者（頁面 orchestrator、回合頭尾）。
在 `size_ratchet.json` 上的檔，同一個 commit 從清單刪除（不刪 gate 會紅）。

## 例子

**Yellow-Chick `app/secretary/turn/handle.py` 862 → 362**：照一回合裡哪些屬於一起，拆成回合頭尾
`handle.py`（362）、分支 `branches.py`（400）、分支的小答案 `branch_replies.py`（169），程式碼原樣搬。

**React 頁面 1343 行**：

```
app/deals/[id]/
├── page.tsx              orchestrator
├── DealHeader.tsx
├── DealTimeline.tsx
├── DealActions.tsx
└── types.ts              共用型別
```

## 常見陷阱

- **循環 import**：A 匯入 B、B 又匯入 A → 共用的型別抽到 `types.ts` / `types.py`
- **monkeypatch 換不掉**：測試用 `monkeypatch.setattr(module, "name", ...)` 換掉的名字，要留在**呼叫它的那個模組**裡
  （Yellow-Chick `provider_for` 因此留在 `handle.py`）
- **logger 名稱**跟著模組路徑變，搬前 grep 有沒有人用 logger 名稱過濾
- **prop drilling**：拆元件拆出 5 層以上傳 props，改用 context 或 state hook
- **測試位置**：新模組的測試跟著放到對應的測試子資料夾，別塞回已超標的 `tests/` 第一層
