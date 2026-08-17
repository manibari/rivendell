---
name: odb-dfm-reference
description: >
  Domain reference for PCB manufacturing-side EDA — parsing ODB++ jobs and building
  CAM/DFM/NPI tooling (the Siemens Valor "read/verify/mark the board" layer, NOT
  schematic/layout design). Encodes the Job→Step→Layer model, the ODB++ parse seams
  (matrix, profile, features, packages), the unit/coordinate traps, and the
  symbol-rendering + depanel + registration gotchas that took real debugging.
  TRIGGER when: parsing ODB++ (`matrix/matrix`, `steps/*/layers`, `eda/data`),
  building a PCB DFM/CAM checker, rendering a board/footprint, normalizing fab
  geometry, or working in PTI-ARES / odb-dfm; "抓 ODB++", "DFM 規則", "Valor", "拼板/
  depanel", "device_class".
  SKIP when: front-end / logic EDA (boolean/SAT, schematic) — different field;
  IoT/SCADA sensor time-series (iot-factory-report); a generic CSV/xlsx job
  (office-xlsx). This is physical/manufacturing EDA = computational geometry.
tags: [backend, dfm, odb, pcb, cam, reference]
version: 1.1.0
source: manual
---

# odb-dfm-reference

Reference for **physical / manufacturing-side EDA**: read a board (ODB++), verify
it (DFM/DRC), mark it (back-annotate) — the Siemens **Valor** (Process Preparation /
NPI) layer. It does NOT draw boards; it reads/verifies/marks them. Grounded in two
real codebases: `~/code/PTI-ARES` and `~/Vault/Peter/scripts/odb-dfm`.

## The model: Job → Step → Layer

ODB++'s native hierarchy, and the spine of any CAM tool:
- **Job** = the board package. **Step** = a single board or a panel (拼板).
  **Layer** = copper / soldermask / paste(鋼網) / drill / ROUT(routing/cut).
- Typed objects: net / component / pad / via / trace / outline, with a netlist.
- A CAM tool = **Importers → one normalized design model (IR) → geometry/DRC engine
  reads it → rule deck → canvas/viewer → disposition/waiver → back-annotation**.
  (PTI-ARES: `parser.py` → `pcb.json` → `enricher.py` → `pcb-enriched.json` →
  `dfm_checker.py`.)

## ODB++ parse seams (where the data lives)

- **`matrix/matrix`** — STEP and LAYER blocks (`(STEP|LAYER)\s*\{...\}`); LAYER rows
  carry ROW/CONTEXT/TYPE/NAME.
- **`steps/<step>/layers/<layer>/features`** — the geometry per layer.
- **`steps/<step>/profile`** — board outline (OB/OS/OC sequence).
- **`eda/data`** — `PKG name pitch xmin ymin xmax ymax` (package extents).
- **`.Z` layers are gzip** — feature files are often `*.Z`; read gzip-aware or you
  get binary garbage (PTI-ARES `9fcc745`).

## Gotchas (highest-signal — each cost real debugging)

- **Units are per-FILE and sometimes UNDECLARED — never assume, always判定.**
  Four distinct traps, all seen in one job (PB0009, PTI-ARES-Transcribe 2026-08-06):
  1. **`features` declares its own `U MM` / `U INCH` per layer** — not global, not
     even job-consistent (PTI-ARES `0a254c2`).
  2. **`components` has NO units declaration at all, and is INCH** even when the
     sibling `features` files say `U MM`. Verify by geometry: components must land
     *inside* the profile. Read as mm, all 1,653 parts collapse into a 3.7×5.2 mm
     corner — and **nothing errors**, you just get silently wrong data.
  3. **`UNITS=` governs coordinates only, NOT size fields.** Symbol names and
     `tools` sizes are **µm** regardless: `tools` says `UNITS=MM` yet
     `FINISH_SIZE=254` means 254 µm. Cross-check: µm values come out as whole mils
     (`r25.4`=1mil, `r152.4`=6mil, `r203.2`=8mil, `r254`=10mil, `r1270`=50mil).
  4. **Valor's UI shows inch** (`X = -2.1119655"`) no matter what the files hold.
  Store one canonical integer unit internally (picometers survive both mm-9dp and
  inch-7dp exactly); keep the source unit + original string if you need round-trip.
