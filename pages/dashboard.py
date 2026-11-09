"""
SmartAttend — Dashboard Home Page
KPI summary cards, weekly bar chart, attendance donut, recent records.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database.db import (
    get_all_students, get_today_attendance,
    get_attendance, get_daily_summary,
)
from utils.ui_helpers import inject_css, metric_card, section_header, page_header, style_table
from utils.charts import attendance_bar_chart, attendance_donut_chart


def render():
    inject_css()
    page_header("🏠 Dashboard", "Smart RFID Attendance System — Overview")

    students  = get_all_students()
    today_att = get_today_attendance()
    today_str = date.today().strftime("%A, %d %B %Y")
    total     = len(students)
    present   = len(today_att[today_att["status"] == "Present"]) if not today_att.empty else 0
    late      = len(today_att[today_att["status"] == "Late"]) if not today_att.empty else 0
    absent    = total - present - late
    pct       = round((present + late) / total * 100) if total else 0

    st.caption(f"📅 {today_str}")

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("👥", "Total Students", total, "#1B2A4A"),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("✅", "Present Today", present + late, "#16A34A",
                                sub=f"{late} late"),
                    unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("❌", "Absent Today", absent, "#DC2626"),
                    unsafe_allow_html=True)
    with c4:
        color = "#16A34A" if pct >= 75 else ("#D97706" if pct >= 60 else "#DC2626")
        st.markdown(metric_card("📊", "Attendance %", f"{pct}%", color),
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts row ────────────────────────────────────────────────────────────
    left, right = st.columns([2, 1])

    with left:
        section_header("📈 Last 7 Days — Attendance Trend")
        daily_df = get_daily_summary(7)
        fig      = attendance_bar_chart(daily_df, "")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with right:
        section_header("🍩 Today's Distribution")
        fig2 = attendance_donut_chart(present, late, absent)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Recent Attendance Table ────────────────────────────────────────────────
    section_header("🕐 Recent Attendance Entries")

    week_ago = (date.today() - timedelta(days=6)).isoformat()
    recent   = get_attendance(week_ago, date.today().isoformat())

    if recent.empty:
        st.info("No attendance records found for the last 7 days.")
    else:
        def _style_status(val):
            colors = {
                "Present": "color:#15803D;font-weight:600",
                "Late":    "color:#B45309;font-weight:600",
                "Absent":  "color:#B91C1C;font-weight:600",
            }
            return colors.get(val, "")

        display = recent[["name", "roll", "dept", "date", "time", "status"]].head(20).rename(
            columns={"name": "Student", "roll": "Roll No.", "dept": "Dept",
                     "date": "Date", "time": "Time", "status": "Status"}
        )
        st.dataframe(
            style_table(display.style, _style_status, subset=["Status"]),
            use_container_width=True,
            hide_index=True,
            height=360,
        )

    # ── Students not yet marked today ─────────────────────────────────────────
    if not today_att.empty and not students.empty:
        marked_rolls = set(today_att["roll"].tolist())
        not_marked   = students[~students["roll"].isin(marked_rolls)]
        if not not_marked.empty:
            section_header(f"⏳ Not Marked Yet ({len(not_marked)} students)")
            st.dataframe(
                not_marked[["name", "roll", "dept", "year"]].rename(
                    columns={"name": "Student", "roll": "Roll No.",
                             "dept": "Dept", "year": "Year"}
                ),
                use_container_width=True,
                hide_index=True,
                height=200,
            )
