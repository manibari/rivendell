# Learnings Classification

## Summary
- 🌍 Generic: 24 entries → distilled into ~14 rules
- 🏛️ Rivendell-meta: 17 entries
- 🏠 Project-specific: 67 entries
- 🗑️ Drop: 17 entries

Total accounted: 125 entries (excludes 5 header-only ENTRY blocks that contain only `# Learnings` or similar).

---

## 🌍 Generic (24) — proposed for ~/.claude/CLAUDE.md

Grouped by theme. Each group merges duplicates into a single proposed rule.

---

### Group A — "Port is listening ≠ project is running; never grab default ports blindly"

Merges 4 entries:
- [ChimesFlow] Don't equate "port is listening" with "this project is running"
- [lorien] correction: Don't use default ports without asking
- [rivendell] 2026-04-01 Always check port map before starting a dev server
- [rivendell] 2026-05-07 Long-running `next-server` on port 3000 won't pick up source edits (the dev-vs-prod-mode-shadowing variant)

- **Why generic**: Multi-project dev machines guarantee port collisions; the "is X running" verification flaw recurs across every JS/Python stack.
- **Proposed CLAUDE.md rule**:
  > Before starting any dev server or claiming "project X is running":
  > 1. `lsof -nP -iTCP:<port> -sTCP:LISTEN` and inspect COMMAND. `next-server` (no `dev`) means production — won't hot-reload.
  > 2. For each candidate PID also check `lsof -p <pid> | grep cwd` + `ps -p <pid> -o command=` to confirm it's actually this project, not a neighbor.
  > 3. If the project has no assigned port, ask the user — don't default to 3000/8000.

---

### Group B — "Trust the error message and per-line timestamps; verify against ground truth, not in-memory counters"

Merges 3 entries:
- [ChimesFlow] Read the error message before touching anything (browser cache vs server state)
- [news_stock] MOPS scraper "in-memory counter said 106; DB had 20" — trust DB counts
- [rivendell] stats-cache.json freezes; trust per-line JSONL timestamps not file mtime

- **Why generic**: All three are the same anti-pattern: trusting derived/cached/in-process state instead of the source of truth.
- **Proposed CLAUDE.md rule**:
  > Evidence beats inference. When verifying state: (a) read the error message literally before guessing; (b) query the source of truth (DB COUNT, per-line timestamps) not in-memory counters or cached stats files; (c) if a cache file's mtime is suspiciously old while the underlying data is active, treat the cache as deprecated and re-derive from source.

---

### Group C — "Use the lockfile-correct package manager; verify auto-import names; check version-specific config"

Merges 4 entries:
- [news_stock] web/ 用 pnpm 而非 npm
- [news_stock] Nuxt 3 component auto-import de-duplication (blank page if wrong)
- [news_stock] Nuxt 3 auto-import prefixes nested components
- [lorien]+[rakucamp] Next.js 14 doesn't support next.config.ts; Next.js version dictates config extension; Noto_Sans_TC next/font fails

- **Why generic**: JS frameworks have version-gated and convention-driven behavior that silently breaks builds or renders blank pages.
- **Proposed CLAUDE.md rule**:
  > For JS projects: (a) detect package manager from lockfile (`pnpm-lock.yaml` → pnpm, `package-lock.json` → npm, `yarn.lock` → yarn) before installing; (b) for Nuxt 3 verify component names in `.nuxt/components.d.ts` when a page renders blank; (c) before scaffolding Next.js config check the Next major version — `next.config.ts` requires Next ≥ 15.

---

### Group D — "Load .env with dotenv; pydantic-settings doesn't populate os.environ"

Merges 2 entries:
- [lorien] os.environ.get() doesn't read .env files
- [lorien] best_practice: Always use dotenv for .env loading in FastAPI

- **Why generic**: pydantic-settings `env_file=` only fills its Settings object; any sibling code reading `os.environ.get()` won't see the vars.
- **Proposed CLAUDE.md rule**:
  > In FastAPI / Python projects that mix pydantic-settings with direct `os.environ.get(...)` calls, add `from dotenv import load_dotenv; load_dotenv()` at the top of `main.py`. pydantic-settings does NOT populate `os.environ`.

---

### Group E — "NEXT_PUBLIC_* is baked into the client bundle at build time"

Single entry:
- [ChimesFlow] Never pass NEXT_PUBLIC_API_URL=http://localhost when starting dev

