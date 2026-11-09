"""
SmartAttend — Attendance Records Page
Browse, filter, and export attendance records.
"""

import io
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database.db import get_attendance, get_all_students
from utils.ui_helpers import inject_css, section_header, page_header, style_table

DEPTS = ["All", "CS", "EC", "ME", "Civil", "EE"]


def render():
    inject_css()
    page_header("📋 Attendance Records", "Browse, filter and export all attendance data")

    # ── Filters ───────────────────────────────────────────────────────────────
    section_header("🔎 Filters")
    fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1])
    with fc1:
        date_from = st.date_input("From", value=date.today() - timedelta(days=6))
    with fc2:
        date_to   = st.date_input("To", value=date.today())
    with fc3:
        status_f  = st.selectbox("Status", ["All", "Present", "Late", "Absent"])
    with fc4:
        dept_f    = st.selectbox("Department", DEPTS)

    search = st.text_input("🔍 Search by name or roll number", placeholder="e.g. Aarav or CS001")

    # ── Fetch data ────────────────────────────────────────────────────────────
    df = get_attendance(
        date_from.isoformat(), date_to.isoformat(),
        dept=dept_f if dept_f != "All" else None,
        status_filter=status_f if status_f != "All" else None,
    )

    if search:
        q  = search.lower()
        df = df[df["name"].str.lower().str.contains(q) |
                df["roll"].str.lower().str.contains(q)]

    # ── Summary metrics ───────────────────────────────────────────────────────
    total_r  = len(df)
    present  = len(df[df["status"] == "Present"]) if not df.empty else 0
    late     = len(df[df["status"] == "Late"])    if not df.empty else 0
    absent   = len(df[df["status"] == "Absent"])  if not df.empty else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Records", total_r)
    m2.metric("✅ Present",    present)
    m3.metric("⏰ Late",       late)
    m4.metric("❌ Absent",     absent)

    st.divider()

    # ── Data table ────────────────────────────────────────────────────────────
    section_header(f"📄 Records ({total_r})")

    if df.empty:
        st.info("No records match the selected filters.")
    else:
        # Pull RFID UID from students table for display
        students = get_all_students()
        rfid_map = dict(zip(students["roll"], students["rfid"])) if not students.empty else {}

        display = df.copy()
        display["rfid"] = display["roll"].map(rfid_map).fillna("—")
        display = display[["name", "roll", "rfid", "dept", "date", "time", "status"]].rename(
            columns={
                "name": "Student", "roll": "Roll No.", "rfid": "RFID UID",
                "dept": "Dept", "date": "Date", "time": "Time", "status": "Status"
            }
        )

        def _style(val):
            return {
                "Present": "color:#15803D;font-weight:600",
                "Late":    "color:#B45309;font-weight:600",
                "Absent":  "color:#B91C1C;font-weight:600",
            }.get(val, "")

        st.dataframe(
            style_table(display.style, _style, subset=["Status"]),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

    # ── Download buttons ──────────────────────────────────────────────────────
    if not df.empty:
        st.divider()
        section_header("⬇️ Export")
        dl1, dl2 = st.columns(2)

        # CSV
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        dl1.download_button(
            label="📄 Download CSV",
            data=csv_bytes,
            file_name=f"attendance_{date_from}_{date_to}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Excel
        try:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Attendance")
            buf.seek(0)
            dl2.download_button(
                label="📊 Download Excel",
                data=buf.getvalue(),
                file_name=f"attendance_{date_from}_{date_to}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except ImportError:
            dl2.warning("Install openpyxl for Excel export: pip install openpyxl")
