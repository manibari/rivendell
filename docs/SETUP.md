# Rivendell setup guide

For onboarding a colleague or setting up rivendell on a new machine.

---

## What rivendell is (and isn't)

**Rivendell is**: a curated library of file-based Claude Code skills (~90), launchd agents that automate parts of the Claude Code workflow, and a dashboard at `localhost:3000` that gives observability over both.

**Rivendell is NOT**: Claude Code itself. Claude Code (the `claude` CLI) ships independently from Anthropic. You install it once, separately, and rivendell runs on top.

### About "built-in" skills

When you run `claude` and look at available skills, you'll see ~16 skills that **are not in this repo**:

- `update-config`, `fewer-permission-prompts`, `simplify`, `loop`, `schedule`, `keybindings-help`, `claude-api`, `batch`, `claude-in-chrome`, `debug`, `dream` — these are all skills compiled into the `claude` binary itself.
- `/init`, `/init-verifiers`, `/insights`, `/review`, `/commit` — same thing, but registered as slash commands rather than skills.

They're real, they work, they auto-update with each Claude Code version bump. **You can't find them in `skills/` because there's no SKILL.md file** — Anthropic ships them as compiled JS inside the `claude` binary.

The dashboard now surfaces them under `category: builtin` so they appear alongside file-based skills. **The most useful ones to know about**:

| skill | why it matters |
|---|---|
| `update-config` | The only way to set hooks (auto-behaviors). Memory/preferences cannot enforce "from now on every X do Y" — only hooks in `settings.json` can, and `update-config` is how you write them. |
| `fewer-permission-prompts` | Auto-allowlist common read-only commands so Claude Code stops asking permission for every `grep` / `ls`. |
| `/insights` | Per-session usage report (which skills fire most, where time goes). |
| `/init-verifiers` | Auto-create verifier skills for a project. |

To see the full inventory of built-ins on your machine:

```bash
strings $(which claude) | grep -oE 'T\$\(\{name:"[a-z][a-z0-9-]+"' | sort -u
strings $(which claude) | grep -oE '\{type:"prompt",name:"[a-z][a-z0-9-]+"[^}]+source:"builtin"' \
  | grep -oE 'name:"[^"]+"' | sort -u
```

This list grows with each Claude Code upgrade — re-run after upgrading.

---

## Deploy on a new machine

### 1. Install Claude Code first

Follow Anthropic's installer. Verify:

```bash
which claude        # should print a path
claude --version    # should print a version
```

Without this, nothing else works — rivendell is built on top.

### 2. Clone rivendell

```bash
git clone <rivendell-repo-url> ~/Documents/Projects/rivendell
cd ~/Documents/Projects/rivendell
```

The path matters — agents.conf and launchd plist templates assume `~/Documents/Projects/<project>`. If you put it elsewhere, you'll need to adjust those.

### 3. Deploy skills + agents

For a fresh machine, the **full bootstrap** is recommended — installs rivendell skills + agents + external skill packs (gstack) + Docker services in one go:

```bash
./bin/sk bootstrap dev-full     # full dev machine (macOS)
./bin/sk bootstrap minimal      # rivendell + gstack only, no extra projects
./bin/sk bootstrap --dry-run dev-full   # preview without changing anything
```

Or run the individual steps manually:

```bash
./bin/sk deploy                 # symlink rivendell skills + install plists
./bin/sk-setup-agents           # activate launchd agents
```

`sk deploy` only handles **rivendell's own** skills (`skills/<cat>/<name>/` → `~/.claude/skills/<name>`). External skill packs (gstack, defined in `profiles/profiles.conf` as `external_skill_pack` entries) are installed only via `sk bootstrap`. Re-run `sk bootstrap` on an existing machine to pick up new packs.

External skill packs are git-cloned into `~/.claude/skills/<NAME>` and their `SETUP_CMD` is invoked. If the target is a symlink (typical for a dev copy of gstack pointing at `~/Documents/Projects/gstack`), bootstrap **skips** it — your dev install stays intact.

Verify launchd agents:

```bash
launchctl list | grep com.sk
# Should show ~15 services: harvest, maintain, tester, dashboard.api, dashboard.web, etc.
```

