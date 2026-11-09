"""
SmartAttend — Reports & Analytics Page
Detailed analytics: daily/weekly/monthly trends, per-student %, low attendance alerts.
"""

import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

from database.db import (
    get_attendance, get_daily_summary, get_student_attendance_pct,
    get_low_attendance_students, get_monthly_summary, get_dept_summary,
    get_all_students,
)
from utils.ui_helpers import inject_css, section_header, page_header, metric_card, style_table
from utils.charts import (
    attendance_bar_chart, monthly_trend_chart,
    student_pct_bar_chart, dept_bar_chart,
)


def render():
    inject_css()
    page_header("📊 Reports & Analytics", "Detailed attendance statistics and trend analysis")

    # ── Report period selector ─────────────────────────────────────────────────
    section_header("📅 Report Period")
    rp1, rp2 = st.columns(2)
    report_type = rp1.selectbox(
        "Quick select",
        ["Last 7 Days", "Last 14 Days", "Last 30 Days", "Custom Range"],
    )
    today = date.today()
    if report_type == "Last 7 Days":
        d_from, d_to = today - timedelta(days=6), today
    elif report_type == "Last 14 Days":
        d_from, d_to = today - timedelta(days=13), today
    elif report_type == "Last 30 Days":
        d_from, d_to = today - timedelta(days=29), today
    else:
        with rp2:
            d_range = st.date_input("Select range", value=(today - timedelta(days=6), today))
            d_from  = d_range[0] if isinstance(d_range, tuple) else today - timedelta(days=6)
            d_to    = d_range[1] if isinstance(d_range, tuple) and len(d_range) == 2 else today

    # ── Overall summary KPIs ───────────────────────────────────────────────────
    df_period = get_attendance(d_from.isoformat(), d_to.isoformat())
    students  = get_all_students()

    total_records = len(df_period)
    present_cnt   = len(df_period[df_period["status"] == "Present"]) if not df_period.empty else 0
    late_cnt      = len(df_period[df_period["status"] == "Late"])    if not df_period.empty else 0
    absent_cnt    = len(df_period[df_period["status"] == "Absent"])  if not df_period.empty else 0
    overall_pct   = round((present_cnt + late_cnt) / total_records * 100) if total_records else 0

    section_header(f"📈 Summary — {d_from.strftime('%d %b')} to {d_to.strftime('%d %b %Y')}")
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    with mc1: st.markdown(metric_card("📄", "Total Records", total_records, "#1B2A4A"), unsafe_allow_html=True)
    with mc2: st.markdown(metric_card("✅", "Present", present_cnt, "#16A34A"), unsafe_allow_html=True)
    with mc3: st.markdown(metric_card("⏰", "Late",    late_cnt,    "#D97706"), unsafe_allow_html=True)
    with mc4: st.markdown(metric_card("❌", "Absent",  absent_cnt,  "#DC2626"), unsafe_allow_html=True)
    with mc5:
        color = "#16A34A" if overall_pct >= 75 else ("#D97706" if overall_pct >= 60 else "#DC2626")
        st.markdown(metric_card("📊", "Overall %", f"{overall_pct}%", color), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs for different analytics ───────────────────────────────────────────
    tab_daily, tab_monthly, tab_students, tab_dept, tab_low = st.tabs([
        "📅 Daily Trend",
        "📆 Monthly Summary",
        "👤 Per-Student",
        "🏫 By Department",
        "⚠️ Low Attendance",
    ])

    # ── Daily Trend ───────────────────────────────────────────────────────────
    with tab_daily:
        section_header("Daily Attendance Breakdown")
        if df_period.empty:
            st.info("No data for the selected period.")
        else:
            daily = df_period.groupby(["date", "status"]).size().reset_index(name="count")
            fig   = attendance_bar_chart(daily, "")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Daily presence rate line
            if not daily.empty:
                pivot    = daily.pivot_table(index="date", columns="status", values="count", fill_value=0).reset_index()
                n_students = len(students)
                if n_students > 0:
                    for col in ["Present", "Late", "Absent"]:
                        if col not in pivot.columns:
                            pivot[col] = 0
                    pivot["pct"] = ((pivot["Present"] + pivot["Late"]) / n_students * 100).round(1)
                    fig2 = px.line(pivot, x="date", y="pct", markers=True,
                                   labels={"date": "Date", "pct": "Attendance %"},
                                   color_discrete_sequence=["#2563EB"])
                    fig2.add_hline(y=75, line_dash="dash", line_color="#DC2626",
                                   annotation_text="75% threshold")
                    fig2.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=0, r=0, t=10, b=0),
                        yaxis=dict(range=[0, 110], ticksuffix="%",
                                   gridcolor="rgba(0,0,0,0.05)"),
                        xaxis=dict(showgrid=False, tickangle=-30),
                    )
                    section_header("Daily Attendance Rate %")
                    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        # Download daily report
        if not df_period.empty:
            csv = df_period.to_csv(index=False).encode()
            st.download_button("⬇️ Download Daily Report (CSV)", csv,
                               f"daily_report_{d_from}_{d_to}.csv", "text/csv")

    # ── Monthly Summary ───────────────────────────────────────────────────────
    with tab_monthly:
        section_header("Monthly Attendance Trends")
        monthly_df = get_monthly_summary()
        if monthly_df.empty:
            st.info("No monthly data available.")
        else:
            fig = monthly_trend_chart(monthly_df)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Monthly summary table
            pivot = monthly_df.pivot_table(index="month", columns="status",
                                           values="count", fill_value=0).reset_index()
            for col in ["Present", "Late", "Absent"]:
                if col not in pivot.columns:
                    pivot[col] = 0
            pivot["Total"] = pivot["Present"] + pivot["Late"] + pivot["Absent"]
            pivot["Attendance %"] = ((pivot["Present"] + pivot["Late"]) / pivot["Total"] * 100).round(1)
            st.dataframe(pivot.rename(columns={"month": "Month"}),
                         use_container_width=True, hide_index=True)

    # ── Per-Student ───────────────────────────────────────────────────────────
    with tab_students:
        section_header("Individual Student Attendance %")
        stu_pct = get_student_attendance_pct()
        if stu_pct.empty:
            st.info("No student data available.")
        else:
            # Filter controls
            dept_filter = st.selectbox("Filter by dept", ["All", "CS", "EC", "ME", "Civil", "EE"],
                                       key="rep_dept")
            view = stu_pct.copy()
            if dept_filter != "All":
                view = view[view["dept"] == dept_filter]

            if not view.empty:
                fig = student_pct_bar_chart(view)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                display = view[["name", "roll", "dept", "year",
                                 "total_days", "present_days", "attendance_pct"]].rename(
                    columns={"name": "Student", "roll": "Roll", "dept": "Dept",
                             "year": "Year", "total_days": "Total Days",
                             "present_days": "Days Present", "attendance_pct": "Attendance %"}
                )

                def _color_pct(val):
                    try:
                        v = float(val)
                        if v < 60: return "color:#B91C1C;font-weight:700"
                        if v < 75: return "color:#B45309;font-weight:700"
                        return "color:#15803D;font-weight:600"
                    except Exception:
                        return ""

                st.dataframe(
                    style_table(display.style, _color_pct, subset=["Attendance %"]),
                    use_container_width=True, hide_index=True,
                )

                csv_pct = view.to_csv(index=False).encode()
                st.download_button("⬇️ Download Student Report (CSV)", csv_pct,
                                   "student_attendance_report.csv", "text/csv")

    # ── By Department ─────────────────────────────────────────────────────────
    with tab_dept:
        section_header("Department-wise Attendance")
        dept_df = get_dept_summary()
        if dept_df.empty:
            st.info("No department data available.")
        else:
            fig = dept_bar_chart(dept_df)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            st.dataframe(
                dept_df.rename(columns={"dept": "Department", "total": "Total Records",
                                        "present": "Present/Late", "pct": "Attendance %"}),
                use_container_width=True, hide_index=True,
            )

    # ── Low Attendance ────────────────────────────────────────────────────────
    with tab_low:
        section_header("⚠️ Students with Low Attendance")
        threshold = st.slider("Attendance threshold (%)", min_value=50, max_value=90,
                              value=75, step=5,
                              help="Students below this percentage are flagged.")
        low_df = get_low_attendance_students(threshold)

        if low_df.empty:
            st.success(f"✅ All students have attendance ≥ {threshold}%")
        else:
            st.error(f"⚠️ {len(low_df)} student(s) have attendance below {threshold}%")

            display = low_df[["name", "roll", "dept", "year",
                               "total_days", "present_days", "attendance_pct"]].rename(
                columns={"name": "Student", "roll": "Roll", "dept": "Dept",
                         "year": "Year", "total_days": "Total Days",
                         "present_days": "Days Present", "attendance_pct": "Attendance %"}
            )

            def _c(val):
                try:
                    v = float(val)
                    if v < 60: return "background-color:#FEE2E2;color:#B91C1C;font-weight:700"
                    return "background-color:#FEF3C7;color:#B45309;font-weight:700"
                except Exception:
                    return ""

            st.dataframe(
                style_table(display.style, _c, subset=["Attendance %"]),
                use_container_width=True, hide_index=True,
            )

            csv_low = low_df.to_csv(index=False).encode()
            st.download_button("⬇️ Download Low Attendance Report (CSV)", csv_low,
                               f"low_attendance_below_{threshold}pct.csv", "text/csv")
