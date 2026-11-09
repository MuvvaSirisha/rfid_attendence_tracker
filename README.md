# Smart RFID Attendance System 📡

A modern, fully functional college attendance management dashboard built with **Python**, **Streamlit**, **SQLite**, and **ESP32 + RC522 RFID Reader**.

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch the dashboard

```bash
python -m streamlit run app.py
```

The dashboard opens at **http://localhost:8501** and auto-creates the database with 15 demo students and 30 days of sample data on first run.

---

## 📡 Connecting the ESP32 (Wi-Fi Mode)

This is the recommended mode — no USB cable needed after setup.

### Step 1 — Start the Flask API

```bash
# In a separate terminal
python api/flask_api.py
```

It will print your **PC's IP address** — note it down.

### Step 2 — Configure the ESP32 sketch

Open `esp32/rfid_reader/rfid_reader.ino` in Arduino IDE and set:

```cpp
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";
const char* SERVER_IP = "192.168.1.X";   // ← your PC's IP from Step 1
```

### Step 3 — Upload and scan

Upload the sketch to the ESP32. When a card is tapped:
- Green LED flashes → attendance marked ✅
- Red LED flashes → unknown card ❌

The dashboard's **Scan Attendance** page updates live every 3 seconds.

---

## 🔌 Connecting the ESP32 (USB Serial Mode)

Use this mode if you prefer a direct USB connection instead of Wi-Fi.

1. Modify the ESP32 sketch to print:  
   `UID:04:A3:F1:7C:05` for each card scan (instead of HTTP POST)
2. Connect the ESP32 via USB
3. In the dashboard → **Scan Attendance** → Select **USB Serial** mode
4. Choose the COM port and click **Connect**

---

## 🗂️ Project Structure

```
Smart-RFID-Attendance/
├── app.py                    ← Main Streamlit entry point
├── requirements.txt          ← Python dependencies
├── smartattend.db            ← SQLite database (auto-created)
│
├── .streamlit/
│   └── config.toml           ← Theme configuration
│
├── api/
│   └── flask_api.py          ← Flask REST API (ESP32 Wi-Fi endpoint)
│
├── database/
│   └── db.py                 ← SQLite CRUD + analytics queries
│
├── pages/
│   ├── dashboard.py          ← Home: KPIs, charts, recent records
│   ├── students.py           ← Add / Edit / Delete students
│   ├── attendance.py         ← Browse, filter, export records
│   ├── scan.py               ← Live RFID scanning page
│   ├── reports.py            ← Analytics: trends, per-student %, low attendance
│   └── settings.py           ← Configuration & system info
│
├── utils/
│   ├── ui_helpers.py         ← Shared HTML components & CSS
│   ├── charts.py             ← Plotly chart builders
│   ├── serial_comm.py        ← PySerial manager for USB mode
│   └── attendance_processor.py ← RFID UID → attendance marking logic
│
└── esp32/
    ├── rfid_reader/
    │   └── rfid_reader.ino   ← Wi-Fi sketch (ESP32 → Flask)
    └── wiring_test/
        └── wiring_test.ino   ← Hardware wiring test
```

---

## 🛠️ ESP32 Wiring

| RC522 Pin | ESP32 GPIO |
|-----------|------------|
| SDA       | GPIO 5     |
| SCK       | GPIO 18    |
| MOSI      | GPIO 23    |
| MISO      | GPIO 19    |
| RST       | GPIO 27    |
| 3.3V      | 3.3V       |
| GND       | GND        |

| LED/Buzzer | ESP32 GPIO |
|------------|------------|
| Green LED  | GPIO 4 (220Ω to GND) |
| Red LED    | GPIO 16 (220Ω to GND) |
| Buzzer     | GPIO 2 |

---

## 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| 🏠 Dashboard | KPI summary cards, weekly bar chart, attendance donut, recent entries |
| 🎓 Student Management | Add/Edit/Delete students, search, RFID UID registration |
| 📋 Attendance Records | Browse records with date/dept/status filters; CSV & Excel export |
| 📡 Scan Attendance | Live RFID scanning via Flask API or USB serial |
| 📊 Reports & Analytics | Daily/monthly trends, per-student %, dept breakdown, low-attendance alerts |
| ⚙️ Settings | Flask API config, serial port info, database stats |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | Dashboard UI |
| pandas | Data processing |
| plotly | Interactive charts |
| flask | REST API for ESP32 Wi-Fi |
| requests | Dashboard → Flask API calls |
| pyserial | USB serial (ESP32 direct connection) |
| openpyxl | Excel export |
| streamlit-autorefresh | Live scan auto-refresh |

---

## 🗄️ Database Schema

**students**
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
roll TEXT NOT NULL UNIQUE,
dept TEXT NOT NULL,
year INTEGER NOT NULL,
rfid TEXT NOT NULL UNIQUE
```

**attendance**
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,
student_id INTEGER REFERENCES students(id),
name TEXT, roll TEXT, dept TEXT,
date TEXT NOT NULL,
time TEXT NOT NULL,
status TEXT CHECK(status IN ('Present','Late','Absent')),
UNIQUE(student_id, date)   -- prevents duplicate entries
```

---

## 🔐 Notes

- **Demo data** is seeded only on first run (when the DB is empty). It is clearly labelled as synthetic.
- **Duplicate scan prevention** is enforced at the database level — scanning the same card twice on the same day shows "Already Marked".
- All data is stored **locally** in `smartattend.db`. No external cloud services or paid APIs are used.
