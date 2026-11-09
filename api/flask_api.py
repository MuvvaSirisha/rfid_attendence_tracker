"""
SmartAttend — Flask REST API
============================
ESP32 scans a card → POSTs UID here over Wi-Fi →
API looks up student → marks attendance in SQLite →
returns result back to ESP32 (for LED/buzzer feedback).

Run in Terminal 1:  python api/flask_api.py
Run in Terminal 2:  python -m streamlit run app.py
"""

from flask import Flask, request, jsonify
from datetime import datetime
import sys
import os
import socket

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import get_student_by_rfid, mark_attendance

app = Flask(__name__)

# In-memory list of recent scans (last 50) — polled by the dashboard
recent_scans: list[dict] = []


# ── POST /api/scan  ──────────────────────────────────────────────────────────
@app.route("/api/scan", methods=["POST"])
def scan():
    """
    Called by ESP32 when a card is tapped.
    Body JSON : { "uid": "04:A3:F1:7C:05" }
    Returns   : { "status": "ok"|"duplicate"|"unknown", "name": "...", ... }
    """
    data = request.get_json(silent=True)
    if not data or "uid" not in data:
        return jsonify({"status": "error", "message": "Missing uid field"}), 400

    uid      = data["uid"].strip().upper()
    time_str = datetime.now().strftime("%H:%M")
    student  = get_student_by_rfid(uid)

    if student:
        outcome = mark_attendance(
            student_id = student["id"],
            name       = student["name"],
            roll       = student["roll"],
            dept       = student["dept"],
            status     = "Present",
            scan_time  = time_str,
        )

        entry = {
            "time":    time_str,
            "name":    student["name"],
            "student": student["name"],
            "roll":    student["roll"],
            "dept":    student["dept"],
            "uid":     uid,
            "result":  "Present" if outcome != "duplicate" else "Duplicate",
        }
        response = {
            "status":  "ok" if outcome != "duplicate" else "duplicate",
            "student": student["name"],
            **entry,
        }
        print(f"[SCAN] {time_str}  UID={uid}  → {outcome}  ({student['name']})")
    else:
        entry = {
            "time":   time_str,
            "name":   "Unknown",
            "roll":   "—",
            "dept":   "—",
            "uid":    uid,
            "result": "Unknown",
        }
        response = {"status": "unknown", **entry}
        print(f"[SCAN] {time_str}  UID={uid}  → Unknown card")

    # Prepend to recent scans list, keep max 50
    recent_scans.insert(0, entry)
    if len(recent_scans) > 50:
        recent_scans.pop()

    return jsonify(response), 200


# ── GET /api/scans  ──────────────────────────────────────────────────────────
@app.route("/api/scans", methods=["GET"])
def get_scans():
    """Dashboard polls this every few seconds for the live scan feed."""
    return jsonify(recent_scans), 200


# ── GET /api/status  ─────────────────────────────────────────────────────────
@app.route("/api/status", methods=["GET"])
def api_status():
    """Health-check endpoint — ESP32 and dashboard call this to verify the API is up."""
    return jsonify({
        "status":              "online",
        "time":                datetime.now().strftime("%H:%M:%S"),
        "total_scans_session": len(recent_scans),
    }), 200


# ── GET /api/students  ───────────────────────────────────────────────────────
@app.route("/api/students", methods=["GET"])
def get_students_api():
    """Return all registered students as JSON (optional helper endpoint)."""
    from database.db import get_all_students
    df = get_all_students()
    return jsonify(df.to_dict(orient="records")), 200


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "YOUR_PC_IP"

    print("=" * 55)
    print("  SmartAttend Flask API — Ready")
    print(f"  PC IP address  :  {local_ip}")
    print(f"  Scan endpoint  :  http://{local_ip}:5000/api/scan")
    print(f"  Status check   :  http://{local_ip}:5000/api/status")
    print()
    print("  Set SERVER_IP in ESP32 sketch to:", local_ip)
    print("=" * 55)

    app.run(host="0.0.0.0", port=5000, debug=False)
