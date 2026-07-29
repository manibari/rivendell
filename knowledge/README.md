# knowledge/ — rivendell 知識庫

消化過的**外部內容**落地於此（git-tracked、可 grep、dashboard 可索引）。跟 `~/.claude/knowledge/`（`knowledge-graph` skill 存「人/公司/專案」實體事實）互補——這裡存「**這份內容講了什麼**」。

## 結構

```
knowledge/
└── videos/                          # 影片摘要（video-transcript skill 產出）
    ├── INDEX.md                     # 可瀏覽索引（save_note 自動重生；按日期排序 + 可信度）
    └── YYYY-MM-DD-<標題>/
        ├── note.md                  # frontmatter（title/url/source/reliability/date/tags）+ 摘要
        └── transcript.txt           # 完整逐字稿
```

**先看 `videos/INDEX.md`** 找筆記；它是從各 note.md frontmatter 衍生的視圖，`save_note.sh` 每次寫入自動重生。

未來可長 `knowledge/articles/`、`knowledge/papers/` 等同構子目錄。

## 怎麼寫入

`skills/media/_shared/scripts/save_note.sh <transcript> <meta|-> <summary.md|->` 會自動存到這裡（預設路徑從 script 位置推回 repo root）。`video-transcript` skill 抓完+摘要後呼叫它歸檔。

## frontmatter 欄位

| 欄位 | 說明 |
|------|------|
| `reliability` | `manual subs`（可信）/ `auto-caption (rough)`（自動字幕）/ `asr (machine transcription)`（whisper 從音訊轉，專有名詞可能誤植）|
| `source` | youtube / bilibili / web |
| `tags` | 手動補主題標籤，方便日後 grep / dashboard 分類 |

**可信度標註很重要**：ASR / auto-caption 來源的精確人名、術語、數字請以原片為準。
