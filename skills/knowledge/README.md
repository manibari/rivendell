# media/ — 影音抓讀 skill 群

一組處理「影音 → 可用產物」的 skill。線上的共用抓取引擎（yt-dlp）；本機檔案走 mlx-whisper ASR。**輸出型態各自不同**——這是它們各自成 skill、而非合成一個 skill 的理由。

| Skill | 輸入 | 輸出 | 何時用 |
|-------|------|------|--------|
| **video-transcript** | 影片 **URL** | **文字**（摘要／文章／逐字稿／翻譯） | 想「讀」線上影片內容（真字幕，比 ASR 準）|
| **local-media-transcribe** | **本機**影音檔 (.mov/.mp4/.m4a/.mp3) | **文字**（逐字稿／摘要／文章／翻譯）+ 螢幕錄影畫面說明 | 本機螢幕錄影／會議錄影／錄音聽寫並說明（離線 mlx-whisper）|
| **video-clip-extract** | 影片 URL + 時間範圍/主題 | **影片**片段 (.mp4) | 想剪一段精華 |
| **subtitle-file** | 影片 URL | **字幕檔** (.srt/.vtt，保留時間軸，可譯) | 想要能重新上傳/翻譯的字幕檔 |
| **yt-channel-scraper** | **訂閱清單**（頻道／UP 主／podcast） | **知識庫新筆記**（新片自動摘要存檔） | 想長期追蹤來源，而不是每次貼一條連結 |

判準：輸出型態不同 → 各自 skill；只是文字產物不同（摘要 vs 逐字稿）→ 同一 skill 的模式。
線上 URL vs 本機檔是**不同輸入源**（真字幕 vs ASR）→ video-transcript 與 local-media-transcribe 分立。
yt-channel-scraper 的輸入是**訂閱清單而非單一 URL**，它呼叫 video-transcript 的同一條管線做每一支片。

## 共用引擎：`_shared/scripts/`

抓取的難處（metadata 探測、挑最佳字幕軌、429 退避重試、瀏覽器 impersonation）只寫一次，各 skill 共用：

| 檔案 | 作用 |
|------|------|
| `media_fetch.sh` | 主抓取器。`yt-dlp -J` 探 metadata → `pick_track.py` 挑一軌 → 退避下載 → 清理。預設輸出純文字；`RAW=1` 輸出保留時間軸的 `.vtt` |
| `pick_track.py` | 從 metadata 挑**單一**最佳字幕軌（手動優先於自動；語言偏好序）。只下載一軌 = 避開多語言 429 連鎖 |
| `vtt_to_text.py` | VTT → 乾淨純文字（**去**時間戳、去滾動字幕重複）。給 video-transcript 用 |
| `vtt_to_srt.py` | VTT → 乾淨 SRT（**保留**時間戳、合併重複軌）。給 subtitle-file 用 |
| `audio_transcribe.sh` | **線上無字幕 fallback**：yt-dlp 抽音訊 → 16kHz wav → whisper.cpp 本地語音轉文字。模型首次自動下載。ASR 非人工字幕，較慢且會誤聽專有名詞 |
| `local_transcribe.sh` | **本機檔案轉錄**（local-media-transcribe 用）：ffmpeg 抽音 → 16kHz wav → **mlx-whisper**（Apple Silicon 原生、快、離線）。無音軌會明確報錯（螢幕錄影可能無聲）。`FORMAT=both` 另出 .srt 時間軸 |
| `save_note.sh` | **歸檔**：把 transcript + 摘要存進 `knowledge/videos/YYYY-MM-DD-<標題>/`（git-tracked 知識庫），note.md 帶 frontmatter，並自動重生 INDEX。根治「只讀不存」 |
| `build_index.py` | 掃 `knowledge/videos/*/note.md` frontmatter → 重生 `INDEX.md`（可瀏覽表格，按日期排序、標可信度）。save_note 每次自動呼叫，也可手動重跑 |
| `feed_items.py` | RSS/Atom → items。podcast 取 `<enclosure>` 音檔直連（不必播完整集）；YouTube 頻道 Atom 沒有 enclosure，取 watch 頁連結。給 yt-channel-scraper 用 |

yt-channel-scraper 自己的 `scripts/feed_scan.py` **不放 `_shared/`**——只有它一個消費者，放共用區會讓「共用」失去意義。它 import 上面的 `feed_items.py`。

### 為什麼 `_shared/` 用相對路徑能 work

rivendell 用 symlink 把每個 skill 部署到 `~/.claude/skills/`（`bin/sk deploy`）。`_shared/` 不是 skill（沒 SKILL.md），不會被單獨部署——但每個 skill 的 SKILL.md 用**實體路徑解析**定位它：

```bash
SKILL_DIR="$(cd -P "${CLAUDE_SKILL_DIR:-skills/knowledge/<name>}" && pwd -P)"
SHARED="$SKILL_DIR/../_shared/scripts"
```

`cd -P` 會穿透 symlink 落回 repo 的實體位置，`../_shared` 就在那當兄弟目錄。⚠️ 限制：若哪天用「複製」而非 symlink 部署到沒有這個 repo 的機器，`_shared` 不會跟著走——屆時需改成各 skill 自帶 copy 或安裝時打包。目前 rivendell 全走 symlink-from-repo，沒問題。

## 前置工具

- `yt-dlp`（全部）：`brew install yt-dlp`；重度使用或常撞 429 改 `pipx install yt-dlp && pipx inject yt-dlp curl_cffi`（brew 版裝不了 impersonation 後端）
- `ffmpeg`（video-clip-extract 與無字幕 fallback）：`brew install ffmpeg`
- `whisper-cpp`（線上無字幕 fallback `audio_transcribe.sh`）：`brew install whisper-cpp`；模型首次執行自動下載到 `~/.cache/whisper-cpp/`
- `mlx-whisper`（本機轉錄 `local_transcribe.sh`／local-media-transcribe，**僅 Apple Silicon**）：`pip install mlx-whisper`；模型首次執行自動下載到 HF cache
