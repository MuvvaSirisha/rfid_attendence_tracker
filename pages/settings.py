"""
SmartAttend — Settings Page
Configure Flask API URL, serial port defaults, demo data management, and app info.
"""

import streamlit as st
from datetime import date
from database.db import get_all_students, get_attendance, seed_if_empty, init_db
from utils.ui_helpers import inject_css, section_header, page_header
from utils.serial_comm import SERIAL_AVAILABLE, get_serial_manager

try:
    import serial.tools.list_ports
    CAN_LIST_PORTS = True
except ImportError:
    CAN_LIST_PORTS = False


def render():
    inject_css()
    page_header("⚙️ Settings", "Configure connections, preferences, and system information")

    # ── Flask API Settings ─────────────────────────────────────────────────────
    section_header("🌐 Flask API (Wi-Fi Mode)")
    st.markdown("""
    The Flask API acts as the bridge between the ESP32 (over Wi-Fi) and the SQLite database.

    **To start the API:**
    ```
    python api/flask_api.py
    ```
    The API runs on `http://localhost:5000`.  
    Set the ESP32 sketch variable `SERVER_IP` to your PC's IP address (shown when API starts).
    """)

    flask_url = st.text_input(
        "Flask API URL",
        value=st.session_state.get("flask_url", "http://localhost:5000"),
        help="Change this if you're running the API on a different host/port.",
    )
    if st.button("Save API URL"):
        st.session_state["flask_url"] = flask_url
        st.success("✅ API URL saved for this session.")

    st.divider()

    # ── Serial / COM Port Settings ─────────────────────────────────────────────
    section_header("🔌 Serial / USB Mode")
    if not SERIAL_AVAILABLE:
        st.warning("PySerial is not installed. Install it with: `pip install pyserial`")
    else:
        st.markdown("Configure the default serial settings for USB ESP32 connection.")
        mgr = get_serial_manager()

        sc1, sc2 = st.columns(2)
        with sc1:
            if CAN_LIST_PORTS:
                import serial.tools.list_ports
                ports = [p.device for p in serial.tools.list_ports.comports()]
                st.info(f"**Available ports:** {', '.join(ports) if ports else 'None detected'}")
            else:
                st.info("Cannot list ports (serial.tools not available).")
        with sc2:
            default_baud = st.selectbox(
                "Default Baud Rate",
                [9600, 57600, 115200],
                index=2,
                key="settings_baud",
            )
            st.caption("Must match `Serial.begin(...)` in your ESP32 sketch (default 115200).")

        st.markdown("""
        **ESP32 Serial Sketch:**  
        For USB serial mode, modify the sketch to output lines like:  
        `UID:04:A3:F1:7C:05`  
        instead of sending HTTP POST requests (removes the Wi-Fi requirement).
        """)

    st.divider()

    # ── Database Info ──────────────────────────────────────────────────────────
    section_header("🗄️ Database")
    students = get_all_students()
    all_att  = get_attendance()

    db1, db2, db3 = st.columns(3)
    db1.metric("Registered Students", len(students))
    db2.metric("Total Attendance Records", len(all_att))
    db3.metric("Departments", students["dept"].nunique() if not students.empty else 0)

    st.caption("Database file: `smartattend.db` (in project root)")

    if not students.empty:
        st.markdown("**Department breakdown:**")
        dept_counts = students["dept"].value_counts().reset_index()
        dept_counts.columns = ["Department", "Students"]
        st.dataframe(dept_counts, use_container_width=False, hide_index=True)

    st.divider()

    # ── Sample Data ───────────────────────────────────────────────────────────
    section_header("🧪 Demo Data")
    st.markdown("""
    The database was seeded with **15 sample students** and **30 days of randomised attendance**  
    when the app was first launched. This data is clearly synthetic and used for demonstration only.

    Sample student RFID UIDs follow the pattern: `04:A3:F1:7C:01` through `04:A3:F1:7C:0F`.
    """)

    if st.button("🔄 Re-seed Demo Data (adds students if DB is empty)"):
        init_db()
        seed_if_empty()
        st.success("Demo data checked / re-seeded.")
        st.rerun()

    st.divider()

    # ── About ──────────────────────────────────────────────────────────────────
    section_header("ℹ️ About")
    st.markdown("""
    **Smart RFID Attendance System** — v2.0  

    | Component | Detail |
    |---|---|
    | Hardware | ESP32 Dev Board + RC522 RFID Reader |
    | RFID Cards | 13.56 MHz Mifare Classic |
    | Backend | Python 3 · SQLite · Flask |
    | Dashboard | Streamlit · Plotly · Pandas |
    | Communication | Wi-Fi HTTP (default) · USB Serial (optional) |

    **Data flow:**
    ```
    RFID Card → RC522 Reader → ESP32
                                  ↓ Wi-Fi (HTTP POST)
                           Flask API (api/flask_api.py)
                                  ↓
                           SQLite Database (smartattend.db)
                                  ↓
                     Streamlit Dashboard (app.py)
    ```

    **Project files:**
    ```
    app.py                  — Main Streamlit entry point
    api/flask_api.py        — Flask REST API for ESP32
    database/db.py          — SQLite operations
    pages/                  — Dashboard, Students, Attendance, Scan, Reports, Settings
    utils/                  — Charts, UI helpers, Serial manager, Attendance processor
    esp32/                  — Arduino sketches for ESP32
    smartattend.db          — SQLite database (auto-created)
    requirements.txt        — Python dependencies
    ```
    """)
