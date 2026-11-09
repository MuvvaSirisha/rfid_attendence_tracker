"""
SmartAttend — Serial Communication Module
Manages PySerial connection to ESP32 for direct USB RFID scanning.
This is an ALTERNATIVE to the Flask Wi-Fi path:
  - Wi-Fi path: ESP32 → Flask API → SQLite (no USB cable needed)
  - Serial path: ESP32 (serial-only sketch) → PySerial → SQLite (USB cable)
"""

import threading
import queue
import time
from typing import Optional
import streamlit as st

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class SerialManager:
    """
    Thread-safe serial port manager.
    Runs a background reader thread that pushes lines into a queue.
    Streamlit pages poll the queue for new RFID UIDs.
    """

    def __init__(self):
        self._ser: Optional["serial.Serial"] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._queue: queue.Queue = queue.Queue(maxsize=50)
        self._lock = threading.Lock()
        self._port   = ""
        self._baud   = 115200
        self._connected = False
        self._last_error = ""

    # ── Public properties ────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    @property
    def port(self) -> str:
        return self._port

    @property
    def baud(self) -> int:
        return self._baud

    @property
    def last_error(self) -> str:
        return self._last_error

    # ── Connection control ───────────────────────────────────────────────────

    def connect(self, port: str, baud: int = 115200) -> bool:
        if not SERIAL_AVAILABLE:
            self._last_error = "PySerial not installed. Run: pip install pyserial"
            return False
        self.disconnect()
        try:
            self._ser = serial.Serial(port, baud, timeout=1)
            self._port   = port
            self._baud   = baud
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            with self._lock:
                self._connected  = True
                self._last_error = ""
            return True
        except Exception as exc:
            self._last_error = str(exc)
            self._connected  = False
            return False

    def disconnect(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass
        with self._lock:
            self._connected = False
        self._ser    = None
        self._thread = None

    # ── Background reader ────────────────────────────────────────────────────

    def _read_loop(self):
        while not self._stop_event.is_set():
            try:
                if self._ser and self._ser.in_waiting:
                    line = self._ser.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        self._handle_line(line)
                else:
                    time.sleep(0.05)
            except Exception as exc:
                with self._lock:
                    self._connected  = False
                    self._last_error = str(exc)
                break

    def _handle_line(self, line: str):
        """
        Parse lines from ESP32 serial output.
        Expected format from the serial-mode sketch:
            UID:04:A3:F1:7C:05
        Any line NOT starting with 'UID:' is treated as a debug message.
        """
        if line.startswith("UID:"):
            uid = line[4:].strip().upper()
            if not self._queue.full():
                self._queue.put(uid)

    # ── Queue access ─────────────────────────────────────────────────────────

    def poll_uid(self) -> Optional[str]:
        """Return one UID from the queue, or None if empty."""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    # ── Port discovery ───────────────────────────────────────────────────────

    @staticmethod
    def list_ports() -> list[str]:
        if not SERIAL_AVAILABLE:
            return []
        return [p.device for p in serial.tools.list_ports.comports()]


# ── Singleton stored in Streamlit session state ────────────────────────────────

def get_serial_manager() -> SerialManager:
    if "serial_mgr" not in st.session_state:
        st.session_state["serial_mgr"] = SerialManager()
    return st.session_state["serial_mgr"]
