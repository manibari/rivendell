"""Agents page — manage launchd agents with start/stop/run controls."""

import datetime
import time
import streamlit as st
from lib.agents import (
    list_agents, load_agent, unload_agent, start_agent,
    install_agent, update_schedule, get_recent_commit, WEEKDAY_NAMES,
)
from lib.db import get_conn, get_today_agent_cost, get_last_success_time


def render() -> None:
    st.title("Agent 管理")

    agents = list_agents()

    if not agents:
        st.info("未找到 sk agent")
        return

    # ── Top metrics row ──────────────────────────────────────────────
    _render_metrics(agents)

    st.divider()

    # ── Agent cards ──────────────────────────────────────────────────
    for agent in agents:
        _render_agent_card(agent)


def _render_metrics(agents: list) -> None:
    """Top-level metrics: total agents, running, last success, today cost."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總 Agent 數", len(agents))
    col2.metric("執行中", sum(1 for a in agents if a.loaded))

    last_success = get_last_success_time()
    col3.metric("上次成功", last_success[:16] if last_success else "—")

    today_cost = get_today_agent_cost()
    col4.metric("今日花費", f"${today_cost:.4f}")


def _render_agent_card(agent) -> None:
    """Render a single agent card with role badge, git config, and history."""
    with st.container(border=True):
        # Header row: name + role badge | status | schedule
        col1, col2, col3 = st.columns([3, 1, 2])

        # Name + role badge
        badge = agent.role_badge
        col1.subheader(f"{agent.project}/{agent.name}")
        col1.caption(badge)

        # Status
        if not agent.installed:
            status_text = "⚪ 未安裝"
        elif agent.loaded:
            status_text = "🟢 已載入"
        else:
            status_text = "🔴 未載入"
        if agent.exit_code is not None and agent.exit_code != 0:
            status_text = f"🔴 Exit {agent.exit_code}"
        col2.write(status_text)

        # Schedule + merge strategy
        col3.write(f"排程：{agent.schedule_display}")
        merge_display = agent.merge_strategy_display
        if merge_display != "—":
            col3.caption(f"Merge: `{merge_display}`")

        # ── Tags row: QA + recent commit ─────────────────────────
        tag_cols = st.columns([2, 3])
        qa_display = agent.qa_display
        tag_cols[0].write(f"**QA:** `{qa_display}`")

        # Recent commit
        if agent.working_directory:
            commit = get_recent_commit(agent.working_directory, agent.name)
            if commit:
                sha, msg = commit
                tag_cols[1].write(f"**最近 commit:** `{sha}` {msg}")
            else:
                tag_cols[1].write("**最近 commit:** —")

        # ── Git safety settings (collapsible) ────────────────────
        cfg = agent.agents_json_config
        if cfg and (cfg.allowed_paths or cfg.forbidden_paths or cfg.max_files_changed):
            with st.expander("🔒 Git 安全設定"):
                if cfg.allowed_paths:
                    st.write(f"**Allowed paths:** `{'`, `'.join(cfg.allowed_paths)}`")
                if cfg.forbidden_paths:
                    st.write(f"**Forbidden paths:** `{'`, `'.join(cfg.forbidden_paths)}`")
                if cfg.max_files_changed:
                    st.write(f"**Max files:** {cfg.max_files_changed}")

        # ── Action buttons ───────────────────────────────────────
        btn_col1, btn_col2, _ = st.columns(3)
        key_prefix = agent.label.replace(".", "_")

        if not agent.installed:
            if btn_col1.button("📥 安裝", key=f"install_{key_prefix}"):
                progress_bar = st.progress(0, text="準備安裝...")
                status_area = st.empty()

                def on_progress(step, total, msg):
                    progress_bar.progress(step / total, text=msg)

                ok, logs = install_agent(agent.plist_path, progress_callback=on_progress)
                for log_line in logs:
                    status_area.caption(log_line)
                if ok:
                    progress_bar.progress(1.0, text="✅ 安裝完成")
                    st.success(f"{agent.name} 已安裝並載入")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    progress_bar.progress(1.0, text="❌ 安裝失敗")
                    st.error(f"安裝 {agent.name} 失敗")
                    for log_line in logs:
                        st.caption(log_line)
            btn_col2.caption("plist 尚未安裝到 LaunchAgents")
        elif not agent.loaded:
            if btn_col1.button("▶ 啟動", key=f"start_{key_prefix}"):
                ok = load_agent(agent.label)
                if ok:
                    st.success(f"{agent.name} 已啟動")
                    st.rerun()
                else:
                    st.error(f"啟動 {agent.name} 失敗")
        else:
            if btn_col1.button("⏹ 停止", key=f"stop_{key_prefix}"):
                ok = unload_agent(agent.label)
                if ok:
                    st.success(f"{agent.name} 已停止")
                    st.rerun()
                else:
                    st.error(f"停止 {agent.name} 失敗")

        if agent.installed:
            if btn_col2.button("🔄 立即執行", key=f"run_{key_prefix}"):
                ok = start_agent(agent.label)
                if ok:
                    st.toast(f"{agent.name} 已觸發")
                else:
                    st.error(f"執行 {agent.name} 失敗")

        # Schedule editor
        with st.expander("⏰ 修改排程"):
            _schedule_editor(agent, key_prefix)

        # Execution history (enhanced)
        with st.expander("📋 執行歷史"):
            _show_run_history(agent.label)


def _schedule_editor(agent, key_prefix: str) -> None:
    """Multi-entry schedule editor."""
    state_key = f"sched_entries_{key_prefix}"
    if state_key not in st.session_state:
        existing = agent.schedule_list
        if existing:
            st.session_state[state_key] = existing
        else:
            st.session_state[state_key] = [{"Hour": 0, "Minute": 0}]

    entries = st.session_state[state_key]

    for i, entry in enumerate(entries):
        col_time, col_freq, col_day, col_del = st.columns([2, 2, 2, 1])

        with col_time:
            t = st.time_input(
                f"時間 #{i+1}",
                value=datetime.time(entry.get("Hour", 0), entry.get("Minute", 0)),
                key=f"time_{key_prefix}_{i}",
            )
            entries[i]["Hour"] = t.hour
            entries[i]["Minute"] = t.minute

        with col_freq:
            has_wd = "Weekday" in entry
            freq = st.selectbox(
                f"頻率 #{i+1}",
                ["每天", "每週"],
                index=1 if has_wd else 0,
                key=f"freq_{key_prefix}_{i}",
            )

        with col_day:
            if freq == "每週":
                wd = st.selectbox(
                    f"星期 #{i+1}",
                    options=list(range(7)),
                    format_func=lambda x: f"週{WEEKDAY_NAMES[x]}",
                    index=entry.get("Weekday", 0),
                    key=f"wd_{key_prefix}_{i}",
                )
                entries[i]["Weekday"] = wd
            else:
                entries[i].pop("Weekday", None)
                st.write("")

        with col_del:
            st.write("")
            if len(entries) > 1:
                if st.button("🗑️", key=f"del_{key_prefix}_{i}"):
                    entries.pop(i)
                    st.rerun()

    if st.button("➕ 新增排程", key=f"add_{key_prefix}"):
        entries.append({"Hour": 0, "Minute": 0})
        st.rerun()

    from lib.agents import _format_one_schedule
    preview = " / ".join(_format_one_schedule(e) for e in entries)
    st.caption(f"預覽：{preview}")

    if st.button("💾 儲存排程", key=f"save_sched_{key_prefix}"):
        ok, msg = update_schedule(agent, entries)
        if ok:
            st.success(msg)
            del st.session_state[state_key]
            time.sleep(1)
            st.rerun()
        else:
            st.error(msg)


def _show_run_history(agent_label: str) -> None:
    """Show the 10 most recent agent_runs as a dataframe."""
    import pandas as pd

    conn = get_conn()
    parts = agent_label.split(".")
    agent_name = parts[-1] if len(parts) > 4 else parts[-1]

    rows = conn.execute("""
        SELECT started_at, finished_at, exit_code, tokens_used, cost_usd,
               commit_sha, files_changed, qa_passed, branch_name, pr_url
        FROM agent_runs
        WHERE agent_name = ?
        ORDER BY started_at DESC
        LIMIT 10
    """, (agent_name,)).fetchall()
    conn.close()

    if not rows:
        st.caption("尚無執行紀錄")
        return

    data = []
    for row in rows:
        exit_code = row["exit_code"]
        qa = row["qa_passed"]
        data.append({
            "時間": row["started_at"] or "—",
            "結果": "✅" if exit_code == 0 else f"❌ ({exit_code})",
            "花費": f"${row['cost_usd']:.4f}" if row["cost_usd"] else "—",
            "Tokens": row["tokens_used"] or "—",
            "Commit": row["commit_sha"] or "—",
            "Files": row["files_changed"] if row["files_changed"] is not None else "—",
            "QA": "✅" if qa == 1 else ("❌" if qa == 0 else "—"),
            "Branch": row["branch_name"] or "—",
        })

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