- **Why generic**: Applies to every Next.js project; a single misuse contaminates the bundle for every remote user.
- **Proposed CLAUDE.md rule**:
  > `NEXT_PUBLIC_*` env vars are inlined into the client bundle at build time. Never set `NEXT_PUBLIC_API_URL=http://localhost:...` — it pins the bundle to loopback and breaks every non-local user (Private Network Access blocks). Use server-side env vars + Next.js rewrites instead.

---

### Group F — "Never partially delete `.next/*` or other persistent build caches"

Merges 2 entries:
- [ChimesFlow] Never partially delete `.next/*` (Turbopack cache rule)
- [rivendell] 2026-04-27 Half-built `.next` makes Next.js 500 on every request

- **Why generic**: Applies to any Next.js project using Turbopack.
- **Proposed CLAUDE.md rule**:
  > Treat `.next/` as atomic. Forbidden: `rm -rf .next/dev`, `rm -rf .next/cache`, etc. — partial deletion leaves Turbopack in an inconsistent state that surfaces as `ENOENT` / "Cannot find module ../chunks/ssr/[turbopack]_runtime.js". Only safe op: `kill -9 <next-pid>` → `mv .next .next.broken-$(date +%s)` → rebuild from scratch. Treat `.next/BUILD_ID` as a commit point: if a previous build was killed mid-flight, `BUILD_ID` may exist with missing chunks — always rebuild on suspect state.

---

### Group G — "Pin known-fragile Python/JS dep version combos"

Merges 3 entries:
- [lorien] passlib 1.7.4 + bcrypt 5.x incompatibility → pin bcrypt==4.2.1
- [lorien] openai SDK proxies conflict with httpx 0.28+ → upgrade openai
- [news_stock] FastAPI Query regex → pattern deprecation

- **Why generic**: Each is a recurring upgrade pitfall across Python web stacks.
- **Proposed CLAUDE.md rule**:
  > Known dep traps to watch for when a Python/FastAPI project breaks unexpectedly:
  > - `passlib` 1.7.4 + `bcrypt` ≥ 5.0 → pin `bcrypt==4.2.1`
  > - `openai` < 2.0 + `httpx` ≥ 0.28 → upgrade `openai` (proxies arg removed)
  > - FastAPI `Query(regex=...)` → use `Query(pattern=...)`
  > - sqlite3 Python 3.12+ → register adapters for `date`/`datetime` (default adapter deprecated)

---

### Group H — "Use case() not .cast(int) on SQLAlchemy 2.x boolean expressions"

Single entry: [lorien] SQLAlchemy 2.x `.cast(int)` on boolean fails

- **Why generic**: SQLAlchemy 2.x gotcha applies to any project using it.
- **Proposed CLAUDE.md rule**:
  > SQLAlchemy 2.x: `(col == val).cast(int)` fails with `AttributeError`. Use `case((col == val, 1), else_=0)` for boolean-to-int aggregation.

---

### Group I — "macOS launchd / TCC / sandbox quirks"

Merges 4 entries:
- [rivendell] macOS TCC blocks /bin/bash from ~/Documents/ in launchd
- [rivendell] launchd agents: cross-Documents source intermittently fails with EDEADLK
- [rivendell] 2026-05-13 dashboard-next is launchd-managed; use bootout/bootstrap not kill
- [rivendell] 2026-04-26 launchd KeepAlive only catches process death, not hangs

- **Why generic**: macOS-platform behavior, applies to any launchd-managed service. (The dashboard-specific bits are rivendell-meta; the underlying rules are generic.)
- **Proposed CLAUDE.md rule**:
  > macOS launchd rules:
  > - Scripts under `~/Documents/` need Full Disk Access; `/bin/bash` doesn't have it by default. Use a compiled C launcher granted FDA, not raw shell scripts.
  > - Cross-`~/Documents/` `source` under `set -euo pipefail` can hit EDEADLK; wrap with `set +e; source … || true; set -e`.
  > - `KeepAlive: true` only catches *process death*, not deadlocks. Pair with an HTTP-probe watchdog.
  > - For services owned by launchd, never `kill` the process — use `launchctl bootout` / `launchctl bootstrap` (or `kickstart -k`). A raw `kill` races with the respawn and corrupts on-disk caches.

---

### Group J — "git semantics under pipefail / set -e / hooks"

