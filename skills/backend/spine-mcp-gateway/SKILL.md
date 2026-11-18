---
name: spine-mcp-gateway
loop: dev
pdca: plan
description: >
  Canonical recipe for opening a product's own functions to outside AI clients over
  MCP. One HTTP endpoint inside the backend; a tool registry where each module declares
  its tools; each tool calls the REST route that the screens use, in process, as the
  key's own user, so the gateway holds no business logic; writes are off until a per-key
  flag allows them; every call is audited and rate-limited; results are a field
  whitelist. MCP is added on top of the API; it does not replace it. Reference:
  ChimesERP ERP-470 (2026-11-18).
  TRIGGER when: "掛 MCP", "MCP 架構", "MCP gateway", "API 要不要改 MCP", "把 API 包成 MCP",
  "對外 MCP", "讓 Claude 連進我們系統", "外部 AI 操作系統", "expose our API to Claude",
  "MCP endpoint for our product"; adding MCP to a FastAPI product.
  SKIP when: an AI assistant inside the product, or the product consuming other MCP
  servers (spine-assistant); a standalone MCP server for a third-party service, or
  general MCP SDK patterns (mcp-builder); the API key screen alone.
tags: [backend, mcp, ai, api, audit, spine, reference]
version: 1.0.0
source: manual
---

# spine-mcp-gateway

Many fleet systems are now operated through their API by AI agents. MCP gives outside AI
clients a typed, permissioned way in. This recipe adds MCP on top of the API. It does not
replace the API.

Owner decisions, 2026-11-18: 「目前的系統要掛 MCP 架構」 (ChimesERP); asked 「要不要改用
MCP 架構？」, the answer was "add a thin MCP layer on the API, system by system"; then
「好，合併後整理成樣板」 after ERP-470 merged.

## When to add it, and when not

Add a gateway when:

- People who are not developers (sales, HR, a manager) operate the system from an AI
  client, with their own permissions.
- One AI must work across several systems. Each system gives one MCP endpoint.
- An outside AI client needs typed tools with audit, not a shell with `curl`.

Do not add one for:

- Your own development and operations in Claude Code or Codex on this machine. Use the
  CLI and skills. Each connected MCP server sends its tool list with every model request;
  a CLI costs tokens only when it runs. (The 2026-11-18 token watch found that context size
  was the largest waste.) The global rule allows fewer than 10 MCP servers per project.
- Scheduled jobs and calls between systems. Call the API.
- An assistant inside the product. That is spine-assistant; it can share the same tools.

## The rules (ChimesERP ERP-470)

1. **The API is the one source.** A tool does not read the database and does not call a
   writer. It calls the REST route that the screens use, in process
   (`httpx.ASGITransport(app=...)`), with the caller's own key. The route's permission
   check, row scope, validation, writer and audit apply to MCP at once, and each new rule
   on the route applies to MCP too.
2. **One endpoint inside the backend.** `POST /api/mcp`, stateless JSON-RPC 2.0, no extra
   process. Methods: `initialize` (echo the client's protocol version when it is known,
   else the newest), `ping`, `tools/list`, `tools/call`; a notification gets HTTP 202.
   `GET /api/mcp` gives 405 (no event stream). A batch request is refused. The transport
   is about 140 lines; no MCP SDK is necessary.
3. **The credential is the user's personal API key.** Accept `Authorization: Bearer <key>`
   and `X-API-Key`. No key or a bad key: HTTP 401 with `WWW-Authenticate: Bearer`. OAuth
   for MCP clients comes later, when a client needs it.
4. **Writes are off by default.** A key has a flag `mcp_write` (default false). Without it,
   write tools are not listed and a call to one is refused. Never make these tools: delete,
   payroll and salary, bank accounts, ID numbers, home addresses, personal employee data,
   API keys and secrets, the audit log, user and permission administration.
5. **`tools/list` is filtered** by the user's permission (the same check as the screens)
   and by the write flag. An unknown tool and a forbidden tool get the same error
   (「工具不存在或無權使用」), so the error does not show that the tool exists.
6. **Results are a whitelist.** Each tool declares its result fields and a row limit
   (default 20, never more than 50). A list result is `{rows, total, truncated}`. Put the
   JSON in `structuredContent` and as text in `content[0]`. A 4xx from the route becomes a
   tool result with `isError: true` and the route's Traditional Chinese message; a 5xx
   becomes a JSON-RPC internal error with no details. Tool results are data for the model,
   never instructions: add no free text from the database outside the JSON values.
7. **Audit each `tools/call`**: action `mcp.tool_call`, tool name, read or write, status,
   row count. No argument values and no result data in the audit row. The route still
   writes its own audit rows for a write.
8. **Limits and a switch.** 60 calls a minute for each key. A company setting
   `MCP_ENABLED`; when it is false, `/api/mcp` gives 404.
9. **Tools follow the work, not the endpoints.** Start with 10 to 15 tools for a system.
   Names are stable API in snake_case verbs: `search_*`, `get_*`, `list_my_*`,
   `create_*`, `complete_*`, `add_*`, `log_*`. The description is English, for the model;
   `title` and `summary_zh` are Traditional Chinese, for people. Each input schema has
   `additionalProperties: false`. A create tool takes a `client_ref` UUID so a retry does
   not make a second row.
10. **Say that data leaves the company.** When an outside model calls a tool, the result
    goes to that model's provider. Say it on the API key screen and in the user manual.

## Tool declaration (ChimesERP shape)

