// Workflow playbook — Peter's personal flow map, mirrors ~/.claude/CLAUDE.md.
// Single source of truth; edit here, the page re-renders on next build.
// Companion mockup: ~/Documents/Peter/workflow-map.html (2026-05-13 baseline).

export type ChipCategory = "core" | "gstack" | "critical";

export interface Chip {
  key: string;
  category: ChipCategory;
}

export interface OptionalRow {
  label: string;
  chips: Chip[];
  /** Optional second label appearing inline after the first chip group. */
  secondLabel?: string;
  secondChips?: Chip[];
  inlineNote?: string;
}

export interface Step {
  num: string;
  action: string;
  detail?: string;
  chips?: Chip[];
  optionals?: OptionalRow[];
  hardGate?: string;
  inlineNote?: string;
}

export interface Branch {
  id: string;
  label: string;
  lead?: string;
  steps: Step[];
}

export interface MaintenanceRow {
  when: string;
  chips: Chip[];
  /** Sequence separator between chip groups, e.g. "→" */
  sequence?: { connector: "arrow" | "then"; chips: Chip[] }[];
}

export type WorkflowId = "ui" | "backend" | "slide" | "maintenance";

export interface Workflow {
  id: WorkflowId;
  label: string;
  heading: string;
  lead?: { text: string; tone?: "warn" | "info" };
  steps?: Step[];
  branches?: Branch[];
  maintenance?: MaintenanceRow[];
}

// Helper to keep chip authoring terse below.
const core = (key: string): Chip => ({ key, category: "core" });
const gst = (key: string): Chip => ({ key, category: "gstack" });
const crit = (key: string): Chip => ({ key, category: "critical" });