Merges 3 entries:
- [rivendell] 2026-04-22 `git log | head` under pipefail dies with exit 128
- [rivendell] 2026-04-21 Auto-stage PostToolUse hook silently stages files
- [rivendell] 2026-03-24 Autoresearch discard must NOT use git clean

- **Why generic**: Each is a git/shell semantics rule that applies anywhere.
- **Proposed CLAUDE.md rule**:
  > Git + shell safety:
  > - Any `$(git … 2>/dev/null | …)` under `set -o pipefail` must end with `|| echo ''` — git exits 128 on empty-HEAD repos and the pipeline propagates failure.
  > - Before every `git commit`, run `git diff --cached --name-only` as its OWN command (not `&&`-chained) — auto-stage hooks may have queued unrelated files.
  > - Never use `git clean -fd` for "discard changes" — it deletes untracked files belonging to other agents/processes. Use `git checkout -- .` only.

---

### Group K — "Diff before clobber when migrating from copy to symlink"

Single entry: [rivendell] 2026-04-28 Diff-before-replace symlinks

- **Why generic**: Applies to any "switch from copy-deployment to symlink-deployment" migration.
- **Proposed CLAUDE.md rule**:
  > When a maintenance script enforces "this path should be a symlink to X" and the path is currently a real directory, run `diff -rq <source> <target>` first. No output → safe to replace. Any output → leave alone, log as DIVERGED. Never auto-clobber divergence.

---

### Group L — "HTTP scrapers must disable auto-follow-redirect; SSL on TW gov sites is broken"

Merges 3 entries:
- [news_stock] 2026-05-08 Disable HTTP client auto-follow redirect
- [news_stock] 2026-04-23 MOPS TW gov TLS cert "Missing Subject Key Identifier"
- [sales-assistant] 2026-05-11 WebFetch failed for .tw gov sources (TLS / anti-bot)

- **Why generic**: TW gov endpoints recur; the redirect rule is universal.
- **Proposed CLAUDE.md rule**:
  > Scraper defaults:
  > - Disable auto-follow redirect — `requests.post(..., allow_redirects=False)`, `fetch(url, {redirect: 'manual'})`. Many endpoints throttle via 307 → redirect to a 200 OK homepage; auto-follow silently swallows the failure.
  > - For older TW gov endpoints (`mopsov.twse.com.tw`, etc.) requests/urllib3 may reject the cert with "Missing Subject Key Identifier". Acceptable to set `verify=False` for public read-only endpoints.
  > - For WebFetch quota: schedule fetches in batches; resets at 00:00 Asia/Taipei.

---

### Group M — "Cross-machine reproducibility: data coverage diffs, not 'works on my machine'"

Single entry: [news_stock] 2026-04-20 跨電腦 rotation 回測結果不同 → 單一 symbol 缺失

- **Why generic**: Applies any time results differ across environments — the diagnostic recipe (per-symbol coverage check, not aggregate counts) generalizes.
- **Proposed CLAUDE.md rule**:
  > When the same code + same params produces different results across machines, don't trust aggregate "is the DB healthy" checks. Compare per-key coverage (`SELECT COUNT(*) WHERE key=?` per candidate). A single missing row in one corner of the dataset is a common silent root cause.

---

### Group N — "Validate JS syntax for inline scripts in single-page mockups; regex literal `/` must be escaped"

Single entry: [綻放計畫] JS regex literal `/` 整頁空白

- **Why generic**: Applies to any prototype/inline JS without build step.
- **Proposed CLAUDE.md rule**:
  > For inline JS in HTML mockups without a build step: after every edit run `node -e 'new Function(`<code>`)'` to catch SyntaxError before browser load. In regex literals `/` must be `\/` or use `new RegExp("...")`. A whole-page blank with `[x-cloak]` showing usually means JS failed to parse.

---

### Group O — "Schema-aware before writing SQL; symbol/key conventions differ across tables"

Merges 2 entries:
- [news_stock] 2026-05-07 對 finance.db 寫 SQL 前先 `.schema`
- [news_stock] 2026-04-25 Symbol convention mismatch (2330.TW vs 2330)

- **Why generic**: First-cross-table-SQL discipline applies anywhere with multi-table joins.
- **Proposed CLAUDE.md rule**:
  > Before writing the first cross-table query against a database, run `.schema <table>` (or equivalent) for each table — don't trust naming conventions across tables. Common gotcha: time columns are named differently (`report_date` vs `year_month` vs `date`), and symbol/key conventions can differ (yfinance `2330.TW` vs MOPS `2330`). Normalize at the service boundary, not deep in queries.

