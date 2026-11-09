"""
SmartAttend — SQLite Database Module
Handles all database operations: Students CRUD + Attendance tracking.
Database: smartattend.db (auto-created next to this file's parent)
"""

import sqlite3
import os
import random
from datetime import date, datetime, timedelta
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "smartattend.db")


# ══════════════════════════════════════════════════════════════════════════════
# Connection helper
# ══════════════════════════════════════════════════════════════════════════════

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ══════════════════════════════════════════════════════════════════════════════
# Schema initialization
# ══════════════════════════════════════════════════════════════════════════════

def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    NOT NULL,
            roll    TEXT    NOT NULL UNIQUE,
            dept    TEXT    NOT NULL,
            year    INTEGER NOT NULL,
            rfid    TEXT    NOT NULL UNIQUE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            name       TEXT    NOT NULL,
            roll       TEXT    NOT NULL,
            dept       TEXT    NOT NULL,
            date       TEXT    NOT NULL,
            time       TEXT    NOT NULL,
            status     TEXT    NOT NULL CHECK(status IN ('Present','Late','Absent')),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(student_id, date)
        )
    """)

    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# Sample data seeding
# ══════════════════════════════════════════════════════════════════════════════

SAMPLE_STUDENTS = [
    ("Aarav Patel",    "CS001", "CS",    2, "04:A3:F1:7C:01"),
    ("Diya Sharma",    "CS002", "CS",    2, "04:A3:F1:7C:02"),
    ("Rohan Mehta",    "EC001", "EC",    3, "04:A3:F1:7C:03"),
    ("Ishita Nair",    "EC002", "EC",    3, "04:A3:F1:7C:04"),
    ("Karan Singh",    "ME001", "ME",    1, "04:A3:F1:7C:05"),
    ("Meera Iyer",     "ME002", "ME",    1, "04:A3:F1:7C:06"),
    ("Arjun Desai",    "CS003", "CS",    2, "04:A3:F1:7C:07"),
    ("Tanvi Kulkarni", "EC003", "EC",    2, "04:A3:F1:7C:08"),
    ("Yash Gupta",     "ME003", "ME",    3, "04:A3:F1:7C:09"),
    ("Shruti Verma",   "CV001", "Civil", 4, "04:A3:F1:7C:0A"),
    ("Priya Joshi",    "CS004", "CS",    1, "04:A3:F1:7C:0B"),
    ("Rahul Kumar",    "EE001", "EE",    2, "04:A3:F1:7C:0C"),
    ("Neha Reddy",     "EE002", "EE",    3, "04:A3:F1:7C:0D"),
    ("Vikram Shah",    "CV002", "Civil", 2, "04:A3:F1:7C:0E"),
    ("Anjali Mishra",  "ME004", "ME",    4, "04:A3:F1:7C:0F"),
]


def seed_if_empty():
    """Kept empty — no dummy data added automatically."""
    pass


def seed_sample_data():
    """Only called if administrator explicitly clicks 'Add Demo Data'."""
    conn = get_conn()
    c = conn.cursor()

    if c.execute("SELECT COUNT(*) FROM students").fetchone()[0] > 0:
        conn.close()
        return

    c.executemany(
        "INSERT INTO students (name, roll, dept, year, rfid) VALUES (?,?,?,?,?)",
        SAMPLE_STUDENTS,
    )
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# Student CRUD
# ══════════════════════════════════════════════════════════════════════════════

def get_all_students() -> pd.DataFrame:
    conn = get_conn()
    df   = pd.read_sql("SELECT * FROM students ORDER BY dept, roll", conn)
    conn.close()
    return df


def add_student(name: str, roll: str, dept: str, year: int, rfid: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO students (name, roll, dept, year, rfid) VALUES (?,?,?,?,?)",
        (name.strip(), roll.strip().upper(), dept, int(year), rfid.strip().upper()),
    )
    conn.commit()
    conn.close()


def update_student(student_id: int, name: str, roll: str, dept: str, year: int, rfid: str):
    conn = get_conn()
    conn.execute(
        "UPDATE students SET name=?, roll=?, dept=?, year=?, rfid=? WHERE id=?",
        (name.strip(), roll.strip().upper(), dept, int(year), rfid.strip().upper(), student_id),
    )
    conn.commit()
    conn.close()


def delete_student(student_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
    conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()


def roll_exists(roll: str, exclude_id: int = None) -> bool:
    conn = get_conn()
    if exclude_id:
        row = conn.execute(
            "SELECT 1 FROM students WHERE roll=? AND id!=?", (roll.strip().upper(), exclude_id)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT 1 FROM students WHERE roll=?", (roll.strip().upper(),)
        ).fetchone()
    conn.close()
    return row is not None


def rfid_exists(rfid: str, exclude_id: int = None) -> bool:
    conn = get_conn()
    if exclude_id:
        row = conn.execute(
            "SELECT 1 FROM students WHERE rfid=? AND id!=?", (rfid.strip().upper(), exclude_id)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT 1 FROM students WHERE rfid=?", (rfid.strip().upper(),)
        ).fetchone()
    conn.close()
    return row is not None


def get_student_by_rfid(rfid: str):
    """Look up student by RFID UID — normalized comparison."""
    if not rfid:
        return None
    conn = get_conn()
    uid_clean = rfid.strip().upper()
    row  = conn.execute(
        "SELECT * FROM students WHERE UPPER(TRIM(rfid))=?", (uid_clean,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def register_card(name: str, uid: str, roll: str = None, dept: str = "General", year: int = 1) -> dict:
    """Quick register or update a student's card UID."""
    conn = get_conn()
    uid_clean = uid.strip().upper()
    name_clean = name.strip()

    existing = conn.execute("SELECT * FROM students WHERE UPPER(TRIM(rfid))=?", (uid_clean,)).fetchone()
    if existing:
        conn.execute("UPDATE students SET name=? WHERE id=?", (name_clean, existing["id"]))
        conn.commit()
        row = conn.execute("SELECT * FROM students WHERE id=?", (existing["id"],)).fetchone()
        conn.close()
        return dict(row)

    if not roll or not roll.strip():
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] + 1
        roll_val = f"ID{count:03d}"
    else:
        roll_val = roll.strip().upper()

    conn.execute(
        "INSERT INTO students (name, roll, dept, year, rfid) VALUES (?,?,?,?,?)",
        (name_clean, roll_val, dept, year, uid_clean),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM students WHERE UPPER(TRIM(rfid))=?", (uid_clean,)).fetchone()
    conn.close()
    return dict(row)


# ══════════════════════════════════════════════════════════════════════════════
# Attendance queries
# ══════════════════════════════════════════════════════════════════════════════

def get_attendance(date_from: str = None, date_to: str = None,
                   dept: str = None, status_filter: str = None) -> pd.DataFrame:
    conn   = get_conn()
    query  = "SELECT * FROM attendance WHERE 1=1"
    params = []
    if date_from:
        query  += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query  += " AND date <= ?"
        params.append(date_to)
    if dept and dept != "All":
        query  += " AND dept = ?"
        params.append(dept)
    if status_filter and status_filter != "All":
        query  += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY date DESC, time DESC"
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


def get_today_attendance() -> pd.DataFrame:
    return get_attendance(date.today().isoformat(), date.today().isoformat())


def mark_attendance(student_id: int, name: str, roll: str, dept: str,
                    status: str, scan_time: str = None) -> str:
    """
    Mark attendance for today. Returns one of:
      'marked'    — newly marked
      'updated'   — already existed, updated
      'duplicate' — already marked as Present/Late (no change)
    """
    today = date.today().isoformat()
    if scan_time is None:
        scan_time = datetime.now().strftime("%H:%M")

    conn     = get_conn()
    existing = conn.execute(
        "SELECT id, status FROM attendance WHERE student_id=? AND date=?",
        (student_id, today),
    ).fetchone()

    if existing:
        if existing["status"] in ("Present", "Late") and status == "Present":
            conn.close()
            return "duplicate"
        conn.execute(
            "UPDATE attendance SET status=?, time=? WHERE id=?",
            (status, scan_time, existing["id"]),
        )
        conn.commit()
        conn.close()
        return "updated"
    else:
        conn.execute(
            """INSERT INTO attendance
               (student_id, name, roll, dept, date, time, status)
               VALUES (?,?,?,?,?,?,?)""",
            (student_id, name, roll, dept, today, scan_time, status),
        )
        conn.commit()
        conn.close()
        return "marked"


# ══════════════════════════════════════════════════════════════════════════════
# Analytics helpers
# ══════════════════════════════════════════════════════════════════════════════

def get_daily_summary(days: int = 7) -> pd.DataFrame:
    """Return per-day present/late/absent counts for the last N days."""
    today    = date.today()
    date_from = (today - timedelta(days=days - 1)).isoformat()
    df = get_attendance(date_from, today.isoformat())
    if df.empty:
        return pd.DataFrame(columns=["date", "status", "count"])
    summary = df.groupby(["date", "status"]).size().reset_index(name="count")
    return summary


def get_student_attendance_pct() -> pd.DataFrame:
    """Return each student's overall attendance percentage."""
    conn = get_conn()
    df   = pd.read_sql("""
        SELECT
            s.id, s.name, s.roll, s.dept, s.year,
            COUNT(a.id)                                        AS total_days,
            SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END) AS present_days
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id
        ORDER BY s.dept, s.roll
    """, conn)
    conn.close()
    if df.empty:
        return df
    df["attendance_pct"] = df.apply(
        lambda r: round(r["present_days"] / r["total_days"] * 100, 1) if r["total_days"] > 0 else 0,
        axis=1,
    )
    return df


def get_low_attendance_students(threshold: int = 75) -> pd.DataFrame:
    df = get_student_attendance_pct()
    if df.empty:
        return df
    return df[df["attendance_pct"] < threshold].sort_values("attendance_pct")


def get_monthly_summary() -> pd.DataFrame:
    """Group attendance by month for bar charts."""
    conn = get_conn()
    df   = pd.read_sql("""
        SELECT
            strftime('%Y-%m', date) AS month,
            status,
            COUNT(*) AS count
        FROM attendance
        GROUP BY month, status
        ORDER BY month
    """, conn)
    conn.close()
    return df


def get_dept_summary() -> pd.DataFrame:
    """Department-wise attendance breakdown."""
    conn = get_conn()
    df   = pd.read_sql("""
        SELECT
            dept,
            COUNT(*) AS total,
            SUM(CASE WHEN status IN ('Present','Late') THEN 1 ELSE 0 END) AS present
        FROM attendance
        GROUP BY dept
        ORDER BY dept
    """, conn)
    conn.close()
    if not df.empty:
        df["pct"] = df.apply(
            lambda r: round(r["present"] / r["total"] * 100, 1) if r["total"] > 0 else 0,
            axis=1,
        )
    return df
