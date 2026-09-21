"""Skills page — browsable skill catalog grouped by category."""

import streamlit as st
from lib.skills import list_skills

# Fixed display order for categories
CAT_ORDER = ["基礎建設", "工作流", "品質", "前端", "後端", "文件", "Git", "整合"]
CAT_ICONS = {
    "基礎建設": "🏗️",
    "工作流": "🔄",
    "品質": "✅",
    "前端": "🎨",
    "後端": "🗄️",
    "文件": "📄",
    "Git": "🔀",
    "整合": "🔌",
}


def render() -> None:
    st.title("Skill 總覽")

    skills = list_skills()
    if not skills:
        st.warning("未找到任何 skill。")
        return

    # Search bar
    search = st.text_input("🔍 搜尋", placeholder="skill 名稱或功能關鍵字...")

    # Filter by search
    if search:
        q = search.lower()
        skills = [s for s in skills if q in s.name.lower() or q in s.summary.lower()]

    # Summary metrics
    invocable_count = sum(1 for s in skills if s.invocable)
    cats = sorted(set(s.category for s in skills))
    col1, col2, col3 = st.columns(3)
    col1.metric("Skill 總數", len(skills))
    col2.metric("可呼叫", invocable_count)
    col3.metric("分類數", len(cats))

    st.divider()

    # Group by category in fixed order
    by_cat: dict[str, list] = {}
    for s in skills:
        by_cat.setdefault(s.category, []).append(s)

    # Display order: predefined first, then any extras
    ordered_cats = [c for c in CAT_ORDER if c in by_cat]
    ordered_cats += [c for c in sorted(by_cat) if c not in ordered_cats]

    for cat in ordered_cats:
        cat_skills = by_cat[cat]
        icon = CAT_ICONS.get(cat, "📦")

        with st.expander(f"{icon} {cat}（{len(cat_skills)}）", expanded=not search):
            for s in sorted(cat_skills, key=lambda x: x.name):
                col_name, col_desc = st.columns([1, 3])
                badge = " `/指令`" if s.invocable else ""
                col_name.markdown(f"**{s.name}**{badge}")
                col_desc.write(s.summary)