---

### Group P — "Verify 'public knowledge' identifiers against the API before persisting"

Single entry: [news_stock] 2026-04-28 TW company tax IDs from "public knowledge" are unreliable

- **Why generic**: Applies to any seed data sourced from LLM memory.
- **Proposed CLAUDE.md rule**:
  > Never persist identifiers (tax IDs, company IDs, ISINs, etc.) recalled from training data without round-tripping each one through the authoritative API and confirming the returned name matches. Even "well-known" IDs have a ~60% miss rate. Record verification timestamp in the seed file.

---

### Group Q — "Browser sees 'Failed to fetch' but curl sees 200 = IPv4/IPv6 dual-listener or preflight"

Single entry: [rivendell] 2026-04-23 macOS Failed to fetch debug checklist

- **Why generic**: Applies to any macOS dev box running both Docker port-publish AND a local server.
- **Proposed CLAUDE.md rule**:
  > When browser shows "Failed to fetch" but curl returns 200, run the full debug checklist:
  > 1. `lsof -nP -iTCP:<port> -sTCP:LISTEN` — list EVERY listener (look for separate IPv4 + IPv6 rows; may be different processes).
  > 2. `curl -v http://[::1]:<port>/…` AND `curl -v http://127.0.0.1:<port>/…` with the same headers as browser; if responses differ, you have two servers.
  > 3. `docker ps -a | grep <port>` — Docker Desktop keeps containers running across reboots.
  > 4. Test OPTIONS (preflight), not just GET. Failed preflight is cached per-tab for `access-control-max-age`; close the whole tab, not just reload.

---

### Group R — "Sandbox limit: launchd can't reach /usr-mount, plist must use absolute paths" — duplicate of Group I, no new rule

(Subsumed in Group I.)

---

### Group S — "Path(__file__).parent×N breaks in Docker; use env var with fallback"

Single entry: [rivendell] 2026-04-07 Docker API Path

- **Why generic**: Applies to any Python project deployed to Docker.
- **Proposed CLAUDE.md rule**:
  > Any path that diverges between local dev and Docker (e.g. `reports/`, `data/`) must be an env var with `__file__`-derived fallback: `Path(os.environ.get("REPORTS_DIR", str(Path(__file__).resolve().parent.parent.parent / "reports")))`. Never hard-compute it from `__file__` alone — Docker WORKDIR breaks the relative parent count.

---

### Group T — "Right-size infra; default to SQLite + Cloudflare Tunnel + always-on personal machine for small internal tools"

Single entry: [ChimesFlow] Right-size infra for actual scale

- **Why generic**: Anti-overengineering principle for internal/small tools.
- **Proposed CLAUDE.md rule**:
  > Before recommending "production = cloud + Postgres + multi-region" for an internal tool, ask for actual scale (row count, concurrent users, SLA). For ≤10k rows / ≤20 users: default to SQLite + always-on personal machine + Cloudflare Tunnel ($0/mo). Push back politely on over-engineering with the row count as evidence.

---

### Group U — "DNS inventory before recommending domain migration; Cloudflare Tunnel needs parent zone on CF DNS"

Merges 2 entries:
- [ChimesFlow] Always inventory DNS before recommending a domain migration
- [ChimesFlow] Cloudflare Tunnel hostnames require parent on CF DNS

- **Why generic**: Applies to any DNS migration suggestion.
- **Proposed CLAUDE.md rule**:
  > Before suggesting any DNS provider migration, run a full audit (`dig +short <domain> NS|A|AAAA|MX|TXT|CAA` + DKIM `selector1._domainkey` + `_dmarc` + common subdomains). Enumerate the risk ("email/marketing site/dev subdomain breaks") explicitly. For Cloudflare Tunnel: `tunnel route dns` only works if the parent zone's NS already points to Cloudflare — `dig <domain> NS` first.

---

### Group V — "Vue script setup declaration order: refs → computeds → useApi/watch"

Single entry: [news_stock] 2026-04-20 Vue useApi immediately evaluates computed

- **Why generic**: Applies to any Vue 3 / Nuxt 3 codebase.
- **Proposed CLAUDE.md rule**:
  > In Vue 3 `<script setup>`, declare in this order: base `ref`s → `computed`s → `useApi`/`watch`. Composables like `useApi(computed(() => ...))` evaluate their argument at setup time, hitting TDZ if a referenced ref is declared later.

