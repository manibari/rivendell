---
name: spine-assistant
loop: dev
pdca: plan
description: >
  Canonical recipe for an in-app agentic AI assistant in a FastAPI + PostgreSQL product:
  the model touches product data only through tools, each tool call runs with the
  asking user's permissions, the answer is structured JSON whose sources must come
  from this turn's tool output, every tool attempt leaves an audit record, one module
  owns the provider choice, and a model failure is a clear error, never a silent
  switch. Two real implementations: Yellow-Chick (secretary + AI employees, gated
  writes, provider roster, quota, memory) and PTI-ARES (read-only Q&A over its own MCP
  server). Default for an internal business system (ERP): read-only first, gated
  writes later.
  TRIGGER when: adding an AI assistant, chat assistant, agent or copilot to a product;
  "AI 助理", "問答助理", "AI 秘書", "做一個 agent", "agentic", "讓 AI 查系統資料",
  "讓 AI 幫忙建單", "assistant tools", "tool calling over our data"; deciding
  read-only vs write, which model provider, quota, memory, or how to cite sources.
  SKIP when: a one-shot model call with no tools, such as OCR or a summary
  (ai-vision-extract, or the product's own provider code) / 單次拍照辨識、單次摘要;
  building only an MCP server (mcp-builder) / 只寫 MCP server; Claude Code agents for
  dev work (agent-headless, agent-persona) / 開發用 agent 排程; a chat bot on Telegram
  (telegram-bot); picking a coding executor (agent-code-dispatch).
tags: [backend, ai, agent, assistant, llm, mcp, audit, spine, reference]
version: 1.0.0
source: manual
---

# spine-assistant

How to put an agentic AI assistant inside a product. The assistant reads (and later
writes) product data for a signed-in user. This recipe comes from two real
implementations. Greenfield products are consumers of this recipe, not sources.

`YC=~/Code/Yellow-Chick` — a secretary that talks to the user, plus AI employees that
do longer work. Writes go through a Gate. Provider roster, quota, memory.
`PTI=~/Code/PTI-ARES` — a read-only Q&A agent on PCB data. One `codex exec` run per
question, with PTI's own stdio MCP server as the only tool source.

## The eight rules (both implementations)

1. **Tools are the only path to data.** The model gets no SQL, no DB URL, no shell.
   Read-only is a property of the tool set and the DB session, not of the prompt.
   PTI: "prompt 擋不住，工具集擋得住" (SD §7 T5); tools run in a READ ONLY transaction.
2. **Each tool call runs as the asking user.** Use the same permission function that
   the HTTP endpoints use. YC `app/permissions.py:31` `can()` serves both. PTI passes
   the asker's identity to the MCP child and filters boards with `may_access`.
   Aggregate tools must filter too (see Gotchas, PTI-494).
3. **The answer is structured JSON, and sources are checked.** Give the model a JSON
   schema. Accept a citation only when a tool returned that reference in this turn.
   Drop the others and record why. PTI also copies `value` and `unit` from the tool
   reference, so the model never restates a number.
4. **Every tool attempt leaves a record.** Record success, failure, cache hit and
   refusal. The audit table is append-only in the database. YC writes one `tool.call`
   event row per attempt. PTI writes one log line per call into `agent_turn.tool_calls`,
   and one `agent_turn` row per question, degraded questions included.
5. **One module reads the provider setting.** YC: only `registry.py` reads
   `settings.llm_provider`, and an AST test fails on a second reader. PTI: only
   `orchestrator.py` reads the Codex model and binary settings.
6. **A model failure is a clear error.** Do not switch to another provider silently
   (YC provider-choice SD D3). Show a fixed reason code. Keep the turn record. A
   configuration error is not retryable (YC `LLMConfigurationError`).
7. **Fake providers for unit tests, plus a real-model acceptance lane.** YC: `mock`
   and `recorded` providers; a missing fixture fails, it never falls back to mock
   (D14). PTI: a fake `codex` binary. Both have a separate lane that calls the real
   model. Neither repo holds a scored question bank. Skuld has an interim one (Sources).
8. **The server owns every limit.** The model sees the remaining budget but cannot
   change it. YC: 3 tool calls per chat turn, plus decision and seconds budgets.
   PTI: 4 questions at the same time, timeout clamped to 120 s, 50 rows per tool.

## Tier decisions (where the two diverge)

The ERP column is a recommendation for a new internal system. It does not come from
either source.

| Decision | Tier A: PTI-ARES | Tier B: Yellow-Chick | Default for an ERP |
|---|---|---|---|
| Writes | None. No write tool exists. A write request gets "我只能查詢…" | Gated writes (below) | **Start A.** Add B per action later |
| Provider | One fixed: Codex CLI on OAuth | Roster of 6 slugs; workspace default + personal key (SD only) | One fixed, behind a roster-shaped module |
| Quota | None; concurrency gate + Codex login health | Monthly plan token cap; OAuth subscription slugs skip it | Usage ledger first; cap when a paid API key is used |
| Memory | None; history per user x board session | `memory` table, explicit remember / forget | None. Add only on a user request |
| Tool transport | Own stdio MCP server | Chat: in-process toolbox. Employees: MCP host | In-process first; MCP when a second model must reuse the tools |
| Progress | One request, 20-30 s, no steps | `turn_progress` table, polled every 0.8 s | Polling, if a turn takes more than 5 s |

### Writes through a Gate (YC, Tier B)

- **Draft, then approve that exact content.** `preview()` returns a draft with a
  `content_hash`. The Gate stores the approval with that hash. The MCP host re-checks
  the hash before it calls the outside world: "核准的就是送出的那一份" (D17).
- **Eight ordered steps per tool call** (`app/integrations/mcp/host.py`): binding,
  (1b reach), cached answer or receipt, gate, reserve, credential, call, book, event.
  The order is the design. The event step writes a row also for each refusal.
- **Money is never pre-approved.** Standing approvals refuse `money=True` at grant and
  at run time (D43, `gate/standing.py`). A money confirmation is pressed only by the
  task's own person, not the owner or an admin (D57, `gate/money.py`).
- **Auto-proceed is not for gates.** D62 lets a non-money suggestion card proceed after
  5 minutes. Gates (login, verification code, payment, irreversible write) never do.
- **Chat writes skip the Gate only when they have an undo.** `gate_exempt` is
  `undo is not None`. The user gets a 10-minute undo button (`writes/chatwrite.py`).
  An action with no undo, such as an invoice, becomes a task with a Gate.
- **Tool grants follow the duty.** A role gets project tools from its duty, and the
  host asks again on every call (D55, `employee/harness/grants.py`). A removed duty
  refuses the next call.

### Provider roster (YC, Tier B)

- `_ROSTER` in `registry.py` maps slug to factory: `mock`, `recorded`, `codex-cli`,
  `anthropic`, `gemini`, `openai-compatible`. Real providers import lazily.
- The interface is `complete(messages, schema) -> Completion` (`types.py`). Structured
  output goes through `schema`, not native tool calls. With a schema, `json` is
  required; a missing `json` is a retryable `StructuredOutputError`.
- MODEL-PROVIDER-CHOICE SD (2026-10-07): personal choice, then workspace default, then
  platform default. No cache, so a save applies to the next call. The code today
  still resolves only the platform setting plus the `llm_funding` key.

### Memory (YC, Tier B)

`app/secretary/memory.py` is the single writer. "記住…" writes without the model. The
model may also extract at most 3 items per turn. "忘掉…" is a soft delete plus an event,
so "why did it forget" has an answer. Reads take the latest 20 rows. Employees never
read the table; they get selected facts on the delegation.

## Build order for a new product

Do the steps in this sequence. Do not start a step before the previous check passes.

1. **Write the SD and the tool list.** For each tool, write the question, the query,
   the return shape and the citation key (PTI `docs/requirements/agentic-q2-readonly-tools.md` §0).
   Check: each tool runs on a real dev DB and returns its citation key.
2. **Build the provider module.** One roster, one reader of the setting, mock and
   recorded providers. Check: an AST test fails when a second module reads the setting.
3. **Build read-only tools on a read-only session.** Call the shared permission
   function inside each tool. Check: two users with different rights get different
   rows; an aggregate tool counts only visible records.
4. **Write one audit record per tool attempt.** Check: a test makes a refused call and
   finds its row; a direct SQL `DELETE` on the audit table fails.
5. **Build the turn loop.** Structured decision, server-side budgets, citation check.
   Check: a recorded answer with an invented reference shows it in the dropped list;
   the call after the limit is refused and recorded.
6. **Build the failure path.** Map each provider failure to a fixed reason code.
   Check: with the provider off, the API returns that code, the turn row exists, and
   no other provider is called.
7. **Build the UI.** Show answer, clickable sources, offline state, and progress.
   Check: a browser test on the mock provider at phone and desktop width.
8. **Add the real-model lane.** Run fixed questions against a scratch `*_test` DB and
   count the calls. Check: the lane refuses a production DB and port.
9. **Add a usage ledger.** Record tokens per call outside the turn transaction.
   Check: a failed turn still leaves its usage row.
10. **Later: add gated writes, one action at a time.** Check: an approval with a
    different hash is refused; a money action cannot get a standing approval.

## Reference (read before copying)

| Piece | File | Point to copy |
|---|---|---|
| Provider contract | YC `app/integrations/llm/types.py` | `complete(messages, schema)`; `Usage` with cached and reasoning tokens as parts of input and output |
| Provider roster | YC `app/integrations/llm/registry.py:109`, `:174` | One dict; `_chosen_slug()` is the only reader; unknown slug error names the file line |
| One-reader test | YC `tests/llm/test_llm_provider.py:103` | AST scan over `app/` |
| Error kinds | YC `app/integrations/llm/errors.py` | `retryable` / `missing_input` / `needs_human`; configuration errors are a separate type |
| Recorded provider | YC `app/integrations/llm/recorded.py` | Fixture key = hash of model + messages + schema; missing fixture raises |
| Chat tools | YC `app/secretary/manifest.json`, `app/secretary/lookup/toolbox.py` | 16 bound tools; `MAX_CALLS_PER_TURN = 3`; refusal rows; per-user results not cached |
| Decision loop | YC `app/secretary/lookup/query_loop.py`, `query_schema.py` | answer / call / clarify / delegate; unknown refs dropped in `_answer` |
| Permission check | YC `app/permissions.py:31` | One `can()` for HTTP and tools |
| MCP host | YC `app/integrations/mcp/host.py`, `gatekeeper.py`, `failures.py` | Eight ordered steps; undeclared exceptions still write a row |
| Gate | YC `app/governance/gate/standing.py`, `money.py` | Hash-bound approvals; money never pre-approved |
| Undoable chat write | YC `app/secretary/writes/chatwrite.py` | queue, drain with re-preview and hash check, undo within 10 minutes |
| Conversation store | YC `app/secretary/store.py` | Single writer; order by `seq`, not `now()` |
| Audit writer | YC `app/governance/events/writer.py` | Only writer of `event`; DB revokes UPDATE / DELETE / TRUNCATE |
| Quota rule | YC `app/commerce/billing/usage.py:107` | `monthly_quota_applies(provider_slug)` |
| Real-model lane | YC `tests/realmodel/realmodel_live.py`, `frontend/tests-live-realmodel/` | Scratch `*_test` DB; calls counted; refuses ports 8400 / 8401 / 8010 |
| Orchestrator | PTI `backend/app/features/agent/orchestrator.py` | Containment notes; `MAX_CONCURRENT` (:106); `validate_citations` (:616) |
| MCP server | PTI `backend/app/features/agent/mcp/__init__.py` | Per-run tool log; `_call` records `ok` / `error`; untrusted-data instruction |
| Viewer scope | PTI `backend/app/features/agent/tools/viewer.py` | Identity passed as a 0600 file; unreadable file = refuse |
| Turn audit | PTI `backend/app/shared/db.py:831` `AgentTurn` | Status `ok` / `no_evidence` / `llm_unavailable`; `tool_calls` JSONB |
| Degrade | PTI `docs/adr/0005-offline-package-excludes-agentic.md` | Health endpoint, 503 `llm_unavailable` with reason token |
| Fake and real model | PTI `tests/agent/ask/test_agent_ask.py:508`, `:1098` | Fake `codex` binary; real run only with `PTI_AGENT_INTEGRATION=1` |

## Gotchas

- **Cap blocked a subscription login (2026-09-26, HOTFIX-OAUTH-QUOTA, YC 0.5.2).** The
  monthly token cap ran before every call, also for Codex on ChatGPT OAuth. Decide by
  the resolved provider slug, not by the tenant funding label. An API key is never
  exempt.
- **Token double count (2026-09-29, YC usage SD §3).** Cached tokens are part of input;
  reasoning tokens are part of output. Total = input + output. The old code added them
  twice.
- **Tool data is prompt-injectable (2026-09-13, PTI security review).** Customer data
  reaches the prompt. Give the child process a minimal env. Pass the DB URL as a 0600
  file, not on argv. Mark tool output as data, never instructions.
- **Expired login looked like a crash (2026-09-30, PTI-470).** The user saw only "LLM
  執行失敗". Store a reconnect flag, report it in health, and hide the input.
- **Aggregate tools leaked other records (2026-10-01, PTI-494, PTI-495, PTI-497).** A
  tool without a board argument counted every board. Filter at query time. "No visible
  boards" is its own result, not 0 rows.
- **An undeclared exception left no row (YC F-35).** Catch at the tool host boundary,
  not in one connector. Raw exception text goes to the log, not to the user.
- **PTI does not record an unknown tool name.** It returns a JSON-RPC error before
  `_call`, so no log line exists. Record that refusal in a new build.
- **A budget checked only between calls is not a budget.** YC measured one final answer
  at 240 s against a 60 s budget. Pass the remaining seconds as the call timeout.
- **The mock picks the first enum value.** Put `answer` first in the decision schema,
  so tests that do not care about tools get an answer.
- **Cache keys must hold the tenant (D20).** Results that depend on the asker must not
  go in a shared cache at all.
- **An audit row in a rolled-back transaction is gone.** YC `write()` flushes in the
  caller's transaction. Record a refusal, then return a refusal result to the model.
  Do not raise an error that rolls back the request.
- **Provider read in seven places (CoBuild, per YC `registry.py`).** One missed place
  gave a bug nobody could trace. This is why rule 5 has a test.

## ChimesERP starting point

ChimesERP has no assistant. Start at Tier A and plug into what exists. **Permissions:**
`backend/app/middleware/auth.py:102` `require_permission(entity, action)` holds the
level lookup inside a `Depends` closure. Move that lookup into a plain function. Then
the dependency and each tool call the same function (YC `can()` shape). Row scope stays
in `backend/app/utils/rbac.py` (`get_scope`, `visible_user_ids_subq`); every tool
applies it. **Audit (PLATFORM-AUDIT):** `backend/app/services/audit_service.py` `log()`
is fail-closed, and PostgreSQL triggers block UPDATE, DELETE and TRUNCATE
(`backend/alembic/versions/0002_audit_trail.py`). Add an `assistant` scope to `_SCOPES`;
an unknown prefix gets no scope. `log()` flushes in the request transaction, so the
refusal gotcha above applies. **Provider:** `OCR_PROVIDER` is read in three places
(`routers/business_cards.py:40`, `services/business_card_ocr/service.py:55`,
`services/business_card_ocr/vision.py:83`). Lot issue picks its own provider in
`lot_issue/recognize.py` `provider_for()`, with classes in
`backend/app/lot_issue/recognition/providers.py`. Give the assistant its own module with
one reader; merging OCR into it is a separate ticket. Copy `ReplayProvider` (record
once, replay offline) and the label prompt rule "report null, never infer". **Writes
later:** money scopes (`accounting`: invoice, payment) stay out of chat writes. Route
gated writes through `backend/app/platform/approvals/` and keep the SoD checks in
`backend/app/platform/sod.py`. The ERP uses `AsyncSession`; YC is synchronous, so port
the shapes, not the code.

## Sources (SoT)

- YC main SD `docs/design/secretary/2026-09-19-secretary-system-sd.md`; decisions D6,
  D10, D11, D14, D17, D18, D20, D21, D43, D55, D57, D62 in `task_plan.md` "## Decisions log"
- YC `docs/design/ai-services/2026-10-07-model-provider-choice-sd.md` (D1-D5),
  `docs/design/ai-services/2026-09-29-oauth-usage-monitor-sd.md`,
  `docs/plans/hotfix/2026-09-26-oauth-quota-hotfix.md`, `tests/llm/test_oauth_quota.py`,
  `app/integrations/llm/codex_quota.py`
- YC `docs/design/chat/2026-09-28-chat-progress-sd.md` §3, `docs/plans/2026-10-05-owner-auto-proceed.md`
- YC `app/governance/gate/provider_block.py`, `app/integrations/mcp/manifest.py`,
  `app/secretary/turn/turn.py`, `tests/secretary/`, `tests/llm/`
- PTI `docs/design/2026-09-11-prepare-check-agentic-sd.md` §4 (LLM 接取, `/agent/ask`),
  `frontend/src/features/agent/AgentPanel.tsx`, `backend/app/features/agent/router.py`
- Skuld `~/Code/Skuld/server/skuld/evals/` (question bank, interim local-model loop)
- Pairs with [[spine-rbac]] (permission tier) and [[spine-roadmap]] (one ticket per
  write action). Registry: `rivendell/docs/spine-modules.md` (#20).
