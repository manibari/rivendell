# Acceptance Criteria: Structure and Checklist

Use this reference to write section 五（驗收程序與標準）and 附件 A of every SOW.

**Completion test for one criterion**: give it to a third party who does not know the project.
That person must be able to run it alone and get the same pass/fail result as both parties.

Origin: a PTI-ARES Phase 1-1 SOW (2026) said only "rule check accuracy X%". It did not state
if the input data was before or after manual preparation. The gap caused heavy unplanned development.

---

## 1. Three layers

```
SOW
├─ Layer 1: Scope            → 二、服務工作內容, 四、交付項目 (what is in, what is out)
├─ Layer 2: Criteria (body)  → 五、5.2 one row per criterion: elements 1, 2, 3, 6
└─ Layer 3: Test plan        → 附件 A: elements 4, 5, 7, 8
```

- Layer 1 defines the deliverables. A function that is not a deliverable is not accepted or tested.
- Layer 2 is the contract text. Keep one row per criterion.
- Layer 3 holds test data, formulas and procedures. This keeps the body short.

Standards behind the layers:

- **PMBOK** (scope statement): deliverables, acceptance criteria, exclusions → Layer 1
- **ISO/IEC/IEEE 29148** (requirements): each requirement must be verifiable → Layer 2
- **ISO/IEC/IEEE 29119** (software testing, formerly IEEE 829): preconditions, inputs, steps,
  expected result, pass criteria → Layer 3
- **ISO/IEC 25010** (quality model): use it to select metrics for AI or system quality

---

## 2. Eight elements of one criterion

| # | Element | 中文 | Question to answer | Failure when missing |
|---|---|---|---|---|
| 1 | Object | 驗收對象 | Which deliverable or function? | Client tests a function that is not in scope |
| 2 | Metric and formula | 指標與算法 | What is measured? What is the numerator and the denominator? | Both sides calculate a different "accuracy" |
| 3 | **Input condition** | **輸入條件** | Which state of the data? Who prepares it? | Client tests with raw data, vendor must build more |
| 4 | Test data | 測試資料 | Which data, how many? When is it fixed? Can it change? | Data changes at test time, results change |
| 5 | **Reference** | **對照基準** | Compared to what? Who sets the expected answer? | A third-party tool becomes the answer key with a different definition |
| 6 | Threshold | 門檻 | Which value is a pass? | "A little better" never ends |
| 7 | Judgment procedure | 判定程序 | Who judges? How many runs? What is retested after a fail? | Full retest, passed items are reopened |
| 8 | **Exclusions** | **排除與例外** | Which cases are not a vendor fault? | Client data problems become vendor development work |

Elements 3, 5 and 8 are missed most often. They decide **who is responsible**.
Elements 2 and 6 only decide **how good** the result must be.

---

## 3. Templates

### 3.1 Data state definition (put in 二、服務工作內容)

When the system has a manual preparation step, define each data state first.
Every criterion then names one state in its 輸入 column.

```markdown
### 資料狀態定義

| 狀態 | 定義 | 由誰完成 |
|---|---|---|
| **{原始資料}** | {未經人工處理的狀態} | 系統自動 |
| **{整理後資料}** | {甲方人員完成整理並凍結的狀態} | 甲方 {角色} |
| **{已處理資料}** | {以指定版本完成處理與判定的狀態} | 系統處理，甲方判定 |

- {人工整理步驟} 由甲方執行，不在乙方服務範圍內。其錯誤或缺漏造成的差異，不計為乙方的錯誤
- 所需輸入不存在時，系統回報「未判讀」，視為正確行為，不計入分母
```

### 3.2 Criteria table (5.2 in the body)

```markdown
### 5.2 驗收標準

每一條驗收標準以「通過／不通過」判定。同一里程碑的驗收標準全部通過，該里程碑才算驗收通過。
「輸入」欄註明該條使用的資料狀態。驗收時不得以其他狀態的資料取代。

**驗收通則**：

1. **版本凍結**：驗收期間，測試資料、{系統／規則／模型} 版本不得變更。任一版本變更，受影響項目重新測試
2. **題目不變**：依簽認時的文字執行，不得在驗收時改寫或追問
3. **執行次數**：每項執行 {一} 次，以第一次結果判定
4. **重測範圍**：未通過的條目修正後，只重測該條目
5. **第三方工具**：不以 {第三方工具} 的結果作為通過條件（除非雙方已逐條對齊定義）

**M{N}：{里程碑名稱}**

| 編號 | 驗收標準 | 輸入 | 驗證方式 |
|---|---|---|---|
| AC-{N}-1 | {對象} 的 {指標} ≥ {門檻}，算法依附件 A-{n} | {資料狀態} | {題庫測試／逐筆比對／現場操作／文件審閱} |
```