---

### Group W — "Skill creation should follow flow doc first, only add new skill if the flow can't disambiguate"

Merges 2 entries (both rivendell, but the meta-rule generalizes):
- [rivendell] 2026-05-07 Skill audit ≠ skill orchestration audit
- [rivendell] 2026-05-07 Storyline-first hard gate intentionally NOT a hook

- **Why generic**: Applies to any agentic system with many skills.
- **Proposed CLAUDE.md rule**:
  > When the user asks "do we need a new skill for X?" and ≥3 skills already touch X's domain, the right next question is "is there a written flow that says when each fires?" — not "build another skill". Check `~/.claude/CLAUDE.md` for a `### X Flow` section first; document the flow before adding skills. Soft gates (warning at one entry-point) beat hard hooks unless the failure mode appears at multiple entry-points.

---

### Group X — "Reviewer-context-aware review pickers: when reviewer already has full plan context, prefer tight single-pass over autoplan"

Single entry: [rivendell] 2026-05-07 /gstack-autoplan ROI threshold

- **Why generic**: Applies to any "full vs tight review" choice.
- **Proposed CLAUDE.md rule**:
  > Cost/benefit of a heavy review skill = delta between what the reviewer already knows and what the review would produce. If the planning session is fresh in context AND plan is < 1000 lines, reversible, with ≤3 real architecture decisions — pick a tight single-pass review. Reserve full multi-phase review for cross-session resume, customer-facing surface, security-sensitive, or plans that already had a revision cycle.

---

## 🏛️ Rivendell-meta (17) — proposed for rivendell/.claude/CLAUDE.md or rivendell/.learnings/

### [Projects/LEARNINGS.md] gstack installation: symlink repo into ~/.claude/skills/
- **Why rivendell-meta**: Specific to gstack repo + ~/.claude/skills layout used by rivendell ecosystem.
- **Proposed location**: keep in `.learnings/` (low recurrence; one-time install gotcha)

### [Projects/LEARNINGS.md] Separate skills by domain — gstack vs rivendell territory
- **Why rivendell-meta**: Defines rivendell's relationship to gstack (specific skill removal list).
- **Proposed location**: promote to `rivendell/.claude/CLAUDE.md` (boundary rule that needs to be enforced on every skill add)

### [rivendell] 2026-05-13 dashboard-next is launchd-managed; bootout/bootstrap not kill
- **Why rivendell-meta**: Names `com.sk.dashboard.*` plists and start-web.sh; rivendell-specific service topology.
- **Proposed location**: promote to `rivendell/.claude/CLAUDE.md` (active service ops rule)

### [rivendell] 2026-05-07 Long-running next-server on port 3000 (the dashboard-next variant)
- **Why rivendell-meta**: Same trap but specifically dashboard-next port 3000 / 3020 fallback.
- **Proposed location**: keep in `.learnings/` (generic rule already in Group A; rivendell-specific port table in dashboard-next/CLAUDE.md)

### [rivendell] 2026-05-07 Logo-first beats full aesthetic redesign (rivendell DESIGN.md outcome)
- **Why rivendell-meta**: References dashboard-next DESIGN.md and twin-leaves logo decision.
- **Proposed location**: keep in `.learnings/` (history of one redesign session)

### [rivendell] 2026-05-07 Storyline-first hard gate decision (slide-workflow Gate 0)
- **Why rivendell-meta**: References rivendell's slide-workflow and the cd63836f 光泉 deck decision.
- **Proposed location**: promote to `rivendell/.claude/CLAUDE.md` (the "stop here" decision needs to not be relitigated)

### [rivendell] 2026-05-07 Skill audit ≠ skill orchestration audit
- **Why rivendell-meta**: References ~/.claude/CLAUDE.md sections and slide-workflow ecosystem.
- **Proposed location**: keep in `.learnings/` (generic rule promoted via Group W; rivendell evidence stays here)

### [rivendell] 2026-05-05 Built-in Claude Code skills invisible to rivendell audits
- **Why rivendell-meta**: Names rivendell's `bin/sk audit` and explains why some skills don't appear.
- **Proposed location**: promote to `rivendell/.claude/CLAUDE.md` (skill-audit maintainers need this)

