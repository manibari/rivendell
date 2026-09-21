# knowledge/ — rivendell 知識庫

消化過的**外部內容**落地於此（git-tracked、可 grep、dashboard 可索引）。跟 `~/.claude/knowledge/`（`knowledge-graph` skill 存「人/公司/專案」實體事實）互補——這裡存「**這份內容講了什麼**」。

## 結構

```
knowledge/
├── content/
│   └── videos/                      # 影片摘要（video-transcript skill 產出）
└── entities/
    └── kg.py                        # 實體知識讀寫 API；資料仍在 ~/.claude/knowledge/
```

影片目錄內的檔案：

```
content/videos/
    ├── INDEX.md                     # 可瀏覽索引（save_note 自動重生；按日期排序 + 可信度）
    └── YYYY-MM-DD-<標題>/
        ├── note.md                  # frontmatter（title/url/source/reliability/date/tags）+ 摘要
        └── transcript.txt           # 完整逐字稿
```

**先看 `content/videos/INDEX.md`** 找筆記；它是從各 note.md frontmatter 衍生的視圖，`save_note.sh` 每次寫入自動重生。`knowledge/videos/` 暫時是指向同一目錄的相容連結。

未來可長 `knowledge/content/articles/`、`knowledge/content/papers/` 等同構子目錄。

## 怎麼寫入

`skills/knowledge/_shared/scripts/save_note.sh <transcript> <meta|-> <summary.md|->` 會自動存到這裡（預設路徑經相容連結指向 `content/videos/`）。`video-transcript` skill 抓完+摘要後呼叫它歸檔。實體事實由 `knowledge/entities/kg.py` 管理；`scripts/kg.py` 是既有 CLI 的相容連結。

## frontmatter 欄位

| 欄位 | 說明 |
|------|------|
| `reliability` | `manual subs`（可信）/ `auto-caption (rough)`（自動字幕）/ `asr (machine transcription)`（whisper 從音訊轉，專有名詞可能誤植）|
| `source` | youtube / bilibili / web |
| `tags` | 手動補主題標籤，方便日後 grep / dashboard 分類 |

**可信度標註很重要**：ASR / auto-caption 來源的精確人名、術語、數字請以原片為準。
