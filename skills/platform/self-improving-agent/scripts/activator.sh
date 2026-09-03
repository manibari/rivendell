#!/usr/bin/env bash
# Hook: UserPromptSubmit
# Purpose: Reminds Claude to evaluate if anything should be logged, AND routes
#          generic vs project-specific learnings to the correct vault.
# Input: JSON on stdin (Claude Code hook payload)
# Output: Plain text reminder to stdout

# Read and discard stdin (required by hook protocol)
cat > /dev/null

cat <<'EOF'
[Self-Improvement Reminder] After completing this task, evaluate if anything should be logged:

Routing — pick the right vault before writing:
- 🌍 Generic (macOS, git, shell, JS/Python framework gotchas, common APIs)
    → ~/.claude/learnings/LEARNINGS.md (cross-project staging buffer)
    → after 2+ recurrences, promote a dense rule to ~/.claude/CLAUDE.md
- 🏛️ Platform-meta (rivendell, gstack, etc. — applies across YOUR projects but is
    tied to one toolchain you maintain)
    → that platform's <repo>/.claude/CLAUDE.md (if it's a rule) or
       <repo>/.learnings/LEARNINGS.md (if it's a history entry)
- 🏠 Project-specific (schemas, paths, business logic of THIS codebase)
    → <current-project>/.learnings/LEARNINGS.md

What to log:
- Did a command fail? → ERRORS.md in the correct vault
- Did the user correct you? → LEARNINGS.md, category: correction
- Was your knowledge outdated? → LEARNINGS.md, category: knowledge_gap
- Did you find a better approach? → LEARNINGS.md, category: best_practice
- Did the user request a missing capability? → FEATURE_REQUESTS.md (project vault)

Quick test for routing: "Would I want this rule when working in a totally different
project tomorrow?" Yes → global. No → project-local.

Use the self-improving-agent skill format. Create the target directory if missing.
EOF