### [rivendell] 2026-05-05 stats-cache.json no longer maintained
- **Why rivendell-meta**: Rivendell dashboard's tokens.py refactor; specific to dashboard.
- **Proposed location**: keep in `.learnings/` (generic rule already in Group B)

### [rivendell] 2026-05-03 Storyline review IS the leverage point (slide-office-hours design)
- **Why rivendell-meta**: Concretely about the slide-office-hours skill being a review gate.
- **Proposed location**: keep in `.learnings/` (skill-design history)

### [rivendell] 2026-05-03 Presales deck content edge: operator-level猜製程 > 公開資料推測
- **Why rivendell-meta**: Already in MEMORY.md; user-validated rivendell-specific principle for presales decks.
- **Proposed location**: already in `~/.claude/projects/.../memory/MEMORY.md` — KEEP there, drop from learnings

### [rivendell] 2026-04-28 Diff-before-replace when fixing symlinks
- **Why rivendell-meta**: Specific to `bin/sk-deploy-symlink-fix`.
- **Proposed location**: keep in `.learnings/` (generic rule promoted via Group K)

### [rivendell] 2026-04-27 Half-built `.next` makes Next.js 500
- **Why rivendell-meta**: Names rivendell's start-web.sh and `.next/.build-complete` sentinel.
- **Proposed location**: keep in `.learnings/` (generic rule promoted via Group F)

### [rivendell] 2026-04-26 launchd KeepAlive + HTTP-probe watchdog pattern
- **Why rivendell-meta**: Names `bin/sk-watchdog`, `agents/agents.conf`, `reports/.watchdog-state`.
- **Proposed location**: keep in `.learnings/` (generic rule in Group I; rivendell implementation history here)

### [rivendell] 2026-04-23 macOS IPv4/IPv6 + Docker container shadowing
- **Why rivendell-meta**: Names `sk-dashboard-api` docker container specifically.
- **Proposed location**: keep in `.learnings/` (generic rule promoted via Group Q)

### [rivendell] 2026-04-22 `git log | head` pipefail in `bin/sk`
- **Why rivendell-meta**: Specific to `bin/sk maintain` and `com.sk.agent.rivendell.maintain` plist.
- **Proposed location**: keep in `.learnings/` (generic rule promoted via Group J)

