#!/usr/bin/env python3
"""Append a command call and emit a harmless response."""
import json
import os
import sys
from datetime import datetime, timezone

cmd, *argv = sys.argv[1:]
record = {
    "cmd": cmd,
    "argv": argv,
    "cwd": os.getcwd(),
    "ts": datetime.now(timezone.utc).isoformat(),
}
with open(os.environ["E2E_RECORDER_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(record) + "\n")

if cmd == "launchctl" and argv[:1] == ["list"] and len(argv) == 1:
    print("PID\tStatus\tLabel")
elif cmd == "docker" and argv[:1] == ["inspect"]:
    print("[]")
elif cmd == "sk-check":
    check = argv[1] if len(argv) > 1 else ""
    canned = {
        "ssot": {"total_drift": 0, "agents_conf_only": [], "projects_json_only": []},
        "disk": {"percent": 0, "status": "ok"},
        "agents": {"total_drift": 0, "defined": 1, "loaded": 0,
                   "not_loaded": [], "loaded_not_in_conf": []},
    }
    print(json.dumps(canned.get(check, {})))
elif cmd == "lsof":
    print("COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME")
