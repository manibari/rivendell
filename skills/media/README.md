# media/ — 影音抓讀 skill 群

一組處理「線上影音 → 可用產物」的 skill。共用同一套抓取引擎（yt-dlp），但**輸出型態各自不同**——這是它們各自成 skill、而非合成一個 skill 四個模式的理由。

| Skill | 輸入 | 輸出 | 何時用 |
|-------|------|------|--------|
| **video-transcript** | 影片 URL | **文字**（摘要／文章／逐字稿／翻譯） | 想「讀」影片內容 |
| **video-clip-extract** | 影片 URL + 時間範圍/主題 | **影片**片段 (.mp4) | 想剪一段精華 |
| **subtitle-file** | 影片 URL | **字幕檔** (.srt/.vtt，保留時間軸，可譯) | 想要能重新上傳/翻譯的字幕檔 |

判準：輸出型態不同 → 各自 skill；只是文字產物不同（摘要 vs 逐字稿）→ 同一 skill 的模式。
所以 video-transcript 內含四種文字模式，但「產影片」「產字幕檔」另立門戶。

## 共用引擎：`_shared/scripts/`

抓取的難處（metadata 探測、挑最佳字幕軌、429 退避重試、瀏覽器 impersonation）只寫一次，三個 skill 共用：

| 檔案 | 作用 |
|------|------|
| `media_fetch.sh` | 主抓取器。`yt-dlp -J` 探 metadata → `pick_track.py` 挑一軌 → 退避下載 → 清理。預設輸出純文字；`RAW=1` 輸出保留時間軸的 `.vtt` |
| `pick_track.py` | 從 metadata 挑**單一**最佳字幕軌（手動優先於自動；語言偏好序）。只下載一軌 = 避開多語言 429 連鎖 |
| `vtt_to_text.py` | VTT → 乾淨純文字（**去**時間戳、去滾動字幕重複）。給 video-transcript 用 |
| `vtt_to_srt.py` | VTT → 乾淨 SRT（**保留**時間戳、合併重複軌）。給 subtitle-file 用 |

### 為什麼 `_shared/` 用相對路徑能 work

rivendell 用 symlink 把每個 skill 部署到 `~/.claude/skills/`（`bin/sk deploy`）。`_shared/` 不是 skill（沒 SKILL.md），不會被單獨部署——但每個 skill 的 SKILL.md 用**實體路徑解析**定位它：

```bash
SKILL_DIR="$(cd -P "${CLAUDE_SKILL_DIR:-skills/media/<name>}" && pwd -P)"
SHARED="$SKILL_DIR/../_shared/scripts"
```

`cd -P` 會穿透 symlink 落回 repo 的實體位置，`../_shared` 就在那當兄弟目錄。⚠️ 限制：若哪天用「複製」而非 symlink 部署到沒有這個 repo 的機器，`_shared` 不會跟著走——屆時需改成各 skill 自帶 copy 或安裝時打包。目前 rivendell 全走 symlink-from-repo，沒問題。

## 前置工具

- `yt-dlp`（全部）：`brew install yt-dlp`；重度使用或常撞 429 改 `pipx install yt-dlp && pipx inject yt-dlp curl_cffi`（brew 版裝不了 impersonation 後端）
- `ffmpeg`（只有 video-clip-extract）：`brew install ffmpeg`