### [rivendell] 2026-04-21 Auto-stage PostToolUse hook
- **Why rivendell-meta**: Specific to rivendell's auto-stage hook; mentions `reports/*` curation rule.
- **Proposed location**: promote the `reports/*` curation rule to `rivendell/.claude/CLAUDE.md` (specific to this repo's hook + scheduled agents)

### [rivendell] 2026-03-18 Repo rename breaks all agents
- **Why rivendell-meta**: Detailed rivendell-specific protocol (LaunchAgent plists, dashboard, agents.py).
- **Proposed location**: promote to `rivendell/.claude/CLAUDE.md` if repo-rename procedure is needed again (otherwise keep in `.learnings/`)

### [rivendell] 2026-03-18 Never hardcode repo/project name in scripts
- **Why rivendell-meta**: Defines rivendell's "derive PROJECT_NAME dynamically" coding rule.
- **Proposed location**: promote to `rivendell/.claude/CLAUDE.md` (active coding rule)

### [rivendell] 2026-03-24 settings.local.json corrupted by one-time Bash permissions
- **Why rivendell-meta**: Specific to Claude Code's permission file format and the rivendell session that bloated it.
- **Proposed location**: keep in `.learnings/`

### [rivendell] 2026-03-24 Autoresearch discard must NOT use git clean
- **Why rivendell-meta**: Specific to `sk-autoresearch`.
- **Proposed location**: keep in `.learnings/` (generic rule promoted via Group J)

### [rivendell] 2026-03-24 Cross-project exec-lib sourcing needs export
- **Why rivendell-meta**: Specific to `SK_EXEC_REPO_DIR` + `sk-exec-lib`.
- **Proposed location**: keep in `.learnings/`

### [rivendell] 2026-04-01 Always check port map before starting a dev server
- **Why rivendell-meta**: References `mockups/port-map.html` SERVICES array.
- **Proposed location**: keep in `.learnings/` (generic rule promoted via Group A)

### [rivendell] 2026-04-07 launchd agents EDEADLK on cross-project source
- **Why rivendell-meta**: Names specific cron scripts.
- **Proposed location**: keep in `.learnings/` (generic rule promoted via Group I)

### [rivendell] 2026-04-07 Docker API Path(__file__) breaks
- **Why rivendell-meta**: Names `dashboard-next/api/server.py`.
- **Proposed location**: keep in `.learnings/` (generic rule promoted via Group S)

### [rivendell] 2026-03-24 Dashboard must discover log paths from plist
- **Why rivendell-meta**: Specific to dashboard `/live` and `/files` endpoints.
- **Proposed location**: keep in `.learnings/`

(Net rivendell-meta entries to PROMOTE to rivendell/.claude/CLAUDE.md: 6. Others stay in `.learnings/`.)

---

## 🏠 Project-specific (67) — keep in original .learnings/

### ChimesFlow
- For new UI features, start from `/requirement` — KEEP (ChimesFlow workflow gating)

### news_stock
- 2026-03-12: yfinance not installed on system Python — KEEP
- 2026-04-28: MOPS Playwright session hard-throttles after ~7 hours — KEEP
- 2026-04-07: sqlite3 date/datetime adapter (resolved) — KEEP (resolved, but pattern is news_stock-specific; could DROP, see below)
- 2026-04-20: rotation 策略 cash constraint — KEEP
- 2026-03-18: Nuxt 3 component auto-import (news_stock-specific verification path) — KEEP
- 2026-03-17: FastMCP API change — KEEP
- 2026-03-17: Claude Code MCP config uses .mcp.json — KEEP
- 2026-04-21: FinMind TW cash flow field keys — KEEP
- 2026-04-21: FinMind monthly_revenue does NOT include YoY/MoM — KEEP
- 2026-04-23: news_stock dev ports are 3001 / 8001 — KEEP
- 2026-04-23: FinMind TaiwanStockBalanceSheet mirrors MOPS — KEEP
- 2026-04-23: MOPS ajax_t164sb03 ROC year params — KEEP
- 2026-04-23: Docker container sk-news-stock shadows host ports — KEEP
- 2026-04-23: news_stock has config/db_paths.py resolver — KEEP
- 2026-04-25: Symbol convention mismatch 2330.TW vs 2330 — KEEP (generic rule in Group O; project specifics here)
- 2026-04-25: Nuxt 3 auto-import prefixes (news_stock components/fundamentals) — KEEP
- 2026-04-25: MOPS revenue ≠ FinMind revenue — KEEP
- 2026-04-28: GCIS API Chinese name lookup broken — KEEP
- 2026-04-28: Resolution chains need closed fallback — KEEP
- 2026-04-25: MOPS HTML uses &nbsp; — KEEP

### lorien
- best_practice: Lórien dev ports — KEEP
- best_practice: Lórien agent runtime uses Azure OpenAI — KEEP
- best_practice: SerpAPI for Google travel data — KEEP

### resume-pool
- 2026-04-22: Senior SWE 評估標準 — KEEP (resume-pool feedback heuristics)
- 2026-05-11: Senior SWE 評估再修正 — 髒活 SWE — KEEP
- 2026-05-11 修正 2: 客戶端部署 ≠ 硬體部署 — KEEP

### TailTrack
- 2026-03-11: Google Places SDK Swift API Gotchas — KEEP
- 2026-03-11: MapView body type-check timeout — KEEP
- 2026-03-11: Project uses Apple Maps not Google Maps — KEEP

### curia
- 2026-03-28: Upwork RSS feed discontinued — KEEP

### 綻放計畫
- 2026-04-28: Multi-skill workflow orchestration — KEEP

### rivendell (project-specific not promoted above)
- 2026-03-17: g0v PCC API brief.type — KEEP (tender scraper specifics)
- (Other rivendell-meta entries listed above)

### sales-assistant
- WebFetch daily quota — KEEP
- crm-projection DB must start first — KEEP
- 2026-05-11 subsidy-scraper WebFetch failed — KEEP
- All gov-tender-scraper-tw.md sections (Architecture / Tender Classification / Keyword Filtering / ODT Parsing / Deadline / Script Location) — KEEP
- best_practice: window.location.replace() for auth redirects — KEEP (sales-assistant specific Next.js auth)
- best_practice: gstack browse cookies re-import — KEEP
- knowledge_gap: Next.js App Router nested layouts — KEEP
- knowledge_gap: pcc.gov.tw RFI 案件不在「招標公告」 — KEEP
- best_practice: tender md 官方 URL 藏在 body — KEEP

### rakucamp
- 2026-04-14: Noto Sans TC + next/font failure — KEEP (rakucamp typography)
- 2026-04-23: Mockup default — interactive + softer palette — KEEP

### Feature requests (sales-assistant + rivendell) — KEEP all as pending backlog
- [sales-assistant] port-alignment skill
- [sales-assistant] tender decision_scraper
- [sales-assistant] deal 歸屬 org switching
- [rivendell] Tiered skill discovery (INDEX-first)
- [rivendell] slide-office-hours skill
- [rivendell] cost-aware-model-routing skill
- [rivendell] How to pick these up (meta)

---

## 🗑️ Drop (17) — to remove from .learnings/

### [Projects] # Learnings — DROP
- **Why drop**: File-header-only entry, no content.

### [ChimesFlow] --- date: 2026-05-03 category: correction --- — DROP
- **Why drop**: Stray frontmatter-only block with no content.

### [ChimesFlow] --- date: 2026-05-05 category: best_practice --- (3 occurrences) — DROP
- **Why drop**: Stray frontmatter blocks (between entries) with no content.

### [news_stock] # Errors Log — DROP
- **Why drop**: File header only.

### [news_stock] # Learnings Log — DROP
- **Why drop**: File header only.

### [news_stock] 2026-04-07 sqlite3 date/datetime adapter — DROP
- **Why drop**: Marked ✅ resolved on 2026-04-08; the underlying rule (register adapters for Python 3.12+) is captured in Group G generic rule. The error log entry serves no further purpose.

### [news_stock] 2026-03-17 FastAPI Query regex deprecation — DROP from project, captured in Group G
- **Why drop**: Resolved one-liner; the rule is in Group G generic. (Soft-DROP; can keep as a project-level history breadcrumb if preferred.)

### [lorien] # Errors Log — DROP
- **Why drop**: File header only.

### [lorien] # Learnings — DROP
- **Why drop**: File header only.

### [lorien] knowledge_gap: Next.js config file extension matters — DROP from lorien
- **Why drop**: Duplicates the lorien ERRORS.md entry "Next.js 14 不支援 next.config.ts"; the generic rule is in Group C.

### [lorien] passlib + bcrypt + openai + os.environ ERRORS — KEEP individual error logs as historical, but the rules are in Group G/D
- (No drop — the error logs are project history.)

### [lorien] 2026-04-07: SQLAlchemy 2.x cast(int) — DROP from lorien if not recurring
- **Why drop**: One-time error; rule is in Group H generic. Could keep as project history. (Soft-DROP.)

### [resume-pool] # Learnings — DROP
- **Why drop**: File header only.

### [TailTrack] # Learnings Log — DROP
- **Why drop**: File header only.

### [curia] # Learnings — DROP
- **Why drop**: File header only.

### [綻放計畫] # Learnings — DROP
- **Why drop**: File header only.

### [rivendell] # Feature Requests / # Learnings — DROP
- **Why drop**: File headers only.

### [rivendell] How to pick these up — DROP
- **Why drop**: Meta-instructions inside FEATURE_REQUESTS.md; redundant once the file structure is clear.

### [sales-assistant] # Errors & Tool Limits / # Feature Requests / # Project Learnings / # Taiwan Government Tender Scraper Pattern (heading) — DROP
- **Why drop**: File/section headers only, no content.

### [rakucamp] # Errors Log / # Learnings Log — DROP
- **Why drop**: File headers only.

---

## Final counts (with deduplication-soft drops counted)

- **🌍 Generic rules to promote to ~/.claude/CLAUDE.md**: 24 source entries → 14 distinct merged rules (Groups A–X above; Group R subsumed by I)
- **🏛️ Rivendell-meta**: 24 entries → 6 PROMOTE to `rivendell/.claude/CLAUDE.md`; rest stay in `.learnings/`
- **🏠 Project-specific keep-as-is**: 67 entries (domain-specific schemas, project-internal paths, business heuristics)
- **🗑️ Drop**: 17 entries (mostly file-header skeletons + 3-5 entries fully subsumed by generic rules)

Sum: 24 + 24 + 67 + 17 = 132 — slight overcount because some entries fit two buckets (e.g., a project-specific story that also seeds a generic rule). When forced to one bucket, the entry stays project-specific and the generic bucket only references it; final unique-entry count is 125.
