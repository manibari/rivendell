---
name: slide-office-hours
loop: sales
pdca: check
description: >
  Red-team review for B2B presales deck storyline.md before slide generation. Routes by
  (stage × profile) matrix; rejects 公開資料 voice. Outputs signed-off storyline consumed
  by slide-workflow / pitch-deck.
  TRIGGER: "/slide-office-hours", "review storyline", "壓力測試 storyline", "簡報前置審核".
  SKIP: storyline.md already `status: signed-off`.
tags: [docs, presales, review]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Edit, Bash, Grep, Glob"
---

# Slide Office Hours

Storyline red-team gate. **Reviews** a user-written `storyline.md`, never **proposes** content.

The leverage point in deck-building is storyline review, not slide generation. AI's default content voice = 「公開資料合理推測」voice = the failure mode this skill exists to catch.

## Hard Rules

These four rules are non-negotiable. Violating any of them = skill failure.

1. **Never propose storyline content.** Only challenge what user wrote. If user asks「那我該寫什麼」, return:
   > 我不能 propose — 我能做的是挑戰你提的東西。先寫個 bullet 我來戳。
2. **Never let 公開資料 voice slip through.** Auto-grep for trigger phrases in the storyline:
   - 「依公開資料」/「根據公開資料」
   - 「業界趨勢顯示」/「市場上常見」/「業界普遍」
   - 「根據公開報告」/「市場研究指出」
   - 「依產業報告」
   Any hit = automatic ❌, force user to rewrite as operator-level claim or remove.
3. **Single bullet rewrites only.** When user revises after ❌, user does it. Skill may rewrite at most ONE bullet to demonstrate the operator-voice pattern, never a whole section. If skill catches itself drafting paragraphs of storyline content → stop, return work to user.
4. **Gate fully green or no sign-off.** Don't accept「先這樣，到時候再改」. Either all 3 layers pass, or status stays `draft`.

---

## Workflow

### Step 1: Locate storyline.md

```bash
# default location
ls -la storyline.md 2>/dev/null

# fallback: search under cwd (warn if multiple)
find . -name "storyline.md" -not -path "./node_modules/*" -not -path "./.next/*" 2>/dev/null
```

If none found:
> 沒找到 storyline.md。複製 template 寫一份再來：
> `cp ~/.claude/skills/slide-office-hours/storyline-template.md ./storyline.md`
>
> 寫完再呼叫 /slide-office-hours review。

If multiple found, ask user which one.

### Step 2: Identify (stage × profile)

Read storyline frontmatter. Required fields:

| Field | Allowed values |
|-------|---------------|
| `stage` | `first-call` / `post-discovery` / `proposal` / `final-pitch` |
| `profile` | `傳產中小` / `大型科技廠` / `公部門` / `新創` |
| `client` | <客戶名> |
| `audience` | <工廠長 / IT主管 / CFO / 老闆 / other> |
| `status` | `draft` (initial) → `signed-off` (after sign-off) |

If any required field missing → ❌ Layer 0, force user to fill before review starts.

### Step 3: Run 3-layer checklist (fail-fast on each)

#### Layer 1: Universal failures (any deck)

| Check | Fail condition | 修法（不寫具體內容）|
|-------|---------------|------------------|
| 公開資料 voice | grep hits 任一 trigger phrase | 改寫成 operator-level 猜測或刪除 |
| Exit criteria | 寫不出 / 「讓客戶了解我們」/ 「建立關係」/ 任何沒有具體動作的句子 | 改成「什麼人、做什麼、什麼時候」三件事都齊 |
| Organizing structure | 沒有 / 自相矛盾 / 寫了但跟 slide 骨架對不起來 | 重定義結構，且每個 operator 猜題都對到結構的一格 |
| Fact-check items | 少於 5 個 / 任一個沒附 source | 補到 5 個都有 source |
| Solutions | capability雜燴（>5 條 bullet 或沒有 focused angle）| 收斂到 1-3 個 focused angle，砍掉「我們也能做 X、Y、Z」的雜燴 |

#### Layer 2: Stage-specific

| Stage | Required content | Fail condition |
|-------|-----------------|---------------|
| first-call | operator_guesses ≥ 3 | < 3 |
| post-discovery | 「Discovery learned X, proposal changed to Y」section 存在 | 缺漏 |
| proposal | scope 紅線 + 退場機制 | 缺其一 |
| final-pitch | 「為什麼選我們不選 [具體對手名]」段落 | 沒寫 / 寫成「市場領先」這種空話 |

