"""rivendell — Streamlit management dashboard."""

import sys
from pathlib import Path

# Ensure dashboard/lib is importable
DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DASHBOARD_DIR.parents[1]
sys.path.insert(0, str(DASHBOARD_DIR))

import streamlit as st
from lib.db import init_db

st.set_page_config(page_title="rivendell", page_icon="📊", layout="wide")
init_db()

st.sidebar.title("📊 rivendell")
page = st.sidebar.radio("導覽", ["總覽", "Agent 管理", "Token 用量", "Skill 總覽"])

st.sidebar.divider()
if st.sidebar.button("🔍 執行 Audit", use_container_width=True):
    with st.spinner("正在執行 sk audit..."):
        import subprocess
        result = subprocess.run(
            ["./bin/sk", "audit"],
            capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )
        if result.returncode == 0:
            st.sidebar.success("Audit 完成！")
            st.rerun()
        else:
            st.sidebar.error(f"Audit 失敗：\n{result.stderr[:300]}")

if page == "總覽":
    from pages.overview import render as overview_render
    overview_render()
elif page == "Agent 管理":
    from pages.agents_page import render as agents_render
    agents_render()
elif page == "Token 用量":
    from pages.token_usage import render as token_render
    token_render()
elif page == "Skill 總覽":
    from pages.skills_page import render as skills_render
    skills_render()