### 4. Set up the dashboard

The dashboard is two services:

- **api (port 8000)**: Python FastAPI at `dashboard-next/api/`
- **web (port 3000)**: Next.js at `dashboard-next/`

Install Python deps:

```bash
cd dashboard-next/api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ../..
```

Build the web frontend (use `--webpack`, see "Gotchas" below):

```bash
cd dashboard-next
npm install
npx next build --webpack
cd ..
```

The `dashboard.api` and `dashboard.web` launchd services should already be running from step 3. Verify:

```bash
curl -s -o /dev/null -w "api 8000: %{http_code}\n" http://127.0.0.1:8000/api/skills
curl -s -o /dev/null -w "web 3000: %{http_code}\n" http://127.0.0.1:3000/
# both should return 200
```

Open `http://localhost:3000` in a browser.

### 5. Optional: install Python utilities

```bash
pip install pyyaml requests
npm install -g agent-skills-cli  # only if you want `./bin/sk import` to work
```

---

## Gotchas

### Turbopack chunk-write race (Next.js 16.x)

Default `next build` uses Turbopack. Turbopack in 16.1.6 has a known race that produces broken `.next/` cache (`.js.map` written but `.js` missing). Symptom: web returns 500 with `Cannot find module ... .next/server/chunks/ssr/...`.

**Fix**: build with webpack instead.

```bash
cd dashboard-next
rm -rf .next node_modules/.cache
npx next build --webpack
launchctl kickstart -k gui/$UID/com.sk.dashboard.web
```

Slower than Turbopack but reliable. Update `package.json` build script if you want this default:

```json
"build": "next build --webpack"
```

### `.next/` cache poisoning

If `npm run build` is killed mid-flight (Ctrl+C, OOM, launchd grace expiry), the `.next/` directory ends up half-built — `BUILD_ID` written, chunks missing. Web 500s on every request afterward.

**Fix**: `rm -rf .next && npx next build --webpack`. The watchdog can detect the symptom (HTTP 500) but `launchctl kickstart` alone won't fix it — bad caches need cache invalidation, not process restart.

### `stats-cache.json` no longer maintained

Older Claude Code versions wrote `~/.claude/stats-cache.json` — usage telemetry. Recent versions stopped. Rivendell's dashboard used to read it; this caused multi-month gaps in the daily usage chart.

**Fix is in place**: `dashboard/lib/tokens.py` now reads `~/.claude/projects/*.jsonl` exclusively, with `bin/sk-token-snapshot` persisting daily totals to `data/rivendell.db` so they survive Claude Code's JSONL rotation (~5 weeks). Nothing for you to do — just be aware that `stats-cache.json` may exist on your machine but is irrelevant.

### IPv4 vs IPv6 listener conflicts

Both api and web bind IPv6 (`*:port`) by default. If you have Docker Desktop running with stale containers also bound to those ports, browsers may hit the Docker container instead and you'll see "Failed to fetch" errors with no obvious cause. Check:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:3000 -sTCP:LISTEN
docker ps -a --format '{{.Names}} {{.Ports}}' | grep -E ':8000|:3000'
```

If Docker has port-publishing on these, stop the offending containers.

### Path encoding for Claude Code session jsonl

Claude Code stores session logs at `~/.claude/projects/-Users-<you>-Documents-Projects-<repo>/`. The dir name is the absolute path with `/` replaced by `-`. The dashboard parses these. If the colleague has rivendell at a non-standard path (e.g. `~/code/rivendell`), the dashboard's project-name extraction may misattribute tokens. Keeping rivendell at `~/Documents/Projects/rivendell` avoids this.

---

## Verifying the install

After everything's set up, run:

```bash
./bin/sk list                                       # should show ~90 skills across 7 categories
launchctl list | grep com.sk | wc -l                # should be ~15
curl -s http://127.0.0.1:8000/api/skills | python3 -c \
  'import json,sys; d=json.load(sys.stdin); print(f"{len(d)} skills, {sum(1 for s in d if s[\"category\"]==\"builtin\")} built-in")'
