#!/usr/bin/env bash
# Hook: PostToolUse (matcher: Bash)
# Purpose: Detects errors in Bash tool output and reminds Claude to log them
# Input: JSON on stdin (Claude Code hook payload with tool_input and tool_output)
# Output: Plain text reminder to stdout (only when errors detected)

# Read the hook input from stdin
INPUT=$(cat)

# Extract the tool output from the JSON payload
# Claude Code PostToolUse sends: {"tool_name": "Bash", "tool_input": {...}, "tool_output": "..."}
OUTPUT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # tool_output may be nested; try common locations
    out = data.get('tool_output', data.get('output', ''))
    if isinstance(out, dict):
        out = out.get('stdout', '') + out.get('stderr', '')
    print(str(out))
except:
    print('')
" 2>/dev/null)

# Check for error indicators
HAS_ERROR=false

# Check exit code if available in the payload
EXIT_CODE=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    code = data.get('tool_output', {})
    if isinstance(code, dict):
        print(code.get('exit_code', code.get('exitCode', '0')))
    else:
        print('0')
except:
    print('0')
" 2>/dev/null)

if [ "$EXIT_CODE" != "0" ] && [ -n "$EXIT_CODE" ]; then
    HAS_ERROR=true
fi

# Check output text for error patterns (case-insensitive)
if echo "$OUTPUT" | grep -qiE '(error:|Error:|ERROR|failed|FAILED|fatal:|FATAL|panic:|command not found|permission denied|no such file|segmentation fault|traceback|exception|abort)'; then
    HAS_ERROR=true
fi

# Only output if an error was detected
if [ "$HAS_ERROR" = true ]; then
    cat <<'EOF'
[Error Detected] A command error was detected. Consider logging to .learnings/ERRORS.md using the self-improving-agent skill format:
- Include the exact error message
- Note the command that failed
- Add reproduction context
- Suggest a fix if identifiable
Create .learnings/ directory if it doesn't exist.
EOF
fi
