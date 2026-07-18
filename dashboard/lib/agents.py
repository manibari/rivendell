"""Read and manage launchd agent state for rivendell."""

from __future__ import annotations

import json
import plistlib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
PROJECT_DIR = Path(__file__).parent.parent.parent  # repo root
AGENT_PREFIX = "com.sk.agent."
MAINTAIN_PREFIX = "com.skills."

# Role inference from agent name/type
ROLE_MAP: dict[str, tuple[str, str]] = {
    "maintainer": ("🔧", "maintainer"),
    "tester": ("🧪", "tester"),
    "developer": ("🚀", "developer"),
    "researcher": ("📊", "researcher"),
    "audit": ("🔍", "auditor"),
    "review": ("📝", "reviewer"),
}


@dataclass
class AgentsJsonConfig:
    """Parsed config from .claude/agents.json for a specific agent."""
    description: str = ""
    merge_strategy: str = "auto"  # "auto" or "pr"
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    max_files_changed: int = 0
    qa_pre_commit: str = "off"  # "off", "auto", or script path
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInfo:
    label: str
    name: str
    project: str
    plist_path: Path
    schedule: dict[str, Any]
    loaded: bool
    installed: bool = True  # plist is in ~/Library/LaunchAgents/
    pid: int | None = None
    exit_code: int | None = None
    working_directory: str = ""
    agents_json_config: AgentsJsonConfig | None = None

    @property
    def role_badge(self) -> str:
        """Return role emoji + label based on agent name."""
        name_lower = self.name.lower()
        for key, (emoji, label) in ROLE_MAP.items():
            if key in name_lower:
                return f"{emoji} {label}"
        return "⚙️ agent"

    @property
    def merge_strategy_display(self) -> str:
        """Human-readable merge strategy."""
        cfg = self.agents_json_config
        if not cfg:
            return "—"
        if cfg.merge_strategy == "pr":
            return "PR → branch"
        return "auto → main"

    @property
    def qa_display(self) -> str:
        """Human-readable QA status."""
        cfg = self.agents_json_config
        if not cfg:
            return "off"
        qa = cfg.qa_pre_commit
        if qa == "off":
            return "off"
        if qa == "auto":
            return "auto (pytest)"
        return qa

    @property
    def schedule_list(self) -> list[dict[str, Any]]:
        """Return schedule as a list of calendar dicts (normalized)."""
        s = self.schedule
        if s.get("type") == "calendar":
            intervals = s.get("intervals")
            if intervals:
                return intervals
            # Single entry — extract calendar fields
            entry = {k: v for k, v in s.items() if k != "type"}
            return [entry] if entry else []
        return []

    @property
    def schedule_display(self) -> str:
        """Human-readable schedule string."""
        s = self.schedule
        if s.get("type") == "calendar":
            entries = self.schedule_list
            if not entries:
                return "手動"
            return " / ".join(_format_one_schedule(e) for e in entries)
        if s.get("type") == "interval":
            secs = s.get("seconds", 0)
            if secs >= 3600:
                return f"每 {secs // 3600} 小時"
            return f"每 {secs // 60} 分鐘"
        return "手動"


WEEKDAY_NAMES = ["日", "一", "二", "三", "四", "五", "六"]


def _format_one_schedule(entry: dict) -> str:
    """Format a single StartCalendarInterval entry."""
    parts = []
    if "Weekday" in entry:
        wd = entry["Weekday"]
        parts.append(f"每週{WEEKDAY_NAMES[wd % 7]}")
    h = entry.get("Hour", "*")
    m = entry.get("Minute", 0)
    parts.append(f"{h}:{m:02d}" if isinstance(m, int) else f"{h}:{m}")
    return " ".join(parts)


def _parse_schedule(plist_data: dict[str, Any]) -> dict[str, Any]:
    """Extract schedule info from plist (StartCalendarInterval or StartInterval)."""
    if "StartCalendarInterval" in plist_data:
        cal = plist_data["StartCalendarInterval"]
        # Can be a dict or list of dicts
        if isinstance(cal, list):
            return {"type": "calendar", "intervals": [dict(c) for c in cal]}
        return {"type": "calendar", **dict(cal)}
    if "StartInterval" in plist_data:
        return {"type": "interval", "seconds": plist_data["StartInterval"]}
    return {"type": "unknown"}


