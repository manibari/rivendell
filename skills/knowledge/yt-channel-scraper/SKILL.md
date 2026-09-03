---
name: yt-channel-scraper
loop: knowledge
pdca: plan
description: >
  Subscribe to YouTube channels, Bilibili UP 主, and podcast shows, then sweep them for new
  episodes and auto-archive each one into the video knowledge base (transcript + 繁中重點摘要 in
  knowledge/videos/). The subscription list is a plain config file; discovery, de-duplication
  against already-archived notes, and per-run caps are handled by feed_scan.py so this skill spends
  its effort on reading and summarising.
  TRIGGER when: user wants to follow a source rather than a single link — "訂閱這個頻道", "追蹤這個
  UP 主", "有沒有新影片", "掃一下訂閱", "把新片都整理進知識庫", "subscribe to this channel",
  "check my subscriptions", "any new videos"; also when they paste a channel / space.bilibili.com /
  podcast-RSS URL (as opposed to a single video URL) and want ongoing coverage.
  DO NOT TRIGGER when: the user pastes ONE video URL and wants it read now (use video-transcript —
  this skill calls it internally, but for a single link the wrapper is pure overhead), wants a
  subtitle file (subtitle-file), a clip (video-clip-extract), or a local file transcribed
  (local-media-transcribe).
tags: [media, content, video, youtube, podcast, bilibili, subscription]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Channel Scraper — 訂閱與自動追蹤

Follow sources, not links. `feed_scan.py` answers "what's new that I haven't already archived";
you then run each queued item through the same fetch→summarise→archive path `video-transcript`
uses, and mark it done. Everything lands in `knowledge/videos/` — same vault, same INDEX.

**The division of labour matters**: the script owns everything deterministic (subscriptions,
feeds, de-duplication, state). You own the reading. Never hand-maintain the seen-set — call
`mark`, or the next run will re-summarise what you just archived.

## Locate the scripts

```bash
SKILL_DIR="$(cd -P "${CLAUDE_SKILL_DIR:-skills/knowledge/yt-channel-scraper}" 2>/dev/null && pwd -P)"
SCAN="$SKILL_DIR/scripts/feed_scan.py"
SHARED="$SKILL_DIR/../_shared/scripts"
```

## Step 0 — Which job is this?

| User says | Go to |
|---|---|
| 「訂閱 X」「追蹤這個頻道」 | Step 1 (add) |
| 「有沒有新的」「掃一下」「更新知識庫」 | Step 2 (scan) → Step 3 (process) |
| 「我訂了哪些」 | `python3 "$SCAN" subs` and stop |

## Step 1 — Add a subscription

```bash
python3 "$SCAN" add youtube  @mattpocockuk  "Matt Pocock"      # handle, channel URL, or UC… id
python3 "$SCAN" add bilibili 25876945       "极客湾"            # UP 主 uid or space URL
python3 "$SCAN" add podcast  https://lexfridman.com/feed/podcast/ "Lex Fridman"
```

Appends to `knowledge/videos/subscriptions.conf` (`NAME | KIND | SOURCE | LIMIT`). Editing that
file by hand is equally fine — it's the source of truth; the state file only remembers what's been
seen.

**A new subscription is seeded on its first scan, not backfilled** — everything currently in the
feed is marked seen and nothing is queued. This is deliberate: one active channel would otherwise
dump 15 videos into the auto-archive loop on day one. To take the newest few anyway:

```bash
python3 "$SCAN" scan --sub "Matt Pocock" --backfill 3
```

Tell the user which it was. 「已訂閱，之後只抓新片」 vs 「已訂閱並回補最新 3 支」 is exactly the
kind of thing they'll otherwise ask about.

## Step 2 — Scan

```bash
python3 "$SCAN" scan            # human-readable
python3 "$SCAN" scan --json     # {queue:[…], seeded:[…], errors:[…]} — use this to drive the loop
```

Each queue entry: `sub / kind / title / url / date / id / duration_sec`. Exit code is 1 if any
subscription errored — read `errors[]`, report it, and **carry on with the rest of the queue**;
one dead feed must not block the others.

**Before processing, check the size of the job.** Auto-archiving is the configured behaviour, but
it is not free — each item costs a fetch plus a summary, and a podcast costs a Whisper run on top.

- Queue ≤ 5 items → just do it.
- Queue > 5, or any podcast over ~90 min (`duration_sec`) → say what you found and how long it'll
  take, and confirm before grinding through it. Offer `scan --limit 1` to take just the newest from
  each subscription now (`--limit` overrides each sub's own cap — it is per subscription, not a
  total), and leave the rest for the next run.

## Step 3 — Process each item

Same pipeline as `video-transcript`, once per queue entry. **Do them one at a time**, and mark each
before starting the next — an interrupted run must not lose or repeat work.

### 3a. Get the text

**YouTube / Bilibili** (`kind: youtube | bilibili`) — real subtitles first:

```bash
bash "$SHARED/media_fetch.sh" "<url>" /tmp/ch-item.txt
# no subs? (Bilibili subs are often login-walled, which looks identical to "none"):
COOKIES=chrome bash "$SHARED/media_fetch.sh" "<url>" /tmp/ch-item.txt
# still nothing → ASR fallback
FALLBACK=whisper COOKIES=chrome WHISPER_LANG=zh bash "$SHARED/media_fetch.sh" "<url>" /tmp/ch-item.txt
```

**Podcast** (`kind: podcast`) — the queue url IS the audio enclosure, so skip yt-dlp entirely:

```bash
curl -fSL "<audio-url>" -o /tmp/ch-ep.mp3
bash "$SHARED/local_transcribe.sh" /tmp/ch-ep.mp3 /tmp/ch-item.txt   # mlx-whisper, offline
```

