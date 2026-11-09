"""
SmartAttend — Main Application Entry Point
==========================================
Run:  python -m streamlit run app.py
(Start Flask API first if using Wi-Fi mode:  python api/flask_api.py)
"""

import streamlit as st

# ── MUST be the very first Streamlit call ──────────────────────────────────────
st.set_page_config(
    page_title="Smart RFID Attendance System",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help":    None,
        "Report a bug": None,
        "About": "Smart RFID Attendance System v2.0 — Built with Streamlit + SQLite + ESP32",
    },
)

# ── Database bootstrap ─────────────────────────────────────────────────────────
from database.db import init_db, seed_if_empty
init_db()
seed_if_empty()

# ── Page modules ───────────────────────────────────────────────────────────────
from pages import dashboard, students, attendance, scan, reports, settings
from utils.ui_helpers import inject_css

# Inject global styling (cleans up sidebar & background)
inject_css()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Branding
    st.markdown("""
    <div style="padding: 8px 0 16px;">
        <div style="font-size:1.5rem;font-weight:800;color:#FFFFFF;letter-spacing:-0.01em;">
            📡 SmartAttend
        </div>
        <div style="font-size:0.78rem;color:#94A3B8;margin-top:2px;">
            Automated Student Attendance Management
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Navigation
    NAV_ITEMS = {
        "📡  Live RFID Scan":      "Scan",
        "🎓  Student Management":  "Students",
        "📋  Attendance Records":  "Attendance",
        "🏠  Dashboard":           "Dashboard",
        "📊  Reports & Analytics": "Reports",
        "⚙️  Settings":            "Settings",
    }

    page_label = st.radio(
        "Navigation",
        list(NAV_ITEMS.keys()),
        label_visibility="collapsed",
    )
    page = NAV_ITEMS[page_label]

    st.markdown("---")

    # Quick status
    from datetime import date
    from database.db import get_all_students, get_today_attendance
    students_df  = get_all_students()
    today_att_df = get_today_attendance()
    total    = len(students_df)
    present  = len(today_att_df[today_att_df["status"].isin(["Present","Late"])]) if not today_att_df.empty else 0
    pct      = round(present / total * 100) if total else 0

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.07);border-radius:8px;padding:12px 14px;">
        <div style="font-size:0.72rem;color:#94A3B8;text-transform:uppercase;
                    letter-spacing:0.05em;margin-bottom:6px;">Today's Summary</div>
        <div style="color:#E2E8F0;font-size:0.88rem;line-height:1.9;">
            👥 Students: <b>{total}</b><br>
            ✅ Present:  <b style="color:#4ADE80;">{present}</b><br>
            📊 Rate:     <b style="color:{'#4ADE80' if pct>=75 else '#FBBF24' if pct>=60 else '#F87171'};">{pct}%</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"📅 {date.today().strftime('%d %b %Y')}")
    st.caption("Smart RFID Attendance System v2.0")

# ── Route to page ──────────────────────────────────────────────────────────────
if page == "Dashboard":
    dashboard.render()
elif page == "Students":
    students.render()
elif page == "Attendance":
    attendance.render()
elif page == "Scan":
    scan.render()
elif page == "Reports":
    reports.render()
elif page == "Settings":
    settings.render()
