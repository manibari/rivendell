---
name: artcraft-conventions
loop: dev
pdca: plan
description: >
  The conventions every Artcraft app follows (PdfCraft, CADCraft, and new ones such as
  PostCraft): how the MCP server is started, how files go in and out, how the app is
  packaged and installed, and how Yellow Chick adopts it as a tool host. Read it before you
  design or build a new craft, or add MCP or packaging to one.
  TRIGGER: "新的 craft", "做成 Artcraft 系列", "跟 artcraft 一樣", "PostCraft", "地端可下載的服務",
  adding an `mcp` subcommand to a craft, "Yellow Chick 操作這個工具", adopting a craft in
  Yellow Chick `mcp/`.
  SKIP: building the installer itself (app-installer owns the steps); a generic MCP server
  that is not a craft (mcp-builder); cloud services (deploy).
version: 1.0.0
tags: [artcraft, mcp, packaging, conventions, yellow-chick]
user_invocable: true
allowed-tools: "Read, Write, Edit, Bash, Grep, Glob"
---

# Artcraft conventions

The leading word is **headless first**. Every feature of a craft is a command in one
registry. The GUI, the CLI and the MCP server all call that registry. A feature is not done
until an agent can call it and a test proves it end to end.

Sources (read them for detail; this skill is the digest, checked on 2026-10-11):
`~/Code/Artcraft/pdfcraft/AGENTS.md` §3–4, `~/Code/Artcraft/cadcraft/docs/mcp.md`,
`packaging/macos/package.sh` in each repo, and Yellow Chick
`docs/design/mcp/2026-10-09-external-mcp-tools-sd.md`. The shared team standard is
`storytold/craftrules` (internal; not on this machine).

## 1. Family layout

| Item | Rule |
| --- | --- |
| Folder | `~/Code/Artcraft/<name>craft/`, one git repository per craft |
| Binaries | `<name>craft` (the app) and `<name>craft-cli` (CLI, MCP, scripts) |
| Rules file | `AGENTS.md` is the source; `CLAUDE.md` imports it; AGENTS.md wins on conflict |
| License | `MIT OR Apache-2.0`, with `NOTICE` and `LICENSE-*` |
| Assets | Each asset has an entry in `ATTRIBUTION.md` or `ATTRIBUTION.toml`; a check enforces it |
| Fonts | From the `craft-fonts` repo through `CRAFT_FONTS_DIR` |
| Version | One place (the workspace `Cargo.toml`, or `pyproject.toml` for a Python craft) |
| Commits | One task id per commit |
| Never crash | Errors return a value the user or agent can act on; no panic path, no lost work |

PdfCraft and CADCraft are Rust. A craft can be Python when its work needs Python tools
(for example yt-dlp, OCR, whisper). The rules above still apply.

## 2. MCP: how it is started

- **Opt-in only.** The app, the CLI and the installer never start the MCP server, never
  register it with an agent, and never listen on a port by default. It runs only when a
  user, or an agent the user configured, runs `<name>craft-cli mcp`.
- **Transport:** newline-delimited JSON-RPC 2.0 on stdio. No network port.
  A future network transport must be off by default, loopback only, and token protected.
- **Protocol:** answer `2025-06-18`; also accept `2025-03-26` and `2024-11-05`.
- **Tool names:** plain snake_case upstream (`doc_open`, `page_render`, `inspect_drawing`).
  The dotted prefix (`pdf.`, `cad.`) belongs to the consumer, not to the craft.
- **Many tools:** offer a compact mode (`--compact`: core tools plus `tool_search` and
  `tool_call`) so an agent does not load 100+ schemas.
- **Resources:** `<name>craft://...` URIs for read-only views (document text, page image).
- **Errors:** a failed tool returns its result with `isError: true` and a message that says
  what was wrong and what is allowed. Protocol errors use the JSON-RPC codes.
- **Calls are synchronous.** There is no job/submit and no progress notification today.
  A call that can take minutes must say so in its description, so the consumer sets a
  long timeout (see §5).
- **UI control channel** (drive the running GUI) is a separate opt-in: `--control <file>`,
  loopback, a fresh random token per launch in an owner-only file. Never log the token.

## 3. Files in and out

- **Paths, not uploads.** Tools take file system paths.
- **`--root DIR` is the boundary.** Every path, including outputs, must be inside DIR;
  relative paths resolve there. A new craft must honour `--root`. (CADCraft has no
  `--root` yet; its consumer sandbox is the boundary.)
- **Atomic writes.** Write to a temporary file and rename. Edits stay in memory until an
  explicit save tool; a tool never discards unsaved work without saying so.
- **Images come back as base64 image content**; large outputs go to a file under the root
  and the tool returns the path.

## 4. Packaging and install

Follow the `app-installer` skill for the steps; it owns the clean-machine check.

- Rust craft: `packaging/macos/package.sh` builds universal binaries in
  `$CARGO_TARGET_DIR/macos-package/bin/`, then the `.app`, codesign (ad-hoc by default,
  Developer ID and notarize optional), then a DMG with `hdiutil`.
- The CLI ships separately as a signed zip `<name>craft-cli-<ver>-macos-<arch>.zip`. It is
  not inside the `.app`, because agents and the consumer's tool host call the CLI.
- Other targets: `packaging/windows` (WiX), `packaging/linux` (nfpm).
- Python craft: the route in `app-installer` that carries its own Python runtime (like
  AutoML.app). External programs the craft needs (yt-dlp, ffmpeg, whisper models) go
  inside the bundle with their licenses in ATTRIBUTION.
- Release steps per repo: `docs/releasing.md`.

## 5. How Yellow Chick adopts a craft

Yellow Chick runs crafts on its local program host (`app/tool_host/`, launchd job
`tools`, 127.0.0.1:8405).

1. Register it in the `mcp/` workspace (its own git repository):
   `servers/<name>/server.toml` (prefix, source and commit, pinned version, build command,
   binary, `launch.args = ["mcp", "--root", "{workspace}"]`, protocol version, sandbox
   network `none` or `public` with a reason) and `tools.toml` (one entry per adopted tool:
   name, kind, side effect, risk, timeout, path arguments, Chinese description with
   TRIGGER / DO NOT TRIGGER).
2. `make smoke`, then `tools/export.py` writes `config/mcp-packs/<name>.json` with the
   binary sha256 and a schema hash per tool. Yellow Chick reads only adopted packs.
3. At run time the host checks the binary hash and the tool schemas (`schema_drift` stops
   the call), starts one process per run in a macOS sandbox, and gives it one run folder
   as `--root`. Files move in and out with `workspace.import` and `workspace.export`.
4. Limits: 120 s per call unless the tool sets more, 10 processes, 200 MB and 200 files per
   run. A long craft call needs its own `timeout_default`.
5. Bind tools to roles in `employees/<slug>/manifest.json` and the project mandates. Add a
   library skill for how to use them (for example `pdf-tidy`).

## 6. Checklist for a new craft

- [ ] Repo at `~/Code/Artcraft/<name>craft`, AGENTS.md, license, attribution, version in one place
- [ ] Every feature is a command in one registry; GUI, CLI and MCP call it
- [ ] `<name>craft-cli mcp` on stdio, opt-in, protocol versions above, snake_case tools, `isError` messages
- [ ] `--root` honoured; atomic writes; outputs as paths
- [ ] Credentials of the user (for example a Codex login) stay on the user's machine, in an owner-only folder; never in logs or tool output
- [ ] Installer passes the `app-installer` clean-machine check; CLI zip shipped beside the app
- [ ] Yellow Chick: `server.toml`, `tools.toml`, smoke steps, pack exported, role and skill bound