`local_transcribe.sh` writes no `.meta` sidecar, so build one before archiving — otherwise the note
loses its title and URL:

```bash
printf 'title: %s\nurl: %s\nlang: \nkind: asr\n' "<title>" "<page-or-audio-url>" > /tmp/ch-item.txt.meta
```

A 3-hour episode is a long Whisper run — start it with `run_in_background` and keep working.

### 3b. Summarise

Write **Mode 1 (重點摘要)** from `video-transcript` — BLUF first, 繁體中文, grounded strictly in the
transcript. The `**一句話**` line is not decoration: `build_index.py` lifts it verbatim into
`INDEX.md`, so it's the one sentence the user will actually re-read months later. Make it say what
the video *claims*, not what topic it covers.

```markdown
## 重點摘要：<標題>

**一句話**：<the core claim>

- <concrete point>
- <ordered by importance>
```

If the transcript came from auto-captions or ASR, say so in the summary and avoid exact quotes —
`save_note.sh` records the reliability flag, but a reader skimming the prose deserves the warning too.

### 3c. Archive and mark

```bash
bash "$SHARED/save_note.sh" /tmp/ch-item.txt /tmp/ch-item.txt.meta /tmp/summary.md
python3 "$SCAN" mark "<url>" --why archived --title "<title>"
```

`save_note.sh` regenerates `INDEX.md` itself. Marking is what keeps the next scan quiet.

### 3d. When an item fails

Don't leave it to be retried forever, and don't silently drop it:

```bash
python3 "$SCAN" mark "<url>" --why failed --title "<title>"    # 429, no audio, geo-blocked…
```

Then report the failures at the end. `--why skipped` is the same mechanism for "user said don't
bother with this one" (a livestream VOD, a 6-hour rerun).

## Step 4 — Report

BLUF: what got archived, what didn't, what's still waiting.

```
掃了 5 個訂閱 → 3 支新片，全部已存進 knowledge/videos/
  ✅ [Fireship] Did Anthropic just kill the indie hacker...?  (manual subs)
  ✅ [极客湾] 手机续航大横评                                    (ASR，術語以原片為準)
  ⚠️  [Lex] #499 Gary Gallagher — 3h53m，太長先跳過（--limit 不含）
```

`knowledge/` is git-tracked. Remind the user to commit if several notes landed — unlike `reports/`,
this vault is not owned by a scheduled agent, so nobody else will commit it for them.

## Managing subscriptions

```bash
python3 "$SCAN" subs                        # list + seed status + resolved channel ids
python3 "$SCAN" baseline --sub "极客湾"      # "I don't care about the backlog" — mark all seen
python3 "$SCAN" mark <url> --why skipped     # forget one item
```

To unsubscribe, delete or comment out the line in `subscriptions.conf`. The seen-set is left alone
on purpose — re-subscribing later won't re-archive the old episodes.

## Notes & gotchas

- **Bilibili blocks rapid space queries with HTTP 412.** Observed 2026-08-09: two `space.bilibili.com`
  listings inside a minute, and the second returns *"Request is blocked by server (412)"*. There is
  no retry that fixes it — wait. Practical consequences: don't loop `scan` while testing, keep
  Bilibili subs few, and treat a 412 in `errors[]` as "try the next run", not as a broken config.
- **The YouTube feed and the YouTube download have different rate limits.** Polling the Atom feed is
  a plain XML GET — it costs nothing and won't 429. The 429 risk lives entirely in Step 3a's
  subtitle download, so a big queue is what gets you blocked, not a big subscription list. If it
  hits, `COOKIES=chrome` is the fix that actually works (see video-transcript's gotchas).
- **De-dup reads the vault, not just the state file.** A note you archived by hand, or one that
  arrived via `git pull` from another machine, is recognised because `feed_scan.py` reads the `url:`
  frontmatter of every `knowledge/videos/*/note.md`. Consequence worth knowing: rename a note's
  folder freely, but don't strip its `url:` line or it'll come back as "new".
- **YouTube's feed only carries ~15 recent uploads.** A channel that posts 20 videos while you're
  away will silently lose the oldest few — they fall out of the feed before you scan. If that
  matters for a specific channel, scan more often; there's no deeper history in the feed to read.
- **Handles resolve once.** `@handle` → `UC…` costs one yt-dlp call, cached in
  `subscriptions-state.json`. If a creator changes their handle, the cached id still works — fix the
  config only if you want the file to read correctly.
- **Podcast enclosures are audio, so every podcast note is ASR** (🤖 in INDEX.md). Proper nouns will
  be wrong. `ASR_PROMPT="…"` on `local_transcribe.sh` biases decoding toward names you expect.

## Running it on a schedule (not wired up yet)

Deliberately manual for now — run it by hand a few times and confirm the feeds parse and dedupe
correctly before letting it write to git unattended. When ready, it follows the same shape as the
other rivendell agents:

1. Add `bin/sk-channel-scrape-cron` (mirror `bin/sk-harvest-cron`) invoking this skill headless.
2. Add to `agents/agents.conf`:
   ```
   com.sk.agent.rivendell.yt-channel-scraper | rivendell | bin/sk-channel-scrape-cron | calendar | 9:00 | reports
   ```
3. `./bin/sk agent start yt-channel-scraper` to generate the plist and load it.

Two things to settle before that switch: committing the new notes (`./bin/sk agent commit
yt-channel-scraper` exists for exactly this — an agent that writes to a git-tracked vault and never
commits leaves the repo permanently dirty), and a hard per-run item cap so one busy day can't
produce a 20-video run.
