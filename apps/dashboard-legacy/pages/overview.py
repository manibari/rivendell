"""Overview page — system health at a glance."""

import re
from pathlib import Path

import streamlit as st
from lib.agents import list_agents
from lib.hooks import list_hooks
from lib.skills import list_skills
from lib.tokens import get_total_stats

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def render() -> None:
    st.title("總覽")

    # Metrics row
    agents = list_agents()
    hooks = list_hooks()
    skills = list_skills()
    totals = get_total_stats()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Skill 總數", len(skills))
    col2.metric("執行中 Agent", sum(1 for a in agents if a.loaded))
    col3.metric("啟用 Hook", len(hooks))
    col4.metric("估算總花費", f"${totals['total_cost_usd']:.2f}")

    # Agent status table
    st.subheader("Agent 狀態")
    if agents:
        for agent in agents:
            if not agent.installed:
                status = "⚪ 未安裝"
            elif agent.loaded:
                status = "🟢 已載入"
            else:
                status = "🔴 未載入"
            if agent.exit_code is not None and agent.exit_code != 0:
                status = f"🔴 exit={agent.exit_code}"
            col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
            col_a.write(f"**{agent.project}/{agent.name}**")
            col_b.write(status)
            col_c.write(f"排程 {agent.schedule_display}")
            col_d.caption(agent.role_badge)
    else:
        st.info("未找到 sk agent")

    # Hook status table
    st.subheader("Hook 狀態")
    if hooks:
        for hook in hooks:
            col_a, col_b, col_c = st.columns([1, 1, 2])
            col_a.write(f"**{hook.event}**")
            col_b.write(hook.matcher or "（全部）")
            col_c.code(hook.command, language=None)
    else:
        st.info("未設定 hook（~/.claude/settings.json）")

    # ── Agent collaboration flow ─────────────────────────────────
    st.subheader("Agent 協作流")
    _render_collaboration_flow(agents)


def _render_collaboration_flow(agents: list) -> None:
    """Show agent collaboration status based on .learnings/ERRORS.md."""
    # Scan all projects for .learnings/ERRORS.md
    seen_dirs: set[str] = set()
    for agent in agents:
        wd = agent.working_directory
        if wd:
            seen_dirs.add(wd)

    total_pending = 0
    total_resolved = 0
    found_any = False

    for wd in seen_dirs:
        errors_md = Path(wd) / ".learnings" / "ERRORS.md"
        if not errors_md.exists():
            continue
        found_any = True
        pending, resolved = _parse_errors_md(errors_md)
        total_pending += pending
        total_resolved += resolved

    if not found_any:
        st.caption("尚無 .learnings/ERRORS.md 資料。Agent 執行後會自動產生。")
        # Show conceptual flow
        st.markdown("""
```
tester 發現 bug → .learnings/ERRORS.md → maintainer 修復 → resolved
```
""")
        return

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Pending 問題", total_pending)
    col2.metric("已解決", total_resolved)
    total = total_pending + total_resolved
    rate = f"{total_resolved / total * 100:.0f}%" if total > 0 else "—"
    col3.metric("解決率", rate)

    # Flow diagram
    st.markdown(f"""
```
tester 發現 bug ({total_pending} pending)
      ↓
.learnings/ERRORS.md
      ↓
maintainer 修復 ({total_resolved} resolved)
```
""")


def _parse_errors_md(path: Path) -> tuple[int, int]:
    """Parse ERRORS.md and count pending vs resolved entries.

    Returns (pending_count, resolved_count).
    Heuristic: lines with [x] or "resolved" are resolved; [ ] or unmarked are pending.
    """
    try:
        content = path.read_text()
    except OSError:
        return 0, 0

    pending = 0
    resolved = 0
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Checkbox format: - [x] resolved, - [ ] pending
        if re.match(r"^-\s*\[x\]", stripped, re.IGNORECASE):
            resolved += 1
        elif re.match(r"^-\s*\[\s\]", stripped):
            pending += 1
        elif "resolved" in stripped.lower() or "fixed" in stripped.lower():
            resolved += 1
        elif stripped.startswith("- ") or stripped.startswith("* "):
            pending += 1

    return pending, resolved
