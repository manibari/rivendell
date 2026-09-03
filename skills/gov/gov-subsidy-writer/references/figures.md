# 計畫書圖檔製作 (SoT)

> Origin: 2026-07 數產署 DFM 案的 4 張圖 + v4 補件的官方格式計畫架構圖。
> 補助計畫書的圖是**文件插圖**，不是簡報視覺圖，也不是工程架構圖 —— 兩者的比例、
> 用色、體例都不同。做法：HTML 寫版 → headless Chrome 截圖 → 內嵌 docx。

## 兩種圖，分清楚

補助計畫書會用到兩類圖，體例相反，不要混：

1. **官方格式圖（黑白 WBS 體例）** —— 計畫架構圖。委員拿它對經費占比、對預定
   進度表。純黑白線框、樹狀結構、無彩色無底圖。見下方模板。
2. **說明性視覺圖（低彩、文件插圖）** —— 系統功能架構、部署架構、甘特。幫委員
   看懂「這東西怎麼運作」。可低彩度上色，但仍是報告插圖，不是 pitch slide。

## 文件插圖比例（關鍵，反覆踩坑）

計畫書內嵌圖是 A4 直書文件裡的橫幅插圖，**不是 16:9 slide**。

- 說明性視覺圖：**寬 1600px、高 620–740px**（實測 DFM 四圖：功能架構 620、
  部署 660、甘特 720、計畫架構 740）。插入 docx 約 16.5cm 寬。
- 官方 WBS 計畫架構圖：更接近方形（實測 1448×1086 ≈ 4:3），因為樹狀分支要往下
  長。插入時等比縮到頁寬。
- 拿 1600×900 的 slide 圖塞進 A4 →上下大片留白。**重出圖，不要縮放**。
- docx 內嵌用 `fig(file, hpx, caption)` helper（見 `assets/build-template.js`），
  caption 格式「圖 N　標題」（全形空格分隔）。

## 官方格式計畫架構圖 —— HTML 骨架

黑白樹狀 WBS：計畫名稱（直書）→ 主幹 → 分項（帶權重）→ 分支 → 工作項目
（帶執行/驗證單位）。這張圖是**連動網的視覺版**：每個工作項目的名稱與權重必須
與內文分項說明、預定進度表、經費表完全一致（見 writing-rules 規則 11）。

```html
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { width:1150px; height:900px; background:#fff;
         font-family:"PingFang TC","Microsoft JhengHei","Noto Sans TC",sans-serif; color:#000; }
  .page { width:1150px; height:900px; padding:20px 26px 26px; display:flex; align-items:stretch; overflow:hidden; }
  /* 左：計畫名稱直書 */
  .plan-col { flex:0 0 78px; display:flex; flex-direction:column; }
  .plan-box { flex:1; border:1.6px solid #000; padding:12px 6px; writing-mode:vertical-rl;
              font-size:18px; line-height:1.3; display:flex; align-items:center; justify-content:center; }
  .plan-w { margin-top:6px; font-size:15px; white-space:nowrap; }
  /* 主幹與分支：純線框 */
  .trunk { flex:0 0 40px; position:relative; }
  .trunk .spine { position:absolute; left:50%; width:1.6px; background:#000; }
  .subs { flex:1; display:flex; flex-direction:column; justify-content:space-between; }
  .sub-row { display:flex; align-items:center; }
  .sub-col { flex:0 0 300px; position:relative; }
  .sub-col::before { content:""; position:absolute; left:-40px; top:50%; width:40px; height:1.6px; background:#000; }
  .sub-box { border:1.6px solid #000; padding:11px 12px; font-size:18px; }
  .sub-w { position:absolute; top:100%; left:3px; margin-top:5px; font-size:15px; }
  .branch { flex:0 0 34px; position:relative; align-self:stretch; }
  .branch .spine { position:absolute; left:0; width:1.6px; background:#000; }
  .items { flex:1; display:flex; flex-direction:column; gap:12px; }
  .item { display:flex; align-items:center; position:relative; }
  .item::before { content:""; position:absolute; left:-34px; top:50%; width:34px; height:1.6px; background:#000; }
  .item-box { flex:0 0 330px; border:1.6px solid #000; padding:9px 12px; font-size:17px; }
  .unit { margin-left:14px; font-size:15px; white-space:nowrap; }
</style>
<div class="page">
  <div class="plan-col">
    <div class="plan-box">{{計畫名稱}}</div>
    <div class="plan-w">權重：100%</div>
  </div>
  <div class="trunk"><div class="spine" style="top:10%; bottom:14%;"></div></div>
  <div class="subs">
    <!-- 每個分項一個 .sub-row。權重＝經費占比，加總 100% -->
    <div class="sub-row">
      <div class="sub-col"><div class="sub-box">A. {{分項名稱}}</div><div class="sub-w">權重：35%</div></div>
      <div class="branch"><div class="spine" style="top:19%; bottom:19%;"></div></div>
      <div class="items">
        <!-- 每個工作項目標執行單位；有引進/委外/驗證才加第二行 -->
        <div class="item"><div class="item-box">A1. {{工作項目}}</div><div class="unit">執行單位：{{公司}}</div></div>
        <div class="item"><div class="item-box">A2. {{工作項目}}</div><div class="unit">執行單位：{{公司}}<br>無形資產引進：{{項目}}</div></div>
      </div>
    </div>
    <!-- B、C、D 分項同上 -->
  </div>
</div>
```

配套的官方語言（放在圖前的內文）：

> 計畫架構如下圖，各分項計畫之比重依開發經費占總開發費用之百分比計算，分項計畫
> 與工作項目名稱與預定進度表所列一致。

## 說明性視覺圖的內容規則

（沿用全域 CLAUDE.md「Diagram & Slide Output Defaults」，補助案特化）

- **不同概念用不同盒＋不同色**：部署架構的「客戶廠內 vs 雲端」是兩個獨立盒不同
  色系（暖色/藍色），中軸標守門員（傳輸加密 / 圖資不外傳），不是共用邊框中間斷開。
- **委員白話**：功能架構圖的模組名用功能語（CAD 解析、知識庫、檢核引擎、報告
  介面），不放技術品牌（NGINX/Redis/port）。給工程師的技術圖跟給委員的圖是兩張。
- **資安貫穿條**：若有資安經費占比要求（如 ≥7%），圖底放一條資安橫條標占比，
  呼應經費表。
- **工作項目名稱一致**：計畫架構圖的 A1…D4 名稱 = 內文分項說明 = 甘特圖 = 經費
  表。改任一處先 grep 全文同步（連動網）。

## 截圖自檢流程（不可省）

寫完 HTML 不算完成，必須截圖 + 肉眼檢查：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --disable-gpu --window-size=<W+40>,<H+50> \
  --screenshot=/tmp/fig-check.png "file://<absolute-path>"
```

然後 Read PNG 檢查：(a) 沒切版/溢出 (b) 沒文字 wrap 成兩行 (c) 沒空白塊
(d) 樹狀線有接上盒子。發現問題就改 HTML 再截。沒截圖驗證過不算完成。