- **Netlist references layers that have no geometry — this is NORMAL, not corruption.**
  Customers **mask inner-layer routing** (traces = their circuit IP) but keep the full
  netlist so the fab still knows connectivity. PB0009: `eda/data`'s `LYR` line names
  **27** layers while `matrix/matrix` has **23** — and they are *not* a subset
  relation (LYR adds s1–s6/p1–p6; matrix adds comp/asm/fab/outline layers). FID
  layer indices point into the **LYR** list, not matrix ROW. Result: **231,412 of
  350,476 FID records (66%) reference layers with no directory.** Therefore: keep the
  two namespaces in separate tables, **do not FK feature references** (every real job
  would fail to import), **do not warn** (every board would warn), render such layers
  as **empty**, and never back-derive the hidden traces — that defeats the customer's
  IP protection on purpose.
- **A copper layer's contents are not all copper — filter the drawing furniture.**
  PB0009's `top` carries 4,046 line records (6.0% of the layer) *outside* the board
  profile: the fab drawing's **title block**, drawn as text strokes with a zero-width
  aperture (`r0.1`) and tagged `.nomenclature` / `.string`. Resolving the strings
  proves it — `DOCUMENT NUMBER`, `CLASS CODE`, `CONFIDENTIAL`, `SIZE`, `FAB0`,
  `PRELIM`, a street address. It sits below the board, off-screen at Valor's default
  zoom, so nobody notices. **Filter `.nomenclature`/`.string` before any envelope,
  DFM, or connectivity pass**, or the board grows by 129 mm; and never index on the
  assumption that features lie inside the profile.
- **Feature attribute values have two meanings — don't blanket-treat them as indices.**
  In `;3=64` the `64` indexes the `&` text table (`&64 FAB0`); in `;5=0.000000` the
  number is a literal (`.string_angle` degrees). Decide by attribute type. Reading
  everything as an index silently turns a zero angle into text-table entry 0.
- **`.sum` files are a free bit-exact oracle.** Every ODB++ file has a sibling
  `.<name>.sum` holding `SIZE` (byte count) and `SUM` = **plain arithmetic sum of all
  bytes** (no modulo). Verified across all 70 `.sum` files in PB0009, zero mismatches.
  Use it to prove a regenerated file is byte-identical without keeping the original.
- **Symbols**: `r<n>` = **diameter in µm** (not radius); `oval` = **obround**
  (stadium), not an ellipse; **rect rotation** is encoded via paired swapped
  symbols, not an angle; the `orient` field is a useless constant — derive
  orientation from geometry.
- **Component = one rigid object**: body + pads + pin-1 placed as a unit; never
  flatten pads off the component. `device_class` (CHIP0402 / BGA / SOIC / …) comes
  from the **Valor checklist matrix**, matched on package geometry.
- **Board-edge rules are really depanel cut keep-out**: the cut geometry lives in
  the ODB++ **profile + ROUT layer**, NOT in the fab DWG. A bbox-edge model is
  wrong — use the real cut path.
- **Connection points = copper crossing the ROUT layer** (board↔panel tabs);
  operators hand-mark these slowly in Valor — they're auto-detectable from geometry.
- **DXG ↔ ODB++ registration**: align via a clean full-width **outline edge**, NOT
  holes (holes don't survive into the DXG). INSERT blocks must be expanded; bridge
  outlines live on layer 0 / OUTLINE.
- **The JSON IR is a knowledge base, not a throwaway** — it's the deliberate
  substrate downstream DFM/AI reads; don't "skip it for perf".
- **Net data IS available**: `cadnet` `$N` index→name; pads carry net; copper pours
  resolve by geometric containment. Position/refdes checks (位號錯置) need this
  back-derived electrical context, not silk-text matching.

## DFM rule framing (when checks reference Valor)

Rules = constraint queries over geometry, partitioned house-spec vs customer-spec,
tier-aware (Standard/Advance spacing matrices), with tolerance policies
(`MANUFACTURING_TOLERANCE_MM`, `DESIGN_INTENT_MARGIN_MM`) and per-pin device-class
matrices. Import Valor/Visual-DFM checklists (xlsx) → normalized rule JSON
(`parse_checklist.py`); normalize rule identity (collapse newlines, strip parens)
or the same rule imports twice. Disposition/waiver every violation (manage false
positives) before trusting a report.

> Front-end framing for reviewers/customers: lead with the official plan/SOW
> section codes (A+ 分項 / phase codes), then fill — don't invent framing from
> industry common-sense. Cite source doc + version in the report footer.
