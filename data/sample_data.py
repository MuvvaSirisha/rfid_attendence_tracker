"""
SmartAttend — Sample Data (Stage 1, in-memory only)
"""

import random
from datetime import date, datetime, timedelta
import pandas as pd

random.seed(42)

DEPARTMENTS = ["CS", "EC", "ME", "Civil", "EE"]

STUDENTS = [
    {"id": 1,  "name": "Aarav Patel",    "roll": "CS001", "dept": "CS",    "year": 2, "rfid": "04:A3:F1:7C:01"},
    {"id": 2,  "name": "Diya Sharma",    "roll": "CS002", "dept": "CS",    "year": 2, "rfid": "04:A3:F1:7C:02"},
    {"id": 3,  "name": "Rohan Mehta",    "roll": "EC001", "dept": "EC",    "year": 3, "rfid": "04:A3:F1:7C:03"},
    {"id": 4,  "name": "Ishita Nair",    "roll": "EC002", "dept": "EC",    "year": 3, "rfid": "04:A3:F1:7C:04"},
    {"id": 5,  "name": "Karan Singh",    "roll": "ME001", "dept": "ME",    "year": 1, "rfid": "04:A3:F1:7C:05"},
    {"id": 6,  "name": "Meera Iyer",     "roll": "ME002", "dept": "ME",    "year": 1, "rfid": "04:A3:F1:7C:06"},
    {"id": 7,  "name": "Arjun Desai",    "roll": "CS003", "dept": "CS",    "year": 2, "rfid": "04:A3:F1:7C:07"},
    {"id": 8,  "name": "Tanvi Kulkarni", "roll": "EC003", "dept": "EC",    "year": 2, "rfid": "04:A3:F1:7C:08"},
    {"id": 9,  "name": "Yash Gupta",     "roll": "ME003", "dept": "ME",    "year": 3, "rfid": "04:A3:F1:7C:09"},
    {"id": 10, "name": "Shruti Verma",   "roll": "CV001", "dept": "Civil", "year": 4, "rfid": "04:A3:F1:7C:0A"},
]


def get_students() -> pd.DataFrame:
    return pd.DataFrame(STUDENTS)


def get_attendance(students_df: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    """Generate attendance for the last N working days."""
    random.seed(99)
    today = date.today()
    rows = []
    record_id = 1

    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        if day.weekday() == 6:   # skip Sunday
            continue
        for _, stu in students_df.iterrows():
            roll = random.random()
            if roll < 0.80:
                status = "Present"
                t = datetime(day.year, day.month, day.day,
                             random.randint(8, 9), random.randint(0, 59))
                scan_time = t.strftime("%H:%M")
            elif roll < 0.88:
                status = "Late"
                t = datetime(day.year, day.month, day.day,
                             random.randint(10, 11), random.randint(0, 59))
                scan_time = t.strftime("%H:%M")
            else:
                status = "Absent"
                scan_time = "—"

            rows.append({
                "id": record_id,
                "student_id": int(stu["id"]),
                "name": stu["name"],
                "roll": stu["roll"],
                "dept": stu["dept"],
                "date": day.isoformat(),
                "time": scan_time,
                "status": status,
            })
            record_id += 1

    return pd.DataFrame(rows)


def get_recent_scans(students_df: pd.DataFrame) -> pd.DataFrame:
    """Simulate the last few RFID scans (as if coming from ESP32)."""
    random.seed(7)
    now = datetime.now()
    sample = students_df.sample(n=min(8, len(students_df)), random_state=7)
    rows = []
    for i, (_, stu) in enumerate(sample.iterrows()):
        ts = now - timedelta(minutes=i * random.randint(3, 10))
        valid = random.random() > 0.1
        rows.append({
            "Time": ts.strftime("%H:%M:%S"),
            "Name": stu["name"] if valid else "Unknown",
            "Roll": stu["roll"] if valid else "—",
            "RFID UID": stu["rfid"],
            "Result": "✅ Present" if valid else "❌ Unknown Card",
        })
    return pd.DataFrame(rows)
