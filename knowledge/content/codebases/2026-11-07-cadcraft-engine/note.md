---
title: CADCraft engine design — patterns for an editing system
source: code
path: ~/Code/Personal/Artcraft/cadcraft (main @ c4d9e6ac)
reliability: read from source code and docs/architecture.md
date: 2026-11-07
tags: [cad, editing-engine, command-pattern, undo, selection, spatial-index, never-crash]
used_by: PTI-ARES docs/design/2026-11-07-cadcraft-engine-study.md
---

# CADCraft engine design

Study made for PTI-ARES (CAD workbench). Decision there: learn the design, do not embed or call
CADCraft ("嵌入一套 cad 工具會像套娃"; "怕把現有 engine 搞壞").

## Patterns (with code references)

| # | Pattern | How CADCraft does it |
|---|---|---|
| C1 | Everything is a command | `CommandSpec` (`crates/engine/src/cmd.rs` L69-83): id, label, params doc, `enabled`, JSON `run`, `undoable`, optional prompt machine. Menus, command line, scripts, CLI, control channel and MCP all call one registry (295 commands). |
| C2 | One execute pipeline | `Session::execute` (`session/execute.rs`): find → enabled → keep state → run → post-command passes → post-command checks (`refuse_non_finite`) → one undo step labelled with the command. |
| C3 | Failure restores state | A panic or a failed check restores the drawing and the selection kept before the command. No half changes. |
| C4 | Cheap undo | Copy-on-write entity store; an undo step is a whole-drawing snapshot; change detection by pointer equality. |
| C5 | Selection is engine state | Selection set lives in the session, is restored and kept in undo. Window (L→R, inside) / crossing (R→L, touches), Shift add/remove, cycling are engine logic (`select.rs`). UI only draws the rectangle. |
| C6 | Spatial index | R-tree (`spatial.rs`) patched per changed chunk; picking ≈ 0.001 ms at 200k entities. |
| C7 | Thin, swappable UI | Layering L0 geom → L4 engine → L5 UI checked by `cargo xtask layers`; panels act only through `run(id, params)`. |
| C8 | Programmatic calls never open dialogs | `engine.execute` = JSON form with defaults. |
| C9 | Never crash | No panics in production code; input-sized numbers capped; every crash fix has a regression test. |

## What transfers to a web product with a persistent, audited history

- Take C1/C2/C3/C8: one command table with a params schema, one pipeline (idempotency, version
  check, write, post-command checks, history record), JSON-callable from tests and scripts.
- Do not take C4 as is: in-memory snapshots do not survive restarts, users or audits. Keep an
  event ledger; make undo generic by storing change sets (rows added/removed/updated) and applying
  the inverse with a conflict check, instead of one compensation function per entity kind.
- Take C5/C6/C7 for the canvas: selection and hit testing in a pure core module with tests; an
  R-tree for box queries; UI components only draw and forward input.
- Add C3-style post-command checks that refuse an edit which would break an invariant.

## Not applicable

Direct in-place editing of the source file (PTI-ARES must keep the customer ODB++ unchanged; edits
are an overlay). Rust/egui/WASM runtime. DXF as the native format.