# should print ~144 skills, 16 built-in
```

If the built-in count is 0, the dashboard can't find `claude` on PATH. Check `which claude` returns a path the api process can also see.

---

## What to tell a colleague joining the project

Short version:

> Rivendell is a Claude Code skill library + dashboard. To onboard:
> 1. Install Claude Code from Anthropic
> 2. Clone rivendell at `~/Documents/Projects/rivendell`
> 3. `./bin/sk deploy && ./bin/sk-setup-agents`
> 4. Build dashboard: `cd dashboard-next && npm install && npx next build --webpack`
> 5. Open http://localhost:3000
>
> Full setup notes: `docs/SETUP.md`. The dashboard's "Built-in" category at the bottom is for skills compiled into the `claude` binary itself — they're not in this repo but you can use them like any other skill (`/update-config`, `/fewer-permission-prompts`, etc.).

---

## Personal assistant channels (`sk dispatch` / mail-triage)

一次性設定，全部憑證放 repo 外的 `~/.config/rivendell/`（勿 commit）：

```bash
cp ~/.config/rivendell/secrets.env.example ~/.config/rivendell/secrets.env
chmod 600 ~/.config/rivendell/secrets.env
```

### Gmail（寄信 + 讀信共用一組）
1. Google 帳戶 → 安全性 → 兩步驟驗證 → 應用程式密碼 → 產生一組
2. 填入 `RIVENDELL_GMAIL_USER` / `RIVENDELL_GMAIL_APP_PASSWORD`
3. 驗證：`python3 scripts/fetch-mail.py --max 3`（唯讀）；
   `echo '{"to":["自己"],"subject":"test","body":"hi"}' | python3 scripts/send-mail.py --payload -`

### Telegram 推播
1. @BotFather 建 bot 拿 token → 填 `RIVENDELL_TG_BOT_TOKEN`
2. 跟 bot 說句話，開 `https://api.telegram.org/bot<token>/getUpdates` 找 chat id → 填 `RIVENDELL_TG_CHAT_ID`
3. 驗證：`bash scripts/tg-notify.sh "hello"`

### Google Calendar（OAuth，一次性授權）
1. GCP Console → 建 OAuth client（類型 **Desktop app**）→ 把 client_id/client_secret 存成
   `~/.config/rivendell/gcal-credentials.json`：`{"client_id":"...","client_secret":"..."}`
2. `python3 scripts/gcal.py auth` → 瀏覽器授權 → token 自動存檔
3. 驗證：`echo '{"summary":"test","start":"2026-09-01T10:00:00","end":"2026-09-01T11:00:00"}' | python3 scripts/gcal.py create-event --payload -`

### 隱私注意
mail-triage 報告（`reports/mail-triage-*.md`）與 dispatch 的 email payload 含信件內容，
會進 git。repo 若推遠端請先確認你能接受，或把 remote 保持 private。

### 安全模型（速記）
- 模型只產提案 JSON；寄信/建事件由確定性 actuator 在你逐件確認後執行
- email/calendar 逐件 typed-yes；垃圾信移 Trash 批次 yes（30 天可救回）；永久刪除程式碼不存在
- 業務行為（客戶信件/報價/會議）一律 `crm` 型交接 Rightek-CRM，dispatch 不自行處理
- 憑證只有 actuator 進程讀得到；headless agent 的 readonly 工具組摸不到 `~/.config/rivendell/`

---

## 助理 Avatar（/avatar 頁 + gateway）

- `localhost:3000/avatar`：選人格（林迪/米瑞爾）→ VRM 對話視窗（麥克風要允許，瀏覽器 STT/TTS 繁中）
- 大腦：`com.sk.gateway`（:8310，127.0.0.1 only，**不可 tunnel 對外**）。引擎預設 codex
  （ChatGPT OAuth 額度），可在畫面切 claude / openai-api / anthropic-api；API 金鑰在畫面輸入，
  存 `~/.config/rivendell/gateway-keys.env`（chmod 600）
- 對話模型零工具；要辦事只會開 `sk dispatch` 提案（--source avatar），確認分級照舊
- VRM 模型是佔位樣本（見 `dashboard-next/public/avatar/models/README.md`，.vrm 不進 git，
  換機重抓或換自製模型）；神經語音（正式 TTS）列後續
