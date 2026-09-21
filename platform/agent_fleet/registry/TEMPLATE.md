---
# ═══════════════════════════════════════════════════════════════════════
# Agent Registry schema v2 — one file per agent. Copy this to <name>.md.
# Registry is the ONLY committed SoT. agents.conf is generated (not in git).
# See docs/requirements/agent-registry.md.
# ═══════════════════════════════════════════════════════════════════════

schema_version: 2

# ── identity / scheduling (ALL kinds) ──
name: my-agent          # REQUIRED. kebab-case. MUST equal the filename stem.
kind: script            # REQUIRED. script | claude | service | ooda
enabled: true           # false = not scheduled (replaces commenting out a conf line)
project: rivendell      # REQUIRED. relative to PROJECTS_DIR. NEVER an absolute path.
entry: bin/sk-foo-cron  # REQUIRED for script/claude/service. Empty for ooda (runs via executor).
extra_args: ""          # optional, passed to entry

schedule:
  type: interval        # interval | calendar | calendar_multi | keepalive
  value: 28800          # interval=seconds; calendar=H:MM or W:H:MM; keepalive="-"
                        # For kind:ooda this is the HEARTBEAT (when it wakes), not a task trigger.
log_dir: reports        # relative to the project root
label: ""               # optional override. Default: com.sk.agent.<project>.<name>.
                        # Legacy services (com.sk.dashboard.api) set it here.

# ── rule layer (kind: claude | ooda) — machine-enforced by the executor ──
# Omit this whole block for kind: script | service.
skills: []              # skill whitelist = the agent's action space
tools: ""               # --allowedTools (least privilege)
paths_forbid: []        # paths the agent may never write
budget_usd: 0           # per-wake spend cap

# ── governance layer (absorbed from the retired .claude/agents.json) ──
# Only for code-writing claude agents. Omit for read-only or ooda agents.
# merge_strategy: auto      # auto | pr
# allowed_paths: []
# forbidden_paths: []
# max_files_changed: 0
# qa_pre_commit: off        # off | auto | <script path>

# ── autonomy layer (kind: ooda ONLY) ──
# pdca_role: check          # plan | do | check | act — sets the fleet handoff topology
# mission: ""               # target STATE (not a task): "keep the world looking like X"
# mission_metric: ""        # a decidable done-signal (see autoresearch goal+metric)
# memory_dir: agents/state/<name>/   # journal the agent reads on wake, writes before sleep
# observe: []               # world-state sources the agent may READ (paths / read-only DB)
# authority:                # Decide's boundary (semantic; tools/paths are the hard layer)
#   can: []                 #   action types it may Act on directly
#   escalate: []            #   beyond authority → write a memorial (奏摺), don't act
# handoff:
#   on_finding: ""          # who a finding goes to (one edge of the PDCA topology)
# persona_card: docs/personas/<name>.md   # optional narrative-layer ref
---

## Mission (narrative layer)

Free prose: tone, the background behind the judgment rules, output format examples.
The executor uses this as prompt material only — every ENFORCED thing lives in the
frontmatter rule layer above.
