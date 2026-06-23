---
name: ic-lot-normalization
description: >
  Domain reference for normalizing semiconductor lot / batch / product codes when
  building an IC test / yield-management (YMS) or ETL pipeline. IC test data arrives
  from many sources — wafer house, packaging subcons (SG/GS/JCET/Carsem), SAP, TE
  testers — each with its own lot-numbering scheme; this encodes the canonical
  normalizers (wafer lot, pkg lot, product code, 7-digit program-variant) and the
  data-janitor gotchas.
  TRIGGER when: parsing/reconciling IC lot numbers, wafer/package batch codes,
  product codes, TE test-program variants; building an IC yield/test ETL or YMS;
  "晶圓批號", "封裝批號", "product code 對不上", "測試平台碼", "lot 正規化",
  working in IC-YMS.
  SKIP when: PCB CAM/DFM (odb-dfm-reference); IoT/SCADA factory sensors
  (iot-factory-report); generic CSV cleanup with no IC-test jargon (office-xlsx).
tags: [backend, semiconductor, ic-test, etl, normalization, reference]
version: 1.0.0
source: manual
---

# ic-lot-normalization

IC test/yield data is multi-source and the same physical lot shows up under several
numbering schemes (wafer house vs packaging subcon vs SAP vs the tester). Before any
genealogy / yield / SPC join, normalize every id to ONE canonical form, or the joins
silently miss. Grounded in `~/code/IC-YMS/backend/normalize.py`.

## The canonical normalizers

- **Wafer lot** → `BASE-NN` (zero-padded). Inputs seen: `DIQ026.1`, `DIQ026_1`,
  `DIQ026#01`, `DIQ026/1`, `DIQ026 Wafer=1`, `DIQ026#01~20`, `DIQ026.1.TXT`. Base =
  `[A-Z]{3}\d{3}`; bare base (no wafer #) returns the base uppercased.
- **Package lot** → `BASE-N(+suffix)`. `DIP725R1_1` → `DIP725R1-1`; generic
  `[A-Z0-9]+[._]\d+(-Z)?` → `BASE-N` keeping a trailing `-Z` etc.
- **Product code** → canonical family code, stripping legacy/SAP wrappers:
  - `AS66583P-00000` → `RTC66583P` (legacy SAP `AS` prefix → `RTC`)
  - `FT66583P-00000-010` → `RTC66583P` (FT lot number → product)
  - `RTC66583P(0000000)` / `RBC66501N(0B0)` / `YHT6619U(0901000)` → strip the
    parenthetical variant → base family (`RTC`/`RBC`/`YHT` + digits).
- **Program variant** = a **7-digit suffix where every position has meaning** (per
  the TE `test PGM naming rule.xlsx`). Positions 1+2 = test platform:
  `1x`=Sigurd(矽格), `2x`=Giga(全智), `3x`=Lingsen(菱生), `5x`=Carsem,
  `6x`=JCET(長電), `7x`=ASEM, `8x`=TFEM, `9x`=天水華天, `0x`=default/template.

## Gotchas (highest-signal — data-janitor traps)

- **Unify the normalizer once, not per-ETL**: IC-YMS originally had three ETL
  scripts each with their own copy → versions diverged → joins broke. Pull
  normalization into ONE shared module every loader imports. (Divergent copies are
  the silent root cause of "the lot is in both tables but won't join".)
- **Unknown code → return RAW, not None**: a code that matches no pattern is passed
  through unchanged, never dropped. Dropping unparseable ids loses real lots; the
  naming-rule sheet "可能未涵蓋所有 code".
- **Cite the naming-rule source**: the 7-digit platform map comes from a specific
  xlsx sheet (`naming Rule`). It's reverse-engineered domain knowledge, not a
  guess — footer the source; codes 00-09 are reserved/template (treat as default).
- **Don't truncate the variant**: every one of the 7 digits encodes something (test
  platform, program rev, …). Stripping it loses provenance.
- **Yield-fraction unit trap**: a yield metadata value can be `95` (percent) or
  `0.95` (fraction) depending on source — normalize the unit at the boundary or
  SBL/yield math is off by 100×.
- **Subcon completeness**: data spans multiple packaging subcons (SG / GS / JCET /
  Carsem); a join that looks complete may be missing a subcon. Check per-subcon
  coverage, not an aggregate row count (cross-machine/source coverage trap).
- **Legacy prefix knowledge is real domain**: `AS→RTC`, `FT lot→product` mappings
  aren't guessable — they encode this fab's SAP history. Keep them in the shared
  module with a comment on provenance.
