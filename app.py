"""
Smart RFID Attendance System
============================
Simplified, single-page application:
- Scans RFID card -> Shows "Attendance Marked!" with student name.
- Displays live table of students present today.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import time

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RFID Attendance System",
    page_icon="📡",
    layout="wide",
)

# ── Database Setup ─────────────────────────────────────────────────────────────
from database.db import (
    init_db,
    get_all_students,
    get_today_attendance,
    get_student_by_rfid,
    register_card,
    mark_attendance,
)

init_db()

# ── Try Serial Import (for USB connection on laptop) ──────────────────────────
try:
    from utils.serial_comm import get_serial_manager, SERIAL_AVAILABLE
except Exception:
    SERIAL_AVAILABLE = False

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except Exception:
    HAS_AUTOREFRESH = False

# Auto-refresh every 2 seconds to catch live card scans
if HAS_AUTOREFRESH:
    st_autorefresh(interval=2000, key="auto_refresh_attendance")

# ── Custom Styling ────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.main-title {
    font-size: 2rem;
    font-weight: 800;
    color: #1B2A4A;
    margin-bottom: 2px;
}
.sub-title {
    font-size: 0.95rem;
    color: #64748B;
    margin-bottom: 20px;
}
.scan-card-success {
    background: #F0FDF4;
    border: 3px solid #16A34A;
    border-radius: 16px;
    padding: 30px;
    text-align: center;
    box-shadow: 0 4px 14px rgba(22, 163, 74, 0.12);
    margin-bottom: 24px;
}
.scan-card-dup {
    background: #FFFBEB;
    border: 3px solid #D97706;
    border-radius: 16px;
    padding: 30px;
    text-align: center;
    box-shadow: 0 4px 14px rgba(217, 119, 6, 0.12);
    margin-bottom: 24px;
}
.scan-card-idle {
    background: #FFFFFF;
    border: 2px dashed #94A3B8;
    border-radius: 16px;
    padding: 40px;
    text-align: center;
    margin-bottom: 24px;
}
.scan-card-new {
    background: #EFF6FF;
    border: 3px solid #2563EB;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "last_scan" not in st.session_state:
    st.session_state["last_scan"] = None

# ── Check Cloud / URL Query Parameter Scan (?uid=XX:XX:XX:XX) ────────────────
# Allows ESP32 over Wi-Fi to hit: https://your-app.streamlit.app/?uid=53:8E:B2:1A
query_uid = st.query_params.get("uid")
if query_uid:
    uid_clean = str(query_uid).strip().upper()
    student = get_student_by_rfid(uid_clean)
    scan_time = datetime.now().strftime("%I:%M %p")

    if student:
        outcome = mark_attendance(
            student_id=student["id"],
            name=student["name"],
            roll=student["roll"],
            dept=student["dept"],
            status="Present",
            scan_time=scan_time,
        )
        st.session_state["last_scan"] = {
            "name": student["name"],
            "roll": student["roll"],
            "uid": uid_clean,
            "time": scan_time,
            "result": "duplicate" if outcome == "duplicate" else "present",
        }
    else:
        st.session_state["last_scan"] = {
            "name": "Unknown",
            "roll": "—",
            "uid": uid_clean,
            "time": scan_time,
            "result": "unknown",
        }
    # Clear query param to avoid re-triggering on manual refresh
    st.query_params.clear()

# ── Check Local USB Serial Scan (when running on laptop) ──────────────────────
if SERIAL_AVAILABLE:
    serial_mgr = get_serial_manager()
    if serial_mgr.is_connected:
        serial_uid = serial_mgr.poll_uid()
        if serial_uid:
            uid_clean = serial_uid.strip().upper()
            student = get_student_by_rfid(uid_clean)
            scan_time = datetime.now().strftime("%I:%M %p")

            if student:
                outcome = mark_attendance(
                    student_id=student["id"],
                    name=student["name"],
                    roll=student["roll"],
                    dept=student["dept"],
                    status="Present",
                    scan_time=scan_time,
                )
                st.session_state["last_scan"] = {
                    "name": student["name"],
                    "roll": student["roll"],
                    "uid": uid_clean,
                    "time": scan_time,
                    "result": "duplicate" if outcome == "duplicate" else "present",
                }
            else:
                st.session_state["last_scan"] = {
                    "name": "Unknown",
                    "roll": "—",
                    "uid": uid_clean,
                    "time": scan_time,
                    "result": "unknown",
                }

# ── App Header ────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">📡 Smart RFID Attendance System</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Live Attendance Tracking &nbsp;•&nbsp; <b>{date.today().strftime("%A, %d %B %Y")}</b></div>', unsafe_allow_html=True)

# ── Hardware Connection Bar (USB Cable Mode) ──────────────────────────────────
if SERIAL_AVAILABLE:
    with st.expander("🔌 ESP32 USB Connection (Select Port & Connect)", expanded=False):
        serial_mgr = get_serial_manager()
        c1, c2, c3 = st.columns([3, 2, 2])
        ports = serial_mgr.list_ports()
        port_list = ports if ports else ["No COM ports found"]
        cur_port = serial_mgr.port if serial_mgr.port in port_list else port_list[0]
        sel_port = c1.selectbox("COM Port", port_list, index=port_list.index(cur_port))

        with c2:
            st.write("")
            st.write("")
            if not serial_mgr.is_connected:
                if st.button("🔗 Connect Reader", type="primary", use_container_width=True):
                    if ports and serial_mgr.connect(sel_port, 115200):
                        st.success(f"Connected to {sel_port}!")
                        st.rerun()
                    else:
                        st.error(serial_mgr.last_error or "Could not open port")
            else:
                if st.button("⛔ Disconnect", use_container_width=True):
                    serial_mgr.disconnect()
                    st.rerun()

        with c3:
            st.write("")
            st.write("")
            if serial_mgr.is_connected:
                st.success("🟢 Reader Connected & Live")
            else:
                st.info("⚪ Reader Disconnected")

# ── Main Live Scan Result Display ─────────────────────────────────────────────
scan = st.session_state.get("last_scan")

if scan:
    result = scan.get("result", "unknown")
    name   = scan.get("name", "Unknown")
    roll   = scan.get("roll", "—")
    time_s = scan.get("time", datetime.now().strftime("%I:%M %p"))
    uid    = scan.get("uid", "")

    if result == "present":
        st.markdown(f"""
        <div class="scan-card-success">
            <div style="font-size:3.5rem; line-height:1;">✅</div>
            <div style="font-size:1.2rem; color:#15803D; font-weight:800; text-transform:uppercase; letter-spacing:0.06em; margin-top:8px;">
                Attendance Marked!
            </div>
            <div style="font-size:2.5rem; color:#0F172A; font-weight:800; margin:8px 0;">
                {name}
            </div>
            <div style="font-size:1.1rem; color:#334155;">
                Roll / ID: <b>{roll}</b> &nbsp;•&nbsp; Time: <b>{time_s}</b> &nbsp;•&nbsp; Status: <b style="color:#15803D;">Present</b>
            </div>
            <div style="font-size:0.85rem; color:#64748B; margin-top:10px;">
                Card UID: <code style="background:#DCFCE7; color:#166534; padding:2px 8px; border-radius:4px;">{uid}</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif result == "duplicate":
        st.markdown(f"""
        <div class="scan-card-dup">
            <div style="font-size:3.5rem; line-height:1;">⚠️</div>
            <div style="font-size:1.2rem; color:#B45309; font-weight:800; text-transform:uppercase; letter-spacing:0.06em; margin-top:8px;">
                Already Marked Today
            </div>
            <div style="font-size:2.5rem; color:#0F172A; font-weight:800; margin:8px 0;">
                {name}
            </div>
            <div style="font-size:1.1rem; color:#334155;">
                Attendance was already recorded for today at <b>{time_s}</b>.
            </div>
            <div style="font-size:0.85rem; color:#64748B; margin-top:10px;">
                Card UID: <code style="background:#FEF3C7; color:#92400E; padding:2px 8px; border-radius:4px;">{uid}</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # Unknown Card: Prompt to link student name immediately
        st.markdown(f"""
        <div class="scan-card-new">
            <div style="font-size:3rem; line-height:1;">🆕</div>
            <div style="font-size:1.4rem; color:#1E40AF; font-weight:800; margin:8px 0 4px;">
                Card Scanned! (Not Registered Yet)
            </div>
            <div style="font-size:1rem; color:#334155;">
                UID: <code style="background:#DBEAFE; color:#1E40AF; font-size:1.05rem; padding:3px 8px; border-radius:4px; font-weight:700;">{uid}</code>
            </div>
            <div style="font-size:0.9rem; color:#475569; margin-top:6px;">
                Enter your details below to register this card and mark attendance:
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("register_unknown_card_form"):
            r1, r2 = st.columns([3, 2])
            new_name = r1.text_input("Your Full Name *", placeholder="e.g. John Doe")
            new_roll = r2.text_input("Roll / ID Number (optional)", placeholder="e.g. CS01")

            if st.form_submit_button("✅ Save Card & Mark Present", type="primary", use_container_width=True):
                if new_name.strip():
                    register_card(new_name.strip(), uid, new_roll.strip() if new_roll else None)
                    # Mark attendance
                    student = get_student_by_rfid(uid)
                    outcome = mark_attendance(
                        student_id=student["id"],
                        name=student["name"],
                        roll=student["roll"],
                        dept=student["dept"],
                        status="Present",
                        scan_time=time_s,
                    )
                    st.session_state["last_scan"] = {
                        "name": student["name"],
                        "roll": student["roll"],
                        "uid": uid,
                        "time": time_s,
                        "result": "present",
                    }
                    st.success(f"Registered! Welcome {new_name.strip()}!")
                    st.rerun()
                else:
                    st.warning("Please enter your name.")

else:
    # Idle state — waiting for tap
    st.markdown("""
    <div class="scan-card-idle">
        <div style="font-size:3.5rem; line-height:1; color:#2563EB;">📡</div>
        <div style="font-size:1.4rem; font-weight:800; color:#1E293B; margin-top:12px;">
            Ready to Scan
        </div>
        <div style="font-size:0.95rem; color:#64748B; margin-top:4px;">
            Tap your RFID card on the reader. Your name will appear here.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Manual Scan / Quick Register Tool ─────────────────────────────────────────
with st.expander("⚡ Manual Scan / Register Card", expanded=False):
    st.caption("You can also register a card UID manually or test a scan:")
    tc1, tc2, tc3 = st.columns([3, 3, 2])
    test_uid = tc1.text_input("Card UID", placeholder="e.g. 53:8E:B2:1A")
    test_name = tc2.text_input("Student Name", placeholder="e.g. John Doe")
    with tc3:
        st.write("")
        st.write("")
        if st.button("Mark Present", type="primary", use_container_width=True):
            if test_uid.strip():
                uid_clean = test_uid.strip().upper()
                if test_name.strip():
                    register_card(test_name.strip(), uid_clean)
                student = get_student_by_rfid(uid_clean)
                scan_time = datetime.now().strftime("%I:%M %p")

                if student:
                    outcome = mark_attendance(
                        student_id=student["id"],
                        name=student["name"],
                        roll=student["roll"],
                        dept=student["dept"],
                        status="Present",
                        scan_time=scan_time,
                    )
                    st.session_state["last_scan"] = {
                        "name": student["name"],
                        "roll": student["roll"],
                        "uid": uid_clean,
                        "time": scan_time,
                        "result": "duplicate" if outcome == "duplicate" else "present",
                    }
                else:
                    st.session_state["last_scan"] = {
                        "name": "Unknown",
                        "roll": "—",
                        "uid": uid_clean,
                        "time": scan_time,
                        "result": "unknown",
                    }
                st.rerun()
            else:
                st.warning("Please enter a Card UID.")

# ── Table: Students Present Today ─────────────────────────────────────────────
st.divider()

today_records = get_today_attendance()

c_left, c_right = st.columns([3, 1])
with c_left:
    st.subheader(f"📋 Students Present Today ({len(today_records)})")
with c_right:
    st.write(f"**Date:** {date.today().strftime('%d %b %Y')}")

if today_records.empty:
    st.info("No students present yet today. Scan an RFID card to record the first attendance!")
else:
    # Get student card UIDs
    students_df = get_all_students()
    rfid_map = dict(zip(students_df["id"], students_df["rfid"])) if not students_df.empty else {}

    display_df = today_records.copy()
    display_df["rfid"] = display_df["student_id"].map(rfid_map).fillna("—")

    display_df = display_df[["name", "roll", "time", "status", "rfid"]].rename(
        columns={
            "name": "Student Name",
            "roll": "Roll / ID",
            "time": "Scan Time",
            "status": "Attendance Status",
            "rfid": "RFID Card UID",
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