export const workflows: Workflow[] = [
  // ───────────────────────────────────────────────────────────────────────── UI
  {
    id: "ui",
    label: "UI Feature / New Page",
    heading: "UI Feature / New Page — 10 步驟",
    lead: {
      tone: "warn",
      text: "若使用者說「幫我做 X / 新增 Y / build Z page」要先問：「要從哪個步驟開始？requirement → design → plan → 直接實作？」",
    },
    steps: [
      {
        num: "1",
        action: "驗證「why」、user story、acceptance criteria",
        chips: [core("requirement"), gst("gstack-office-hours")],
      },
      { num: "2", action: "畫螢幕轉換 + 分支", chips: [core("user-flow")] },
      { num: "3", action: "Design system / brand direction", chips: [gst("gstack-design-consultation")] },
      { num: "4", action: "產生 design variants，挑一個", chips: [gst("gstack-design-shotgun")] },
      { num: "5", action: "Mockup → 定靜態 HTML", chips: [core("mockup"), gst("gstack-design-html")] },
      {
        num: "6",
        action: "實作任務清單 + Plan Review",
        chips: [core("planning-with-files")],
        optionals: [
          {
            label: "Plan reviews:",
            chips: [
              gst("gstack-plan-eng-review"),
              gst("gstack-plan-design-review"),
              gst("gstack-plan-ceo-review"),
              gst("gstack-autoplan"),
            ],
            inlineNote: "大功能用 /gstack-autoplan 一鍵跑全部",
          },
        ],
      },
      {
        num: "7",
        action: "實作（implement）",
        optionals: [
          {
            label: "遇到 bug:",
            chips: [gst("gstack-investigate")],
            secondLabel: "重構時 lock 穩定區:",
            secondChips: [gst("gstack-freeze"), gst("gstack-unfreeze")],
          },
          {
            label: "破壞性命令前:",
            chips: [crit("gstack-careful")],
            secondLabel: "獨立第二意見:",
            secondChips: [gst("gstack-codex")],
          },
        ],
      },
      { num: "8", action: "Pre-commit diff review", chips: [gst("gstack-review")] },
      {
        num: "9",
        action: "QA — headless browser UI flow test",
        chips: [gst("gstack-qa")],
        optionals: [
          {
            label: "Report-only mode:",
            chips: [gst("gstack-qa-only")],
            secondLabel: "視覺一致性:",
            secondChips: [gst("gstack-design-review")],
          },
        ],
      },
      {
        num: "10",
        action: "部署",
        chips: [gst("gstack-land-and-deploy"), gst("gstack-ship")],
        inlineNote: "land-and-deploy = CI/CD 環境，ship = 非 CI 環境",
        optionals: [
          {
            label: "部署後:",
            chips: [gst("gstack-canary"), gst("gstack-document-release")],
          },
        ],
      },
    ],
  },

  // ───────────────────────────────────────────────────────────────────── BACKEND
  {
    id: "backend",
    label: "Backend / Bug Fix / Refactor",
    heading: "Backend-only / Bug Fix / Refactor — 5 步驟",
    lead: {
      tone: "info",
      text: "Exceptions: 使用者明確說「直接實作」或「skip design」→ 跳到 step 2",
    },
    steps: [
      { num: "1", action: "Root cause first（bugs）", chips: [gst("gstack-investigate")] },
      { num: "2", action: "實作" },
      { num: "3", action: "Diff review", chips: [gst("gstack-review")] },
      {
        num: "4",
        action: "破壞性命令前確認",
        chips: [crit("gstack-careful")],
        inlineNote: "drop table / rm / force push 前",
      },
      {
        num: "5",
        action: "部署",
        chips: [gst("gstack-land-and-deploy"), gst("gstack-ship")],
        optionals: [
          {
            label: "效能敏感:",
            chips: [gst("gstack-benchmark")],
            secondLabel: "部署後監控:",
            secondChips: [gst("gstack-canary")],
          },
        ],
      },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────── SLIDE
  {
    id: "slide",
    label: "Slide / Deck Building",
    heading: "Slide / Deck Building — 先分流",
    lead: {
      tone: "warn",
      text: "接到「做 X 簡報 / 準備 Y 提案 / 幫我做 deck」要先問：「哪一類 deck？投資人 BP / 客戶客製提案 / B2B 首次拜訪 / IoT 廠務報告 / 高階主管通用」",
    },
    branches: [
      {
        id: "branch-a",
        label: "A. 投資人 BP",
        steps: [
          {
            num: "A",
            action: "投資人 BP / Pitch Deck",
            detail: "含 discovery interview，內部完整 skill flow",
            chips: [core("pitch-deck")],
          },
        ],
      },
      {
        id: "branch-b",
        label: "B. 客戶客製提案",
        steps: [
          {
            num: "B",
            action: "客戶客製提案",
            detail: "從素材庫組裝，匹配 sales-customer-intel + case studies + solutions + 補助",
            chips: [core("sales-material")],
          },
        ],
      },
      {
        id: "branch-c",
        label: "C. IoT / 廠務報告",
        steps: [
          {
            num: "C",
            action: "IoT / 廠務時序資料報告",
            detail: "CSV/Excel → 視覺化報告 + PPTX；UPW/RO/壓縮機/冷凍機",
            chips: [core("iot-factory-report")],
          },
        ],
      },
      {
        id: "branch-d",
        label: "D. B2B 首拜 / 通用",
        lead: "D. B2B 首次拜訪 / 高階主管通用 — 8 步驟通用流程",
        steps: [
          {
            num: "1",
            action: "情蒐",
            detail: "operator-level 猜製程 / 業務流程 > 公開資料推測（B2B first-call 尤甚）",
            chips: [core("sales-customer-intel"), core("metadata-workshop")],
            optionals: [
              { label: "能與客戶對話:", chips: [core("discovery-interview")] },
            ],
          },
          {
            num: "2",
            action: "Storyline 草稿",
            detail: "USER-OWNED — Peter 寫 storyline.md，AI 補洞",
          },
          {
            num: "3",
            action: "Storyline Red Team",
            chips: [core("slide-office-hours")],
            hardGate: "硬 gate — storyline.md 需 status: signed-off 才能往下",
          },
          {
            num: "4",
            action: "風格鎖定",
            optionals: [
              {
                label: "有參考 PPTX:",
                chips: [core("slide-template-extractor")],
                secondLabel: "從零開始:",
                secondChips: [core("ui-ux-pro-max"), gst("gstack-design-consultation")],
              },
            ],
          },
          { num: "5", action: "大綱 → 內容（7 階段）", chips: [core("slide-workflow")] },
          {
            num: "6",
            action: "生成",
            optionals: [
              {
                label: "PPTX:",
                chips: [core("office-pptx")],
                secondLabel: "Google Slides:",
                secondChips: [core("gdoc-report-builder")],
              },
              { label: "HTML deck:", chips: [gst("gstack-design-html")] },
            ],
          },
          {
            num: "7",
            action: "文字打磨",
            chips: [core("de-slopify")],
            inlineNote: "繁中模式 + 講者備註",
          },
          { num: "8", action: "審查視覺一致性", chips: [gst("gstack-design-review")] },
        ],
      },
    ],
  },

  // ─────────────────────────────────────────────────────────────── MAINTENANCE
  {
    id: "maintenance",
    label: "Recurring Maintenance",
    heading: "Recurring Maintenance",
    lead: { tone: "info", text: "遇到固定情境直接 trigger 對應 skill，不需走完整 workflow" },
    maintenance: [
      { when: "遇到不明 bug", chips: [gst("gstack-investigate")] },
      {
        when: "每次 ship 前",
        chips: [crit("gstack-careful")],
        sequence: [
          { connector: "arrow", chips: [gst("gstack-review")] },
          { connector: "arrow", chips: [gst("gstack-qa")] },
        ],
      },
      {
        when: "每次 ship 後",
        chips: [gst("gstack-canary")],
        sequence: [{ connector: "arrow", chips: [gst("gstack-document-release")] }],
      },
      { when: "定期 UI 健檢（不修）", chips: [gst("gstack-qa-only")] },
      {
        when: "重構時保護穩定區域",
        chips: [gst("gstack-freeze")],
        sequence: [{ connector: "then", chips: [gst("gstack-unfreeze")] }],
      },
      { when: "需要獨立第二意見", chips: [gst("gstack-codex")] },
      { when: "每週 retro", chips: [gst("gstack-retro")] },
      { when: "安全審計（上線前）", chips: [gst("gstack-cso")] },
      { when: "gstack 有 UPGRADE_AVAILABLE", chips: [gst("gstack-upgrade")] },
      { when: "學到新東西 / 踩坑", chips: [gst("gstack-learn")] },
    ],
  },
];

// ─────────────────────────────────────────────────────────────── SKILL DETAILS
// Surfaced on click in the SkillModal. Mirrors mockup's skillData object.

export interface SkillDetail {
  desc: string;
  trigger?: string;
  skip?: string;
}

export const skillDetails: Record<string, SkillDetail> = {
  requirement: {
    desc: "定義結構化的需求、user stories、acceptance criteria。",
    trigger: "user 說 'define requirement' / 'write user story' / 'what should we build'；或描述一個沒清楚範疇的功能想法",
    skip: "需求已存在，user 在問如何實作",
  },
  "gstack-office-hours": {
    desc: "YC Office Hours 風格 — 兩模式。Startup mode: 六個 forcing questions 暴露需求現實 / status quo / specific 程度 / 最窄 wedge / 觀察 / future-fit。Builder mode: side project / hackathon / 學習 / open source 的 brainstorm。會存 design doc。",
    trigger: "'brainstorm this' / 'I have an idea' / 'help me think through this' / 'office hours' / 'is this worth building'；user 描述新產品想法、問是否值得做、想在寫 code 前思考設計決策",
  },
  "user-flow": {
    desc: "用 Mermaid flowchart 設計 user workflow diagram，涵蓋 happy path + error branches。",
    trigger: "'design flow' / 'draw flowchart' / 'user journey'；需要 map 螢幕轉換 + decision points",
    skip: "user 在問 system architecture 或 data flow diagram（不是 user flow）",
  },
  "gstack-design-consultation": {
    desc: "Design consultation — 了解你的產品、研究 landscape、提出完整 design system + 產 font+color preview。建 DESIGN.md 當 source of truth。既有網站用 /plan-design-review 反推 system。",
    trigger: "'design system' / 'brand guidelines' / 'create DESIGN.md'；開新專案 UI 沒既有 DESIGN.md 時主動建議",
  },
  "gstack-design-shotgun": {
    desc: "Design shotgun — 產多個 AI design variants、開比較 board、收 structured feedback、迭代。standalone design exploration。",
    trigger: "'explore designs' / 'show me options' / 'design variants' / 'visual brainstorm' / 'I don't like how this looks'",
  },
  mockup: {
    desc: "三種精細度的 UI mockup（ASCII → static HTML → interactive HTML），讀 project design system 拿 tokens / constraints，可 export Figma。",
    trigger: "'/mockup' / 'create wireframe / mockup / UI prototype'；dev-process-gate 偵測 missing wireframe/mockup 階段",
    skip: "已經在寫 component、後端工作、或問 design system 建立（不是 mockup 建立）",
  },
  "gstack-design-html": {
    desc: "Design finalization — 產 production-quality Pretext-native HTML/CSS。Text 真實 reflow、heights computed、layout 動態。30KB overhead、zero deps。",
    trigger: "'finalize this design' / 'turn this into HTML' / 'build me a page' / 'implement this design'",
  },
  "planning-with-files": {
    desc: "Manus-style file-based planning：task_plan.md、findings.md、progress.md。",
    trigger: "'/planning-with-files'；複雜多步驟專案；工作會 >5 tool calls 需要 progress tracking",
    skip: "任務簡單可直接執行；user 要 engineer 用的實作計畫（用 writing-plans）",
  },
  "gstack-plan-eng-review": {
    desc: "Eng manager 模式 plan review — 鎖定執行計畫：architecture / data flow / diagrams / edge cases / test coverage / performance。",
    trigger: "'review the architecture' / 'engineering review' / 'lock in the plan'",
  },
  "gstack-plan-design-review": {
    desc: "設計師視角的 plan review — 互動式像 CEO / Eng review。每個 design 維度 0–10 評分，解釋怎樣才 10，再修 plan 達到。",
    trigger: "'review the design plan' / 'design critique'",
  },
  "gstack-plan-ceo-review": {
    desc: "CEO / founder 模式 plan review — 重新想問題、找 10-star product、挑戰前提、scope 擴張。四模式：SCOPE EXPANSION / SELECTIVE EXPANSION / HOLD SCOPE / SCOPE REDUCTION。",
    trigger: "'think bigger' / 'expand scope' / 'strategy review' / 'rethink this' / 'is this ambitious enough'",
  },
  "gstack-autoplan": {
    desc: "Auto-review pipeline — 讀完整 CEO / design / eng / DX review skills 順序跑，用 6 個 decision principles 自動決策。Final approval gate 浮現 taste decisions。一個指令、完整 reviewed plan。",
    trigger: "'auto review' / 'autoplan' / 'run all reviews' / 'make the decisions for me'",
  },
  "gstack-investigate": {
    desc: "Systematic debugging with root cause investigation。四階段：investigate / analyze / hypothesize / implement。Iron Law：no fixes without root cause。",
    trigger: "'debug this' / 'fix this bug' / 'why is this broken' / 'investigate this error' / 'root cause analysis'",
  },
  "gstack-freeze": {
    desc: "Lock 穩定區域，防止意外修改。重構時 freeze 不該動的部分，完成後 unfreeze。",
    trigger: "重構時保護穩定區域",
  },
  "gstack-unfreeze": {
    desc: "解鎖 frozen 區域。",
    trigger: "freeze 區域完成保護期、可恢復編輯",
  },
  "gstack-careful": {
    desc: "Safety guardrails for destructive commands — 警告 rm -rf / DROP TABLE / force-push / git reset --hard / kubectl delete 等。User 可逐條 override。Prod / live system / shared 環境用。",
    trigger: "'be careful' / 'safety mode' / 'prod mode' / 'careful mode'",
  },
  "gstack-codex": {
    desc: "獨立第二意見對 implementation 進行 review。",
    trigger: "需要 independent verification / 第二人觀點 review code 或設計",
  },
  "gstack-review": {
    desc: "Pre-commit diff review — 在 commit 前 review 變更。",
    trigger: "每次 commit / ship 前；'review my diff'",
  },
  "gstack-qa": {
    desc: "系統 QA 測 web app 並修 bugs — 跑 QA testing 後 iteratively 修 source code、原子 commit 每個 fix、re-verify。三 tier：Quick / Standard / Exhaustive。",
    trigger: "'qa' / 'test this site' / 'find bugs' / 'test and fix'；user 說 feature 準備好測試或問 'does this work?'",
  },
  "gstack-qa-only": {
    desc: "Report-only QA testing — 系統測試 web app 並產 structured report（health score / screenshots / repro steps），但不修。",
    trigger: "'just report bugs' / 'qa report only' / 'test but don't fix'",
  },
  "gstack-design-review": {
    desc: "Live site 視覺一致性 review — 不是 plan review。",
    trigger: "ship 後做視覺審查；視覺一致性 check",
    skip: "Plan 階段的 design review 用 /gstack-plan-design-review",
  },
  "gstack-land-and-deploy": {
    desc: "Merge PR → wait CI → deploy。CI/CD 環境用。",
    trigger: "ship to prod, with CI/CD pipeline",
    skip: "Non-CI 環境用 /gstack-ship",
  },
  "gstack-ship": {
    desc: "Merge + deploy + verify。Non-CI 環境用。",
    trigger: "ship to prod, without CI/CD",
    skip: "有 CI/CD 用 /gstack-land-and-deploy",
  },
  "gstack-canary": {
    desc: "Post-deploy regression 監控 — canary deployment + 監測。",
    trigger: "部署後監測；ship 後做 canary",
  },
  "gstack-document-release": {
    desc: "Ship 後 update docs / README。",
    trigger: "ship 後 doc update",
  },
  "gstack-benchmark": {
    desc: "Performance benchmark — 改 request path / performance-sensitive code 時跑。",
    trigger: "改到 request path 或 performance-sensitive code",
  },
  "pitch-deck": {
    desc: "Pitch decks / 投資人 presentations — strategic storytelling、discovery interview、HTML slide generation、PPTX export。",
    trigger: "'做 BP' / '投資人 deck' / 'pitch deck' / '募資簡報' / 'investor presentation'",
    skip: "技術文件 / 內部 status — 用 /office-pptx",
  },
  "sales-material": {
    desc: "組裝 client-specific sales presentations — 從本地 materials library 匹配 sales-customer-intel / case studies / solutions / 補助，via html2pptx 產 PPTX。",
    trigger: "'幫我做客戶提案' / '準備 B2B 提案' / '做 X 公司的銷售簡報' / '客戶提案素材'",
    skip: "投資人 deck（用 pitch-deck）；編 existing PPTX（用 office-pptx）",
  },
  "iot-factory-report": {
    desc: "分析 factory IoT / SCADA time-series（CSV/Excel）→ 視覺報告 + PPTX。涵蓋 UPW/RO / 壓縮機 / 冷凍機。",
    trigger: "'廠務報告' / '設備分析' / 'IoT 資料分析' / 'UPW 分析' / '壓縮機報告'",
    skip: "generic CSV（用 office-xlsx）；無 sensor data 的商業報告",
  },
  "sales-customer-intel": {
    desc: "B2B customer intelligence：公司名 → web research → 可執行 sales report。WebSearch + Playwright (findbiz.nat.gov.tw 查台灣公司)。",
    trigger: "'客戶調查' / '公司調查' / '會前準備' / '情蒐' / '更新[公司名]報告'",
    skip: "stocks（用 invest-research）",
  },
  "metadata-workshop": {
    desc: "Metadata 萃取 + 整理 workshop — 客戶情境的 operator-level 製程 / 業務流程猜測比公開資料推測更有效。",
    trigger: "情蒐 / sales-customer-intel 後做 metadata 萃取",
  },
  "discovery-interview": {
    desc: "客戶 discovery interview — 能與客戶實際對話時用。",
    trigger: "能跟客戶直接對話的場合",
  },
  "slide-office-hours": {
    desc: "B2B presales deck storyline.md slide 生成前的 red-team review。依 (stage × profile) matrix routing；拒絕「公開資料」voice。",
    trigger: "'/slide-office-hours' / 'review storyline' / '壓力測試 storyline'",
    skip: "storyline.md 已 status: signed-off",
  },
  "slide-template-extractor": {
    desc: "從現有 PPTX 提取 template 風格。",
    trigger: "有參考 PPTX 要對齊風格時",
  },
  "ui-ux-pro-max": {
    desc: "UI/UX design intelligence with searchable database — 50+ styles / 97 color palettes / 57 font pairings / 25 chart types / 9 stacks。",
    trigger: "設計 UI components / 選 color palettes 或 typography / 建 landing pages / dashboards",
    skip: "backend-only / CLI tools / 純邏輯無 UI",
  },
  "slide-workflow": {
    desc: "七階段 gated presentation workflow：purpose → style → outline → content → generate → review → export。",
    trigger: "'做簡報' / '做 deck' / '準備提案' / '幫我做 slides' / '簡報流程'",
    skip: "完整 outline + locked template + '直接生成'",
  },
  "office-pptx": {
    desc: "PowerPoint (.pptx) 建立 / 編輯 / 分析 — layouts / speaker notes / comments / media。",
    trigger: "建立 / 編輯 / 分析 .pptx 或 presentations",
  },
  "gdoc-report-builder": {
    desc: "Google Slides / Docs report builder。",
    trigger: "輸出 Google Slides 格式",
  },
  "de-slopify": {
    desc: "移除 AI 生成 prose 中明顯的「slop」字眼 — 讓 text 聽起來真實人寫。",
    trigger: "發 README / docs / blog / 任何 public-facing text 前；AI 輔助寫作後",
  },
  "gstack-retro": {
    desc: "Retrospective — 每週回顧。",
    trigger: "週末或週一定期 retro",
  },
  "gstack-cso": {
    desc: "Chief Security Officer — 安全審計（上線前）。",
    trigger: "ship to prod 前；安全敏感變更",
  },
  "gstack-upgrade": {
    desc: "升級 gstack 到最新版本 — detect global vs vendored install、跑 upgrade、show 變化。",
    trigger: "'upgrade gstack' / 'update gstack'；UPGRADE_AVAILABLE 提示",
  },
  "gstack-learn": {
    desc: "Capture learnings — 學到新東西或踩坑時 log。",
    trigger: "學到新東西 / 踩坑 / 找到更好方法",
  },
};
