"""
SmartAttend — Live RFID Attendance Scanner
Scans RFID cards via USB Serial or Wi-Fi (Flask) and immediately displays the student's name.
No dummy data. Real scans only.
"""

import streamlit as st
import requests
from datetime import date, datetime

from database.db import (
    get_all_students, get_today_attendance,
    get_student_by_rfid, register_card,
)
from utils.ui_helpers import inject_css, section_header, page_header, style_table
from utils.serial_comm import get_serial_manager, SERIAL_AVAILABLE
from utils.attendance_processor import process_rfid_scan

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

FLASK_URL = "http://localhost:5000"


def check_flask_online() -> bool:
    try:
        return requests.get(f"{FLASK_URL}/api/status", timeout=0.8).status_code == 200
    except Exception:
        return False


def get_flask_scans() -> list:
    try:
        r = requests.get(f"{FLASK_URL}/api/scans", timeout=0.8)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def render():
    inject_css()
    page_header("📡 Live RFID Scanner", "Tap your RFID card on the reader to record attendance and display your name")

    # Session state for tracking last scan
    if "last_scan" not in st.session_state:
        st.session_state["last_scan"] = None
    if "recent_scans_list" not in st.session_state:
        st.session_state["recent_scans_list"] = []

    # ── Connection Setup ───────────────────────────────────────────────────────
    with st.expander("🔌 ESP32 Connection Settings (USB Serial or Wi-Fi)", expanded=True):
        mode = st.radio(
            "Select how your ESP32 is connected:",
            ["🔌 USB Cable (Serial Port)", "🌐 Wi-Fi (Flask API)"],
            horizontal=True,
        )

        use_serial = mode.startswith("🔌")
        serial_mgr = get_serial_manager() if SERIAL_AVAILABLE else None

        if use_serial:
            if not SERIAL_AVAILABLE:
                st.error("PySerial is not installed. Run: `pip install pyserial`")
            else:
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                ports = serial_mgr.list_ports()
                port_list = ports if ports else ["No COM ports detected"]
                cur_port = serial_mgr.port if serial_mgr.port in port_list else port_list[0]
                sel_port = c1.selectbox("COM Port", port_list, index=port_list.index(cur_port))
                baud = c2.selectbox("Baud Rate", [115200, 9600, 57600], index=0)

                with c3:
                    st.write("")
                    st.write("")
                    if not serial_mgr.is_connected:
                        if st.button("🔗 Connect", type="primary", use_container_width=True):
                            if ports and serial_mgr.connect(sel_port, baud):
                                st.success(f"Connected to {sel_port}!")
                                st.rerun()
                            else:
                                st.error(serial_mgr.last_error or "Could not open port")
                    else:
                        if st.button("⛔ Disconnect", use_container_width=True):
                            serial_mgr.disconnect()
                            st.rerun()

                with c4:
                    st.write("")
                    st.write("")
                    if serial_mgr.is_connected:
                        st.success("🟢 Connected")
                    else:
                        st.info("⚪ Disconnected")

        else:
            online = check_flask_online()
            fc1, fc2 = st.columns([2, 1])
            with fc1:
                if online:
                    st.success("🟢 Flask API is Online at `http://localhost:5000`")
                else:
                    st.warning("🔴 Flask API is Offline. Run in terminal: `python api/flask_api.py`")
            with fc2:
                if st.button("🔄 Refresh Status", use_container_width=True):
                    st.rerun()

    # Auto-refresh every 2 seconds when reading
    if HAS_AUTOREFRESH:
        st_autorefresh(interval=2000, key="rfid_live_autorefresh")

    # ── Check for incoming scans from hardware ────────────────────────────────
    # 1. From Serial
    if SERIAL_AVAILABLE:
        serial_mgr = get_serial_manager()
        if serial_mgr.is_connected:
            uid = serial_mgr.poll_uid()
            if uid:
                res = process_rfid_scan(uid)
                st.session_state["last_scan"] = res
                st.session_state["recent_scans_list"].insert(0, res)

    # 2. From Flask API (if running)
    if check_flask_online():
        flask_scans = get_flask_scans()
        if flask_scans:
            latest = flask_scans[0]
            # If newer than current last_scan
            last = st.session_state["last_scan"]
            if not last or last.get("uid") != latest.get("uid") or last.get("time") != latest.get("time"):
                st.session_state["last_scan"] = {
                    "uid":     latest.get("uid", ""),
                    "name":    latest.get("name", "Unknown"),
                    "roll":    latest.get("roll", "—"),
                    "time":    latest.get("time", ""),
                    "result":  "present" if latest.get("result") == "Present" else (
                        "duplicate" if latest.get("result") == "Duplicate" else "unknown"
                    ),
                    "message": "Scan recorded",
                }

    # ── BIG LIVE SCAN DISPLAY ─────────────────────────────────────────────────
    last_scan = st.session_state.get("last_scan")

    if last_scan:
        result = last_scan.get("result", "unknown")
        name   = last_scan.get("name", "Unknown")
        roll   = last_scan.get("roll", "—")
        time_s = last_scan.get("time", datetime.now().strftime("%H:%M:%S"))
        uid    = last_scan.get("uid", "")

        if result == "present":
            st.markdown(f"""
            <div style="background:#F0FDF4; border:3px solid #16A34A; border-radius:18px; padding:36px; text-align:center; box-shadow:0 4px 16px rgba(22,163,74,0.15); margin-bottom:24px;">
                <div style="font-size:3.8rem; line-height:1;">🎉</div>
                <div style="font-size:1.1rem; color:#15803D; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; margin-top:8px;">
                    Attendance Recorded!
                </div>
                <div style="font-size:2.6rem; color:#0F172A; font-weight:800; margin:10px 0;">
                    {name}
                </div>
                <div style="font-size:1.15rem; color:#334155; font-weight:500;">
                    Roll / ID: <b>{roll}</b> &nbsp;•&nbsp; Time: <b>{time_s}</b> &nbsp;•&nbsp; Date: <b>{date.today().strftime('%d %b %Y')}</b>
                </div>
                <div style="font-size:0.85rem; color:#64748B; margin-top:12px;">
                    RFID Card UID: <code style="background:#DCFCE7; color:#166534; padding:3px 8px; border-radius:6px;">{uid}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

        elif result == "duplicate":
            st.markdown(f"""
            <div style="background:#FFFBEB; border:3px solid #D97706; border-radius:18px; padding:36px; text-align:center; box-shadow:0 4px 16px rgba(217,119,6,0.15); margin-bottom:24px;">
                <div style="font-size:3.8rem; line-height:1;">👋</div>
                <div style="font-size:1.1rem; color:#B45309; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; margin-top:8px;">
                    Already Marked Today
                </div>
                <div style="font-size:2.6rem; color:#0F172A; font-weight:800; margin:10px 0;">
                    {name}
                </div>
                <div style="font-size:1.1rem; color:#334155;">
                    Your attendance is already saved for today at <b>{time_s}</b>.
                </div>
                <div style="font-size:0.85rem; color:#64748B; margin-top:12px;">
                    RFID Card UID: <code style="background:#FEF3C7; color:#92400E; padding:3px 8px; border-radius:6px;">{uid}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

        else:
            # Unregistered Card Detected — Allow 1-click registration right here!
            st.markdown(f"""
            <div style="background:#EFF6FF; border:3px solid #2563EB; border-radius:18px; padding:30px; text-align:center; margin-bottom:20px;">
                <div style="font-size:3.2rem; line-height:1;">🆕</div>
                <div style="font-size:1.5rem; color:#1E40AF; font-weight:800; margin:10px 0 6px;">
                    New RFID Card Detected!
                </div>
                <div style="font-size:1.05rem; color:#334155;">
                    Card UID: <code style="background:#DBEAFE; color:#1E40AF; font-size:1.1rem; padding:4px 10px; border-radius:6px; font-weight:700;">{uid}</code>
                </div>
                <div style="font-size:0.95rem; color:#64748B; margin-top:8px;">
                    This card is not yet linked to your name. Enter your name below to register it:
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.form("quick_register_form", clear_on_submit=False):
                r1, r2 = st.columns([3, 2])
                new_name = r1.text_input("Your Full Name *", placeholder="e.g. Rahul Sharma")
                new_roll = r2.text_input("Roll / ID (optional)", placeholder="e.g. CS101")

                if st.form_submit_button("✅ Save Card & Mark Present", type="primary", use_container_width=True):
                    if new_name.strip():
                        register_card(new_name.strip(), uid, new_roll.strip() if new_roll else None)
                        # Process scan with the new name
                        updated_res = process_rfid_scan(uid)
                        st.session_state["last_scan"] = updated_res
                        st.session_state["recent_scans_list"].insert(0, updated_res)
                        st.success(f"Registered! Welcome, {new_name.strip()}!")
                        st.rerun()
                    else:
                        st.warning("Please type your name.")

    else:
        # Idle / Waiting display
        st.markdown(f"""
        <div style="background:#FFFFFF; border:2px dashed #CBD5E1; border-radius:18px; padding:48px 24px; text-align:center; margin-bottom:24px;">
            <div style="font-size:4rem; line-height:1; color:#2563EB;">📡</div>
            <div style="font-size:1.5rem; font-weight:800; color:#1E293B; margin-top:14px;">
                Ready to Scan
            </div>
            <div style="font-size:1rem; color:#64748B; margin-top:6px;">
                Tap your physical RFID card on the RC522 reader.
            </div>
            <div style="font-size:0.85rem; color:#94A3B8; margin-top:8px;">
                Current Time: {datetime.now().strftime('%I:%M:%S %p')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Test Scan Bar ─────────────────────────────────────────────────────────
    with st.expander("🧪 Test with a Card UID (or Register Card Manually)"):
        tc1, tc2, tc3 = st.columns([3, 3, 2])
        test_uid = tc1.text_input("Card UID", placeholder="e.g. 53:8E:B2:1A", key="manual_uid")
        test_name = tc2.text_input("Assign Name (Optional)", placeholder="e.g. Rahul Sharma", key="manual_name")
        with tc3:
            st.write("")
            st.write("")
            if st.button("⚡ Test Scan", type="primary", use_container_width=True):
                if test_uid.strip():
                    if test_name.strip():
                        register_card(test_name.strip(), test_uid.strip())
                    res = process_rfid_scan(test_uid.strip())
                    st.session_state["last_scan"] = res
                    st.session_state["recent_scans_list"].insert(0, res)
                    st.rerun()
                else:
                    st.warning("Enter a UID.")

    # ── Today's Real Attendance Records ───────────────────────────────────────
    st.divider()
    section_header("📋 Today's Attendance")

    today_att = get_today_attendance()
    all_students = get_all_students()

    k1, k2, k3 = st.columns(3)
    k1.metric("Registered People", len(all_students))
    k2.metric("✅ Present Today", len(today_att))
    k3.metric("📅 Today", date.today().strftime("%d %b %Y"))

    if today_att.empty:
        st.info("No attendance recorded yet today. Scan a card above to be the first!")
    else:
        def _style(val):
            return {
                "Present": "color:#15803D;font-weight:700;",
                "Late":    "color:#B45309;font-weight:700;",
                "Absent":  "color:#B91C1C;font-weight:700;",
            }.get(val, "")

        show = today_att[["name", "roll", "dept", "time", "status"]].rename(
            columns={"name": "Name", "roll": "Roll / ID", "dept": "Dept", "time": "Scan Time", "status": "Status"}
        )
        st.dataframe(
            style_table(show.style, _style, subset=["Status"]),
            use_container_width=True,
            hide_index=True,
        )
