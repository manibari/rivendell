---
name: Knowledge Graph
loop: knowledge
pdca: act
description: Three-Layer Memory System for structured entity tracking — durable facts about people, companies, and projects as atomic JSONL entries with living summaries, written via scripts/kg.py. TRIGGER when encountering durable facts (job change, decision, preference, milestone) during conversation, or user says "remember", "recall", "what do we know about", "/knowledge-graph". SKIP for engineering learnings (self-improving-agent), session workflow patterns (session-harvest), or project-scoped memory (auto memory).
when_to_use: when encountering durable facts about people, companies, or projects during conversation, or when user asks to remember/recall/look up entity information
version: 2.0.0
tags: [memory, knowledge, entities]
languages: all
user_invocable: true
---

# Knowledge Graph

Manages a Three-Layer Memory System for compounding knowledge across sessions.

## Architecture

### The Three Layers

1. **Entity Knowledge** (`~/.claude/knowledge/`) — Structured facts about people, companies, and projects stored as atomic JSONL entries with living summaries
2. **Auto Memory** (`~/.claude/projects/*/memory/`) — Session logs, decisions, and events captured by the existing auto memory system
3. **Persistent Memory** (`MEMORY.md`) — High-level patterns, preferences, and agent-wide context

The knowledge graph (Layer 1) is the durable, structured layer. Conversations feed it; synthesis distills it.

### The Compounding Flywheel

```
Conversations → Durable facts encountered → Inline Fact Extraction → Entity Facts
                                                                          |
                                    Manual Synthesis (on request) → Living Summaries
                                                                          |
                                                    Richer Context → Better Conversations
```

Every conversation makes the agent smarter. Facts compound. Summaries stay fresh. Context improves over time.

### Integration with Existing Memory System

This skill works alongside the existing auto memory system. Auto memory captures broad session context; the knowledge graph adds **structured entity tracking** on top. They complement each other:

- Auto memory = chronological, session-scoped, broad
- Knowledge graph = entity-scoped, durable, structured

## Directory Structure

```
~/.claude/knowledge/
├── people/<slug>/       → summary.md + facts.jsonl
├── companies/<slug>/    → summary.md + facts.jsonl
└── projects/<slug>/     → summary.md + facts.jsonl
```

## Fact Schema (JSONL -- one object per line)

```json
{
  "id": "<slug>-NNN",
  "fact": "The actual fact in plain English",
  "category": "relationship|milestone|status|preference|context|decision",
  "ts": "YYYY-MM-DD",
  "source": "conversation|manual|inference",
  "status": "active|superseded",
  "supersedes": "<id>"
}
```

### Rules

1. **Append-only** -- never edit or delete lines in facts.jsonl
2. **Supersede, don't delete** -- when a fact changes, add a new fact with `"supersedes": "<old-id>"` and mark the old fact's status as `"superseded"` (edit that one line only)
3. **Auto-increment IDs** -- `<slug>-001`, `<slug>-002`, etc.
4. **Be atomic** -- one fact per entry, not paragraphs
5. **Skip ephemera** -- no "user said hi", no transient chat

### What Qualifies as a Durable Fact

Extract:
- Relationship changes (new job, new team, promotions)
- Life milestones (moved cities, had a baby, started a project)
- Status changes (left company, started freelancing)
- Stated preferences ("I prefer X over Y")
- Key decisions ("decided to use Rust for the backend")
- Important context ("allergic to shellfish", "works night shifts")

Skip:
- Casual conversation, jokes, greetings
- Temporary states ("feeling tired today")
- Already-known facts (check existing facts first)
- Vague or uncertain information

## Write API — scripts/kg.py (the only write path)

All writes go through `<rivendell>/scripts/kg.py`. Never hand-edit facts.jsonl —
the script owns id assignment, append-only enforcement, the surgical supersede
edit, dedup backstop, and structural validation.

```bash
# Add a fact (id auto-assigned; prints it)
python3 <rivendell>/scripts/kg.py add people alice \
  --fact "Moved to backend team at Acme" --category status [--supersedes alice-001]

# Regenerate a summary (3-8 lines from stdin; last-updated line auto-appended)
python3 <rivendell>/scripts/kg.py summary people alice <<'EOF'
Alice
Backend engineer at Acme Corp.
Recently moved from frontend.
EOF

python3 <rivendell>/scripts/kg.py init           # bootstrap dirs + git repo (idempotent)
python3 <rivendell>/scripts/kg.py dump --active-only   # compact dump for prompts
python3 <rivendell>/scripts/kg.py verify         # structural check, exit 0/1
```