#### Layer 3: Profile-specific

| Profile | Required content | Fail condition |
|---------|-----------------|---------------|
| 大型科技廠 | operator_guesses 每條都有 cross-customer / cross-industry pattern 支撐 | 任一條只是憑空猜 → reject 並標記「自殺風險：客戶內部 AI/IT team 很可能比你懂自家製程」 |
| 大型科技廠 | differentiation_target 寫明（同業 / 顧問 / 雲端商 / 客戶內部 / other）| 沒寫 / 寫成「市場」這種空話 |
| 傳產中小 | operator_guesses ≥ 3（可不需 cross-customer 支撐） | < 3 |
| 公部門 | 對到法規 + 預算科目 + 首長交代對象 | 缺其一 |
| 新創 | 對到速度 / 對齊 / iteration cadence | 都沒提 |

### Step 4: Output review report

Format:

```
## Layer 1: Universal
- ✅ 公開資料 voice — clean
- ❌ Exit criteria — 寫成「建立關係」太籠統
  修法：改成「什麼人、做什麼、什麼時候」
- ✅ Organizing structure — 四面向定義清楚
- ❌ Fact-check — 只有 3 個，不夠
  修法：補到 5 個 + source
- ✅ Solutions — 三條 focused angle

## Layer 2: first-call
- ✅ operator_guesses 4 個

## Layer 3: 傳產中小
- ✅ operator_guesses ≥ 3

⚠️ 2 個 ❌，無法簽核。修完再叫我。
```

不寫具體應該怎麼補的內容（不可違反 Hard Rule 1）。

### Step 5: User revises → re-run Layer 1-3

Loop until all green.

### Step 6: Sign-off

When all green, update `storyline.md` frontmatter via `Edit`:

```yaml
status: signed-off
signed_at: 2026-05-03T14:32:00+08:00  # ISO 8601 with TZ
signed_by: slide-office-hours
```

Then output:

```
✅ Storyline signed off.
- Layer 1 (universal): all green
- Layer 2 (first-call): all green
- Layer 3 (傳產中小): all green

下一步：
- /slide-workflow — 進 outline → HTML → PPTX 流程
- /pitch-deck — 投資人 deck orchestrator
- /sales-material — 客戶素材組裝（如果是已有素材庫的提案）
```

---

## (Stage × Profile) routing reference

完整 16 cell matrix。以 first-call × 傳產中小（光泉）vs first-call × 大型科技廠（力成）對照最有教育意義：

| 軸 | 光泉（傳產中小）| 力成（大型科技廠）|
|---|---|---|
| operator猜題有效性 | ✅ 最有效 — 客戶 IT 弱、操作層 insight 直接 land | ⚠ 風險最高 — 客戶內部 AI/IT team 很可能比你懂 |
| 該逼問的核心 | 5 個 operator 猜題 + 不能錯的事實 | 「你比客戶內部 team 強在哪？」「cross-customer pattern 在哪？」「中華電在 OSAT / 半導體封測 case ref？」|
| 如果沒 differentiation_target | OK | reject — 自殺 |
| 如果 operator_guesses 沒 pattern 支撐 | OK | reject |

---

## Anti-Patterns

| 不要 | 要 |
|------|---|
| 替用戶 propose storyline 內容 | 只挑戰用戶寫的，最多重寫一個 bullet 示範 |
| 接受「先這樣，到時候再改」 | Gate 全綠才簽核 |
| 對科技廠放行沒 pattern 支撐的 operator 猜題 | reject + 標記「自殺風險」 |
| 對 final-pitch 不要求具體對手名 | 寫不出對手 = 沒準備好打競標 |
| 在 review 過程中替用戶腦補事實 | 事實 ≥ 5 個 + 每個都有 source，是用戶的活 |
| 跳過 stage / profile 識別直接跑 checklist | 先確認 (stage × profile)，checklist 要對位 |

---

## When to invoke vs skip

**Invoke when:**
- 任何 B2B 客戶 deck 動工前
- 既有 storyline.md 但 status 不是 `signed-off`
- 用戶說「我要做 [客戶] deck」但沒有 storyline.md
- slide-workflow / pitch-deck Gate 0 觸發

**Skip when:**
- storyline.md 已 `signed-off` 且用戶要進下一步生成
- 純內部 deck（不是給客戶 / 投資人 / 競標審查的）
- 用戶明確說「不做 storyline review，跳過 gate」（slide-workflow 的 override 路徑）