### 3.3 Test plan (附件 A, one block per metric)

```markdown
### A-{n} {指標名稱}

- **測試資料**：甲方指定 {N} 筆 {資料狀態}，於 {M?} 前簽認並記錄版本，驗收期間不更換
- **指標算法**：{指標} ＝ {分子} ÷ {分母}
- **對照基準**：{標準答案的來源}，由 {雙方共同／甲方} 於簽認時確認
- **判定程序**：由 {誰} 判定，執行 {N} 次
- **排除與例外**：{不計入分母或不計為錯誤的情況}
- **題目範圍**（題庫類適用）：答案必須能由交付範圍內的資料得出。超出範圍的題目，乙方得於簽認前要求替換
```

---

## 4. Worked example

**Weak**: 規則檢查準確率達 90%。
Only element 6 is present. Element 2 has a name but no formula.

**Complete**:

| 編號 | 驗收標準 | 輸入 | 驗證方式 |
|---|---|---|---|
| AC-01 | 規則檢查召回率 ≥ 90%，算法依附件 A-1 | 凍結板（甲方 PE 已完成 Prepare 並凍結） | 逐筆比對 |

附件 A-1:

- 測試資料：甲方指定 3 塊板，簽約後 30 日內簽認，驗收期間不更換
- 指標算法：召回率 ＝ 系統報出且與標準答案相符的違規筆數 ÷ 標準答案的違規筆數
- 對照基準：雙方共同標註的違規清單。量測起訖點依規則定義，不以第三方工具的量法為準
- 判定程序：雙方共同執行，逐筆比對，每塊板執行一次。未通過的規則修正後只重測該規則
- 排除與例外：Prepare 錯誤或缺漏造成的差異不計入；規則所需輸入不存在時回報「未判讀」，不計入分母

---

## 5. Checks before delivery

- [ ] Each deliverable has at least one criterion
- [ ] Each criterion is pass/fail. No adjectives such as「良好」「穩定」「合理」
- [ ] Each ratio states the numerator and the denominator
- [ ] Each criterion names the input data state and who prepares it
- [ ] The answer key owner is fixed before signing
- [ ] No third-party tool result is a pass condition, unless definitions are aligned item by item
- [ ] Data, versions and questions are frozen during acceptance
- [ ] The retest scope is only the failed items
- [ ] Client data duties have deadlines. Late data extends the schedule
- [ ] Requests outside scope go to the change-management clause
- [ ] For AI answers: the question set has a scope rule, one run per question, and a "no fabrication" item
- [ ] An optimization criterion with no baseline data follows section 6: the method is in the contract, the number comes after the training period

---

## 6. Optimization with no baseline data

Use this section for an AI that tunes a running process (air conditioning, energy, yield,
scheduling) when there is no data and no baseline at signing. A fixed "saves X%" fails
element 5: there is nothing to compare with.

Put the method in the contract. Set the number later.

1. **Fix how to measure, not how much.** The contract states the metric, the formula, the
   meters, the normalization (outdoor weather, occupancy, production volume) and the
   comparison method.
2. **Compare in the same period.** Alternate "AI on" and "AI off" in the same weeks, by day
   or by week. Sign the alternation table before the test. Do not compare different
   seasons or the last year.
3. **Use one constraint and one target.** The service level that the process must keep
   (comfort, quality, delivery) must not get worse. The saving is the target.
4. **Set the number after a training period.** The contract holds a conservative floor.
   Both parties fix the final threshold in writing from the training-period data, before
   the acceptance test.
5. **A claim without a measurement is not a threshold.** A figure from a product page or
   an older project that no test measured goes to 預期效益 only.

```markdown
| AC-{N}-1 | {服務水準指標}（如 PMV）在 AI 控制期間不劣於對照期間，算法依附件 A-{n} | {量測點、期間} | AI 開／關交替比較 |
| AC-{N}-2 | {節能指標} ≥ {保守下限}；正式門檻於訓練期結束後，依附件 A-{n} 雙方書面議定 | {正規化後的量測值} | AI 開／關交替比較 |
```

附件 A-{n}:

- 比較方式：{訓練期結束} 起 {N} 週，AI 控制與原控制方式依 {日／週} 交替；交替表於測試前簽認
- 正規化：以 {外氣溫度、使用人數、產量} 校正
- 正式門檻：訓練期資料完成後 {N} 個工作日內，雙方依交替比較結果書面議定，不低於 {保守下限}
- 排除與例外：設備故障、維修，以及 {甲方} 變更操作條件的期間，不計入

Origin (2026-10-28): an airport air-conditioning tender gave the AI item no number in its
acceptance clause. An older metro-station PoC had measured comfort (PMV) only, not energy.
The product page said 「節能 10–20%」; that figure can go to 預期效益 only.