`KG_ROOT` env var overrides the storage root (default `~/.claude/knowledge`) —
use it to isolate tests. The knowledge dir is its own git repo (created by
`init`); `bin/sk-facts-cron` uses that git as a transaction boundary.

## Inline Fact Extraction (During Conversation)

Automated extraction is handled by `bin/sk-facts-cron` (daily 21:30, mines
recent session transcripts). Inline extraction remains for interactive
sessions, when a durable fact surfaces in conversation:

```
1. Notice a durable fact in the conversation (see "What Qualifies" above)
2. Determine entity type (person/company/project) and slug
3. Check existing facts (kg.py dump) -- skip if already known
4. Add via kg.py add (use --supersedes <old-id> if it contradicts an existing fact)
5. Briefly confirm to user: "Noted: <fact summary> for <entity>"
```

Do NOT extract facts silently in the background. Always inform the user when a fact is recorded.

## Manual Synthesis

Triggered when user says **"synthesize knowledge"** or **"/knowledge-graph synthesize"**.

Claude may also proactively suggest synthesis when it notices summaries are stale (e.g., many new facts since last summary update).

```
1. List all entities in ~/.claude/knowledge/
2. For each entity with facts modified since last synthesis:
   a. Load all facts from facts.jsonl
   b. Filter to status: "active" only
   c. Write a new summary.md (3-8 lines):
      - Who/what is this entity
      - Current relationship/status
      - Key active facts
      - Last updated date
   d. Mark any contradicted facts as superseded
3. Report what was synthesized
```

## Entity Lookup

When context about an entity is needed:

```
1. Check ~/.claude/knowledge/<type>/<slug>/summary.md first (cheap)
2. Only load facts.jsonl if summary is stale or more detail needed
3. Fall back to searching auto memory files if entity not yet in the graph
```

## Low-token Recall Policy

To minimize token usage, recall should be **triggered**, not automatic.

### Rules

1. **Only recall on triggers:**
   - Proper nouns (names of people, companies, projects you track)
   - Explicit recall phrases: "remember", "recall", "what do we know about"
   - Project keywords that match entity slugs

2. **Inject summary.md only** (max 5 lines) -- never inject facts.jsonl unless:
   - User explicitly asks for details/specifics
   - Summary is stale or missing
   - Contradictory information needs resolution

3. **Use a single profile summary** when the topic is preferences or planning

### Why This Matters

- **No recall unless triggered** -- most messages skip recall entirely
- **Summaries only** -- very short injections (5 lines vs potentially hundreds of facts)
- **No raw facts unless requested** -- keeps context window lean

## Creating New Entities

When you encounter a new person/company/project worth tracking:

```bash
# First fact creates the entity folder automatically
python3 <rivendell>/scripts/kg.py add people alice \
  --fact "Frontend engineer at Acme Corp, works on the design system" --category context

# Initial summary
python3 <rivendell>/scripts/kg.py summary people alice <<'EOF'
# Alice
Frontend engineer at Acme Corp.
Works on the design system team.
EOF
```

## User-Invocable Commands

When user says `/knowledge-graph`:

- `/knowledge-graph` -- show all tracked entities (list directories)
- `/knowledge-graph synthesize` -- run manual synthesis for all stale entities
- `/knowledge-graph lookup <name>` -- look up a specific entity
- `/knowledge-graph add <type> <slug>` -- create a new entity interactively
- `/knowledge-graph status` -- show entity count, last synthesis date, recent facts

## Setup

### 1. Create Directory Structure

```bash
python3 <rivendell>/scripts/kg.py init   # dirs + git repo, idempotent
```

### 2. Add to CLAUDE.md or Project Instructions

```markdown
### Knowledge Graph -- Entity Memory
- Save durable facts to ~/.claude/knowledge/<type>/<slug>/facts.jsonl (append-only JSONL)
- Never delete facts -- supersede instead ("status":"superseded","supersedes":"old-id")
- When encountering a new notable entity, create its folder + initial fact + summary
- Only recall on triggers (proper nouns, "remember/recall", or project keywords)
- Inject summary.md only (max 5 lines); never inject facts.jsonl unless asked
```

## Credits

Adapted from [jdrhyne/agent-skills knowledge-graph](https://github.com/jdrhyne/agent-skills/tree/main/clawdbot/knowledge-graph) for Claude Code.
