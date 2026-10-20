---
genre: presales
client: <客戶名>
stage: <first-call | post-discovery | proposal | final-pitch>
profile: <傳產中小 | 大型科技廠 | 公部門 | 新創>
audience: <工廠長 | IT主管 | CFO | 老闆 | other>
status: draft
---

# <客戶名> deck storyline

> 這份是 storyline，不是 deck。寫完跑 `/slide-office-hours` review，簽核後才動 slide。
> AI 不會替你寫這份的內容 — 那是這個 skill 故意設計的失敗模式。

## Exit criteria

這場聽完，客戶該做什麼動作？具體到「**什麼人、做什麼、什麼時候**」三件事都齊。

不能寫的：
- ❌「讓客戶了解我們」
- ❌「建立關係」
- ❌「展示能力」

可以寫的（範例）：
- ✅「IT 主管下次帶研發主管一起見，兩週內」
- ✅「客戶承諾給我們三個月份的設備 log 樣本，會後三天內」
- ✅「客戶內部 review 後決定是否進 Discovery Workshop，月底前」

<在這裡寫>

## Organizing structure

選一個結構並命名。每個 operator 猜題都要對到結構的一格。

範例：
- 三層架構（基礎建設層 / 預測層 / 決策層）
- 四大面向（業務 / 製造 / 廠務 / 工安）
- 五階段 funnel（Discover / Define / Develop / Deliver / Decide）

**選擇理由**：為什麼選這個結構？跟客戶熟悉的 mental model 對不對得上？

<在這裡寫>

## Operator-level 猜題（≥3 個，不准抄公開資料）

> 對客戶的**生產製程 / 業務流程**最大膽的猜測。猜錯客戶會修正你 = 免費 Discovery。
>
> ❌ 不可以是「依公開資料 / 業界趨勢顯示 / 市場研究指出」這種 voice
> ❌ 不可以是「我們也能做 X」這種 capability claim
> ✅ 要是「**我猜你的 [流程/系統/部門] 是這樣運作的：...**」

1. <你猜客戶的 X 流程是這樣運作的：...>
2. <你猜客戶的 Y 部門是這樣決策的：...>
3. <你猜客戶的 Z 系統現在最大痛點是：...>

**（科技廠專用）每條 operator 猜題的 cross-customer pattern 支撐**：

| # | 猜題 | 來自哪個 cross-customer 經驗 / cross-industry pattern |
|---|------|----------------------------------------------------|
| 1 | ... | <例：在 [其他客戶] 看過類似的問題，模式是 X> |
| 2 | ... | <例：[相鄰產業] 的 [流程] 通常會遇到這個 trade-off> |

（傳產中小 / 公部門 / 新創 可省略此表）

## 差異化角度（科技廠 / 競標案 / final-pitch 必填）

- **differentiation_target**: <同業 ASE / Amkor | 顧問業 Accenture / Deloitte | 雲端商 AWS / GCP | 客戶內部 AI team | 其他具體名稱>
- **我比 [target] 強在哪**：<一句話，要具體不要空話>
- **證據**：<case ref / cross-customer pattern / 跨集團資源 / 實際 demo>

> ⚠️ 「市場領先 / 技術強 / 全方位服務」= 空話，這格寫這種 = ❌

<在這裡寫>

## 5 個不能錯的基本事實

客戶業務常識性事實，搞錯一條當場 burn credibility。每一條附 source。

| # | 事實 | source |
|---|------|--------|
| 1 | <例：光泉有自家牧場 + 契作酪農，不是純契作> | <URL / 文件 / 內部 ref> |
| 2 | ... | ... |
| 3 | ... | ... |
| 4 | ... | ... |
| 5 | ... | ... |

## Stage-specific 補充

### first-call
（無額外要求 — operator_guesses ≥ 3 已涵蓋）

### post-discovery
**Discovery learned X, proposal changed to Y**：

| Discovery 學到 | 因此提案改成 |
|---------------|------------|
| <例：客戶其實沒有 SCADA，是 Excel 手動> | <把 IoT 整合那段拿掉，先做 OCR + Excel pipeline> |
| ... | ... |

### proposal
- **Scope 紅線**：<什麼一定不做 / 不能做>
- **退場機制**：<在什麼條件下我們可以停損 / 客戶可以中止>

### final-pitch
**為什麼選我們不選 [具體對手名]**：

| 對手 | 客戶可能擔心對手什麼 | 我們的具體答覆 |
|------|--------------------|--------------|
| <例：ASE> | 規模大但反應慢 | 我們專案 PM 直接對接客戶研發，無轉手 |
| <例：客戶自建 team> | 自己做才安全 | 我們做完 transfer 不留 lock-in，三個月 handover |

## 不放進 deck 的東西（避免 scope creep）

明確列出捨棄的方向，避免後面動工時又想塞回去。

- ❌ <例：不放公司歷年得獎 — 客戶不在乎>
- ❌ <例：不放完整 case study list — 太長，挑 2 個最相關的就好>
- ❌ ...

## 投影片骨架（粗略，不寫內容）

| # | type | title | 對應上面哪一塊 |
|---|------|-------|---------------|
| 1 | cover | <客戶名> × <我們> | - |
| 2 | agenda | 今天三件事 | organizing structure |
| 3 | context | 我們對你的初步理解 | operator猜題 1 |
| 4 | guess | 我們猜你的 X 流程 | operator猜題 1 |
| 5 | guess | 我們猜你的 Y 決策 | operator猜題 2 |
| 6 | guess | 我們猜你的 Z 痛點 | operator猜題 3 |
| 7 | how | 如果猜對了，我們怎麼幫 | solutions |
| 8 | diff | 為什麼是我們 | differentiation（科技廠 / 競標）|
| 9 | next | 下一步 | exit criteria |

骨架可調，但每一頁都要對應上面的某一塊 — 沒對到的頁 = 砍掉。
