"""Token Usage page — Claude Code token consumption and estimated costs."""

from datetime import date, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
from lib.tokens import get_filtered_usage, get_total_stats


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def render() -> None:
    st.title("Token 用量")

    # Date range selector
    st.subheader("篩選期間")
    presets = {"最近 7 天": 7, "最近 30 天": 30, "最近 90 天": 90, "自訂": 0, "全部": -1}
    preset = st.radio("快速選擇", list(presets.keys()), horizontal=True, index=1)
    preset_days = presets[preset]

    today = date.today()
    if preset_days > 0:
        date_start = (today - timedelta(days=preset_days)).isoformat()
        date_end = today.isoformat()
    elif preset_days == 0:
        # Custom range
        col_d1, col_d2 = st.columns(2)
        d_start = col_d1.date_input("開始日期", value=today - timedelta(days=30))
        d_end = col_d2.date_input("結束日期", value=today)
        date_start = d_start.isoformat()
        date_end = d_end.isoformat()
    else:
        date_start = None
        date_end = None

    # Fetch all data in one pass
    data = get_filtered_usage(date_start, date_end)

    if not data.total_sessions:
        st.warning("選定期間內無 Claude Code 使用紀錄。")
        return

    # Show selected range
    if date_start and date_end:
        st.caption(f"顯示期間：{date_start} ~ {date_end}")
    else:
        totals = get_total_stats()
        st.caption(f"顯示全部資料（{totals.get('first_session', '?')} 起）")

    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sessions", f"{data.total_sessions:,}")
    col2.metric("訊息數", f"{data.total_messages:,}")
    col3.metric("估算花費", f"${data.total_cost_usd:.2f}")
    col4.metric("Tokens", _fmt_tokens(data.total_tokens))

    st.divider()

    # Model breakdown
    st.subheader("各模型用量")
    if data.models:
        model_data = []
        for m in data.models:
            short_name = (m.model.replace("claude-", "")
                          .replace("-20251101", "").replace("-20250929", "")
                          .replace("-20251001", ""))
            model_data.append({
                "模型": short_name,
                "Input": _fmt_tokens(m.input_tokens),
                "Output": _fmt_tokens(m.output_tokens),
                "Cache 讀取": _fmt_tokens(m.cache_read_tokens),
                "Cache 建立": _fmt_tokens(m.cache_create_tokens),
                "估算費用": f"${m.cost_usd:.2f}",
            })
        st.dataframe(
            pd.DataFrame(model_data),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # Project breakdown
    st.subheader("各專案用量")
    if data.projects:
        proj_data = []
        for p in data.projects:
            proj_data.append({
                "專案": p.project,
                "Sessions": p.sessions,
                "訊息數": p.messages,
                "工具呼叫": p.tool_calls,
                "Tokens": _fmt_tokens(p.tokens_total),
                "估算費用": f"${p.cost_usd:.2f}",
            })
        st.dataframe(
            pd.DataFrame(proj_data),
            use_container_width=True,
            hide_index=True,
        )

        # Pie chart
        pie_df = pd.DataFrame([
            {"專案": p.project, "費用": p.cost_usd}
            for p in data.projects if p.cost_usd > 0
        ])
        if not pie_df.empty:
            fig_pie = px.pie(pie_df, values="費用", names="專案",
                             title="各專案估算費用佔比")
            fig_pie.update_layout(height=350)
            st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # Daily trend
    st.subheader("每日趨勢")
    if not data.daily:
        st.info("選定範圍內無每日資料。")
        return

    df = pd.DataFrame([
        {
            "日期": u.date,
            "Sessions": u.sessions,
            "訊息數": u.messages,
            "工具呼叫": u.tool_calls,
            "Tokens": u.tokens_total,
            "費用": u.cost_usd,
        }
        for u in data.daily
    ])

    # Token bar chart
    fig = px.bar(
        df, x="日期", y="Tokens",
        title="每日 Token 用量",
        color_discrete_sequence=["#636EFA"],
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

    # Activity line chart
    fig2 = px.line(
        df, x="日期", y=["Sessions", "訊息數", "工具呼叫"],
        title="每日活動",
        markers=True,
    )
    fig2.update_layout(height=300)
    st.plotly_chart(fig2, use_container_width=True)

    # Cost line chart
    fig3 = px.area(
        df, x="日期", y="費用",
        title="每日估算費用（USD）",
        color_discrete_sequence=["#EF553B"],
    )
    fig3.update_layout(height=300)
    st.plotly_chart(fig3, use_container_width=True)

    # Detail table
    st.subheader("每日明細")
    display_df = df.copy()
    display_df["Tokens"] = display_df["Tokens"].apply(_fmt_tokens)
    display_df["費用"] = display_df["費用"].apply(lambda x: f"${x:.2f}")
    st.dataframe(
        display_df.sort_values("日期", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