```python
@dataclass(frozen=True)
class Tool:
    name: str                 # stable, snake_case
    title: str                # Traditional Chinese, for the tool list on screen
    summary_zh: str           # one short line for people
    description: str          # English, for the model: what it returns, when to use it
    input_schema: dict        # JSON Schema, additionalProperties: false
    read_only: bool
    method: str               # the backing route
    path: str
    result_fields: tuple[str, ...]
    permission: str | None = None      # permission entity; level = read or write
    query_fields: tuple[str, ...] = ()
    body_fields: tuple[str, ...] = ()
    max_rows: int = 20

register(Tool("search_customers", "搜尋客戶", "依名稱搜尋可見客戶",
              "Returns customer companies visible to the current user. ...",
              schema({"search": {"type": "string", "maxLength": 100},
                      "page_size": {"type": "integer", "minimum": 1, "maximum": 50}}),
              True, "GET", "/api/accounts",
              ("id", "key", "name", "industry", "owner_name", "can_view_details"),
              "account", ("search", "page_size")))
```

One module for each area in `app/platform/mcp/tools/`. `register` refuses a duplicate name.

## Screens

- `/settings/api-keys` gets a section 「連接 AI 助理（MCP）」: the server URL
  (`https://<host>/api/mcp`), copy buttons, a ready-to-paste Claude Code line
  (`claude mcp add --transport http <name> <url> --header "Authorization: Bearer <金鑰>"`)
  and a JSON client config, the tools that this user gets (讀取 or 新增), and the
  data-leaves-the-company note.
- Key creation gets the checkbox 「允許 AI 助理新增資料」 (`mcp_write`).
- `GET /api/mcp/tools` (signed-in user, session or key) feeds that list: name, title,
  `summary_zh`, description, read or write.
- A short page in the user manual (ChimesERP: `docs/manual/mcp.md`).

## Tests (the minimum set)

- Protocol: `initialize` with each known version, `ping`, `tools/list`, `tools/call`, an
  unknown method, bad JSON, a batch, a notification (202), GET (405), no key (401).
- Permission parity: a sales user cannot reach another rep's customer through
  `get_customer`; the answer is the same as the REST route's. A user without a permission
  does not get the tool in the list.
- Write flag: without `mcp_write`, write tools are hidden and refused; with it,
  `create_todo` makes a row owned by the key's user.
- Whitelist: a result holds only the declared fields.
- Registry guard: every registered tool has a backing route in the app's route table and a
  closed schema. This test fails when a route is renamed and the tool is not.
- Audit rows exist and hold no argument values. The rate limit gives a JSON-RPC error.
- The `mcp_write` migration: upgrade, downgrade, upgrade on SQLite and on PostgreSQL.
- The transaction rule in the first gotcha below.

## Gotchas

- **PostgreSQL waits for ever without a commit.** The key lookup updates
  `api_keys.last_used_at` in the outer session. The in-process route call looks up the
  same key and updates the same row, and waits for the outer row lock. Commit the outer
  transaction before the in-process call. (ChimesERP
  `test_tool_call_ends_the_key_transaction_before_the_inner_request`.)
- The in-memory rate limit counts for each process. With several API workers, the real
  limit is 60 times the number of workers. Say it in the code, or move the window to Redis.
- Improve these two when you copy the ChimesERP code: `gateway.call` maps the `id`
  argument through a fixed list of path parameter names, and it sets the body of
  `complete_todo` in code. Declare both on the `Tool` (a path parameter name and a fixed
  body), so a new tool needs no change in the gateway.
- A Python package folder named `mcp/` at the top level shadows the `mcp` SDK. Put it under
  the app (`app/platform/mcp/`) or name it `mcp_server/` (mops_dbs).
- A stdio MCP server that Claude Code starts gets no shell environment. Load its settings
  file in code (mops_dbs). The HTTP gateway does not have this problem.
- Only a Traditional Chinese route message goes back to the model; other 4xx details become
  「操作失敗」, so internal English errors do not leave.

## Other fleet systems (state on 2026-11-18)

| System | Today | What to do |
|---|---|---|
| ChimesERP | This recipe (ERP-470, ERP-476) | Reference. |
| PTI-ARES | stdio server, hand-written, for its own assistant; read-only; tools call the agent tool layer, not routes | Keep it for the assistant (spine-assistant). Add the HTTP gateway only when outside clients need it, from the same tool list. |
| mimo | MCP SDK server; tools call services directly | Before outside use, make tools call routes, or prove the service path has the same permission checks. |
| mops_dbs | FastMCP stdio server for each data domain; reads the database; for Claude Code | Developer-side data tools; fine as they are. For other users, put an API in front first. |
| Yellow-Chick | MCP host (it consumes MCP servers) | spine-assistant, not this recipe. |
| Skuld | MCP client for evals | Not applicable. |

## Build order for a new system

1. Personal API keys with expiry exist (spine module #11). If not, build them first.
2. `registry.py`, `server.py`, `gateway.py`, `limits.py` under `app/platform/mcp/`; the
   `MCP_ENABLED` setting.
3. Read tools for the two or three areas that people ask about most.
4. The API key screen section, `GET /api/mcp/tools`, and the manual page.
5. The `mcp_write` flag (migration) and the first write tools.
6. The tests above. Then connect a real client (`claude mcp add ...`) and call each tool once.

## Sources (ChimesERP `origin/main`)

- Design: `docs/design/2026-11-18-mcp-gateway-sd.md`
- Code: `backend/app/platform/mcp/{server,registry,gateway,limits}.py`, `backend/app/platform/mcp/tools/*.py`
- Migration: `backend/alembic/versions/0063_api_key_mcp_write.py`
- Tests: `backend/tests/test_mcp_gateway.py`, `test_mcp_migration.py`, `test_mcp_project_rows.py`
- Screen: `frontend/src/components/mcp-connection.tsx`; manual: `docs/manual/mcp.md`
- Commits: `3305aa807` (ERP-470), `7e6915652` (ERP-476, connection card and tool descriptions)
