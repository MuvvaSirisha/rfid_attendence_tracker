"""
SmartAttend — Attendance Processor
Handles the RFID UID → student lookup → attendance marking pipeline.
Works with both serial (PySerial) and Wi-Fi (Flask) scan sources.
"""

from datetime import datetime
from database.db import get_student_by_rfid, mark_attendance


def process_rfid_scan(uid: str) -> dict:
    """
    Given an RFID UID string, look up the student and mark attendance.
    Returns a result dict with keys:
        uid, name, roll, dept, time, result, message
    result values: 'present', 'duplicate', 'unknown'
    """
    uid_upper = uid.strip().upper()
    scan_time = datetime.now().strftime("%H:%M")
    student   = get_student_by_rfid(uid_upper)

    if student is None:
        return {
            "uid":     uid_upper,
            "name":    "Unknown Card",
            "roll":    "—",
            "dept":    "—",
            "time":    scan_time,
            "result":  "unknown",
            "message": f"UID {uid_upper} is not registered in the system.",
        }

    outcome = mark_attendance(
        student_id = student["id"],
        name       = student["name"],
        roll       = student["roll"],
        dept       = student["dept"],
        status     = "Present",
        scan_time  = scan_time,
    )

    if outcome == "duplicate":
        return {
            "uid":     uid_upper,
            "name":    student["name"],
            "roll":    student["roll"],
            "dept":    student["dept"],
            "time":    scan_time,
            "result":  "duplicate",
            "message": "Attendance already marked for today.",
        }

    return {
        "uid":     uid_upper,
        "name":    student["name"],
        "roll":    student["roll"],
        "dept":    student["dept"],
        "time":    scan_time,
        "result":  "present",
        "message": "Attendance marked successfully.",
    }