def read_agents_json(project_dir: str | Path) -> dict[str, AgentsJsonConfig]:
    """Read .claude/agents.json and return per-agent config.

    The file maps agent names to their git/qa settings.
    Returns empty dict if file doesn't exist.
    """
    agents_json = Path(project_dir) / ".claude" / "agents.json"
    if not agents_json.exists():
        return {}

    try:
        data = json.loads(agents_json.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    configs: dict[str, AgentsJsonConfig] = {}
    agents_section = data if isinstance(data, dict) else {}

    # Support both flat {agent_name: {...}} and nested {"agents": {agent_name: {...}}}
    if "agents" in agents_section and isinstance(agents_section["agents"], dict):
        agents_section = agents_section["agents"]

    for agent_name, agent_data in agents_section.items():
        if not isinstance(agent_data, dict):
            continue
        git = agent_data.get("git", {})
        qa = agent_data.get("qa", {})
        configs[agent_name] = AgentsJsonConfig(
            description=agent_data.get("description", ""),
            merge_strategy=git.get("merge_strategy", "auto"),
            allowed_paths=git.get("allowed_paths", []),
            forbidden_paths=git.get("forbidden_paths", []),
            max_files_changed=git.get("max_files_changed", 0),
            qa_pre_commit=qa.get("pre_commit", "off"),
            raw=agent_data,
        )

    return configs


def get_recent_commit(project_dir: str, agent_name: str) -> tuple[str, str] | None:
    """Get the most recent auto-commit SHA + message for an agent.

    Returns (short_sha, message) or None.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--grep", f"agent.*{agent_name}",
             "-n", "1", "--format=%h|%s"],
            capture_output=True, text=True, timeout=5,
            cwd=project_dir,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split("|", 1)
            if len(parts) == 2:
                return parts[0], parts[1]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _extract_name_and_project(label: str, plist_data: dict[str, Any]) -> tuple[str, str]:
    """Derive agent name and project from label and ProgramArguments."""
    if label.startswith(AGENT_PREFIX):
        # Label format: com.sk.agent.<project>.<name>
        parts = label.removeprefix(AGENT_PREFIX).split(".", 1)
        project = parts[0] if parts else "unknown"
        name = parts[1] if len(parts) > 1 else parts[0]
    elif label.startswith(MAINTAIN_PREFIX):
        # Label format: com.skills.<name>
        name = label.removeprefix(MAINTAIN_PREFIX)
        project = PROJECT_DIR.name
    else:
        name = label
        project = "unknown"

    # Try to get project from WorkingDirectory
    wd = plist_data.get("WorkingDirectory", "")
    if wd:
        project = Path(wd).name

    return name, project


_LAUNCHCTL_SNAP: dict[str, Any] = {"t": 0.0, "rows": {}}


def _launchctl_snapshot() -> dict[str, tuple[int | None, int | None]]:
    """{label: (pid, exit_code)} from ONE `launchctl list` dump, 5s TTL.

    Why: the old per-label `launchctl list <label>` ran a subprocess for EVERY
    agent — 20+ agents made /api/agents take ~18s, which (combined with the
    token-corpus cold parse) fed the watchdog kill/restart spiral of 2026-07-18.
    One tabular dump carries the same facts for all labels.
    """
    import time as _time

    now = _time.time()
    if now - _LAUNCHCTL_SNAP["t"] < 5 and _LAUNCHCTL_SNAP["rows"]:
        return _LAUNCHCTL_SNAP["rows"]
    rows: dict[str, tuple[int | None, int | None]] = {}
    try:
        result = subprocess.run(
            ["launchctl", "list"], capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            pid_s, status_s, label = parts
            pid = int(pid_s) if pid_s.strip().isdigit() else None
            try:
                raw = int(status_s.strip())
                # tabular status is a wait status when >255, plain code otherwise
                exit_code: int | None = raw >> 8 if raw > 255 else raw
            except ValueError:
                exit_code = None
            rows[label.strip()] = (pid, exit_code)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return _LAUNCHCTL_SNAP["rows"] or {}
    _LAUNCHCTL_SNAP["rows"] = rows
    _LAUNCHCTL_SNAP["t"] = now
    return rows


def _check_loaded(label: str) -> tuple[bool, int | None, int | None]:
    """Check if agent is loaded, via the shared launchctl snapshot.

    Returns (loaded, pid, exit_code).
    """
    snap = _launchctl_snapshot()
    if label not in snap:
        return False, None, None
    pid, exit_code = snap[label]
    return True, pid, exit_code


def list_agents() -> list[AgentInfo]:
    """List all sk agents from ~/Library/LaunchAgents/ + project plist files."""
    agents: list[AgentInfo] = []
    seen_labels: set[str] = set()

    # 1. Installed agents in ~/Library/LaunchAgents/
    for plist_path in sorted(
        list(AGENTS_DIR.glob(f"{AGENT_PREFIX}*.plist"))
        + list(AGENTS_DIR.glob(f"{MAINTAIN_PREFIX}*.plist"))
    ):
        agent = _load_agent_info(plist_path, installed=True)
        if agent:
            agents.append(agent)
            seen_labels.add(agent.label)

    # 2. Project-level plist files (not yet installed)
    for plist_path in sorted(PROJECT_DIR.glob("com.*.plist")):
        agent = _load_agent_info(plist_path, installed=False)
        if agent and agent.label not in seen_labels:
            agents.append(agent)
            seen_labels.add(agent.label)

    # 3. Enrich from projects.json
    #
    # projects.json provides project metadata: repo path / working_directory and
    # (currently) the agent→project binding. agents.conf is the SSOT for agent
    # identity and schedule per README.md "Agent SSOT vs project metadata", but
    # the project-binding derivation is currently read from projects.json here.
    # Drift between the two is surfaced by `bin/sk check ssot`.
    #
    # TODO (Ship 4): derive agent.project from agents.conf label convention
    # (com.sk.agent.<project>.<name>) so projects.json becomes purely enrichment.
    # Tracked in docs/plans/2026-05-19-token-ingestion-ssot-plan.md.
    from lib.projects import load_projects
    projects = load_projects()
    for agent in agents:
        for proj_name, proj in projects.items():
            if agent.name in proj.agents:
                agent.project = proj_name
                if not agent.working_directory and proj.repo:
                    agent.working_directory = proj.repo
                break

    # 4. Enrich agents with agents.json config
    configs_cache: dict[str, dict[str, AgentsJsonConfig]] = {}
    for agent in agents:
        wd = agent.working_directory
        if not wd:
            continue
        if wd not in configs_cache:
            configs_cache[wd] = read_agents_json(wd)
        configs = configs_cache[wd]
        # Match by agent name (try exact, then partial)
        if agent.name in configs:
            agent.agents_json_config = configs[agent.name]
        else:
            for key, cfg in configs.items():
                if key in agent.name or agent.name in key:
                    agent.agents_json_config = cfg
                    break

    return agents


def _load_agent_info(plist_path: Path, installed: bool) -> AgentInfo | None:
    """Load agent info from a plist file."""
    try:
        with open(plist_path, "rb") as f:
            data = plistlib.load(f)
    except Exception:
        return None

    label = data.get("Label", plist_path.stem)
    name, project = _extract_name_and_project(label, data)
    schedule = _parse_schedule(data)

    if installed:
        loaded, pid, exit_code = _check_loaded(label)
    else:
        loaded, pid, exit_code = False, None, None

    return AgentInfo(
        label=label,
        name=name,
        project=project,
        plist_path=plist_path,
        schedule=schedule,
        loaded=loaded,
        installed=installed,
        pid=pid,
        exit_code=exit_code,
        working_directory=data.get("WorkingDirectory", ""),
    )


def install_agent(plist_path: Path, progress_callback=None) -> tuple[bool, list[str]]:
    """Copy plist to ~/Library/LaunchAgents/ and load it.

    Returns (success, log_messages).
    progress_callback(step, total, message) is called for each step.
    """
    import shutil
    logs: list[str] = []
    dest = AGENTS_DIR / plist_path.name

    def _step(step: int, total: int, msg: str) -> None:
        logs.append(msg)
        if progress_callback:
            progress_callback(step, total, msg)

    try:
        _step(1, 4, f"讀取 plist: {plist_path.name}")

        # Validate plist
        with open(plist_path, "rb") as f:
            data = plistlib.load(f)
        label = data.get("Label", "")
        if not label:
            _step(2, 4, "❌ plist 缺少 Label 欄位")
            return False, logs
        _step(2, 4, f"驗證通過: label={label}")

        # Copy to LaunchAgents
        shutil.copy2(plist_path, dest)
        _step(3, 4, f"複製到 {dest}")

        # Unload first in case already loaded
        subprocess.run(
            ["launchctl", "unload", str(dest)],
            capture_output=True, text=True, timeout=10,
        )

        # Load
        result = subprocess.run(
            ["launchctl", "load", str(dest)],
            capture_output=True, text=True, timeout=10,
        )

        # Verify loaded
        check = subprocess.run(
            ["launchctl", "list", label],
            capture_output=True, text=True, timeout=5,
        )
        if check.returncode == 0:
            _step(4, 4, "✅ launchctl load 成功")
            return True, logs
        elif result.returncode == 0:
            # load said OK but list says not found — still treat as success
            _step(4, 4, "✅ launchctl load 成功（等待排程）")
            return True, logs
        else:
            err = result.stderr.strip() or "unknown error"
            _step(4, 4, f"❌ launchctl load 失敗: {err}")
            return False, logs
    except Exception as e:
        logs.append(f"❌ 例外: {e}")
        return False, logs


def load_agent(label: str) -> bool:
    """Load (bootstrap) an agent via launchctl."""
    plist_path = AGENTS_DIR / f"{label}.plist"
    if not plist_path.exists():
        return False
    result = subprocess.run(
        ["launchctl", "load", str(plist_path)],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0


def unload_agent(label: str) -> bool:
    """Unload (bootout) an agent via launchctl."""
    plist_path = AGENTS_DIR / f"{label}.plist"
    if not plist_path.exists():
        return False
    result = subprocess.run(
        ["launchctl", "unload", str(plist_path)],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0


def start_agent(label: str) -> bool:
    """Manually start (kick) an agent via launchctl."""
    result = subprocess.run(
        ["launchctl", "start", label],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0


def update_schedule(agent: AgentInfo,
                    entries: list[dict[str, int]]) -> tuple[bool, str]:
    """Update an agent's schedule in its plist, then reload.

    Args:
        agent: The agent to update.
        entries: List of schedule dicts, each with Hour, Minute, and optionally Weekday.
                 Example: [{"Hour": 7, "Minute": 30}, {"Hour": 22, "Minute": 0}]

    Returns (success, message).
    """
    if not entries:
        return False, "至少需要一個排程"

    plist_path = agent.plist_path
    try:
        with open(plist_path, "rb") as f:
            data = plistlib.load(f)

        # Single entry → dict, multiple → list of dicts
        if len(entries) == 1:
            data["StartCalendarInterval"] = entries[0]
        else:
            data["StartCalendarInterval"] = entries

        data.pop("StartInterval", None)

        with open(plist_path, "wb") as f:
            plistlib.dump(data, f)

        # If installed, also update the copy in LaunchAgents and reload
        if agent.installed:
            import shutil
            dest = AGENTS_DIR / plist_path.name
            if dest != plist_path:
                shutil.copy2(plist_path, dest)

            subprocess.run(
                ["launchctl", "unload", str(dest)],
                capture_output=True, text=True, timeout=10,
            )
            result = subprocess.run(
                ["launchctl", "load", str(dest)],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return False, f"plist 已更新但 reload 失敗: {result.stderr.strip()}"

        display = " / ".join(_format_one_schedule(e) for e in entries)
        return True, f"排程已更新為：{display}"
    except Exception as e:
        return False, f"更新失敗: {e}"
