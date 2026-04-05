import csv
import glob
import io
import os
import sqlite3
import subprocess
from contextlib import contextmanager
from datetime import datetime

import psutil

# ---------------------------------------------------------------------------
# Config (all overridable via environment variables)
# ---------------------------------------------------------------------------
DB_PATH      = os.environ.get("HISTORY_DB_PATH", "/tmp/rpi_dashboard.db")
HISTORY_DAYS = int(os.environ.get("HISTORY_DAYS", "7"))
TEMP_WARN    = float(os.environ.get("TEMP_WARN", "70"))
TEMP_CRIT    = float(os.environ.get("TEMP_CRIT", "80"))
CPU_WARN     = float(os.environ.get("CPU_WARN",  "70"))
CPU_CRIT     = float(os.environ.get("CPU_CRIT",  "85"))
RAM_WARN     = float(os.environ.get("RAM_WARN",  "70"))
RAM_CRIT     = float(os.environ.get("RAM_CRIT",  "85"))
DISK_WARN    = float(os.environ.get("DISK_WARN", "80"))
DISK_CRIT    = float(os.environ.get("DISK_CRIT", "90"))

# ---------------------------------------------------------------------------
# SQLite persistent history
# ---------------------------------------------------------------------------
def _init_db():
    with _db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT    NOT NULL,
                epoch     INTEGER NOT NULL,
                temp      REAL,
                fan_rpm   INTEGER,
                cpu       REAL,
                ram       REAL,
                disk      REAL,
                clock_mhz INTEGER
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_epoch ON readings(epoch)")


@contextmanager
def _db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _store_reading(stats: dict):
    epoch = int(datetime.now().timestamp())
    with _db() as con:
        con.execute(
            "INSERT INTO readings (ts, epoch, temp, fan_rpm, cpu, ram, disk, clock_mhz) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                stats["timestamp"],
                epoch,
                stats["temp"],
                stats["fan_rpm"],
                stats["cpu_usage"],
                stats["ram_usage"],
                stats["disk_usage"],
                stats["clock_speed"],
            ),
        )
        # Prune rows older than HISTORY_DAYS
        cutoff = epoch - HISTORY_DAYS * 86400
        con.execute("DELETE FROM readings WHERE epoch < ?", (cutoff,))


def get_history(hours: int = 1) -> list:
    """Return readings from the last `hours` hours as a list of dicts."""
    cutoff = int(datetime.now().timestamp()) - hours * 3600
    with _db() as con:
        rows = con.execute(
            "SELECT ts, epoch, temp, fan_rpm, cpu, ram, disk, clock_mhz "
            "FROM readings WHERE epoch >= ? ORDER BY epoch ASC",
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_history_csv(hours: int = 1) -> str:
    """Return readings for the last `hours` hours as a CSV string."""
    rows = get_history(hours)
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["ts", "epoch", "temp", "fan_rpm", "cpu", "ram", "disk", "clock_mhz"],
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


# ---------------------------------------------------------------------------
# Throttle / Power status
# ---------------------------------------------------------------------------
THROTTLE_BITS = {
    0x1:     ("Under-voltage",          False),
    0x2:     ("Freq Capped",             False),
    0x4:     ("Throttled",               False),
    0x10000: ("Under-voltage occurred",  True),
    0x40000: ("Throttling occurred",     True),
}


def get_throttled_status():
    try:
        out = subprocess.check_output(["vcgencmd", "get_throttled"]).decode().strip()
        status_int = int(out.split("=")[1], 16)
    except Exception:
        return {"label": "N/A", "healthy": False, "current": [], "historical": [], "available": False}
    current, historical = [], []
    for bit, (desc, is_hist) in THROTTLE_BITS.items():
        if status_int & bit:
            (historical if is_hist else current).append(desc)
    all_issues = current + historical
    label = "Healthy"
    if all_issues:
        label = ", ".join(current) if current else "History: " + ", ".join(historical)
    return {"label": label, "healthy": not bool(current), "current": current, "historical": historical, "available": True}


# ---------------------------------------------------------------------------
# Process list
# ---------------------------------------------------------------------------
def get_top_processes(n=5):
    procs = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            cpu = proc.cpu_percent(interval=0.0)
            if cpu > 0.0:
                procs.append({"name": proc.info["name"], "cpu_percent": cpu})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return procs[:n]


# ---------------------------------------------------------------------------
# Sensor helpers
# ---------------------------------------------------------------------------
_FAN_PATH_CACHE = None


def _resolve_fan_path():
    global _FAN_PATH_CACHE
    if _FAN_PATH_CACHE is not None:
        return _FAN_PATH_CACHE
    candidates = glob.glob("/sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input")
    if candidates:
        _FAN_PATH_CACHE = candidates[0]
    return _FAN_PATH_CACHE


def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000, 1), True
    except Exception:
        return 0.0, False


def get_fan_rpm():
    path = _resolve_fan_path()
    if not path:
        return 0, False
    try:
        with open(path) as f:
            return int(f.read().strip()), True
    except Exception:
        return 0, False


def get_all_thermal_zones() -> list:
    """Return a list of dicts for every thermal zone found on the system."""
    zones = []
    for path in sorted(glob.glob("/sys/class/thermal/thermal_zone*/temp")):
        zone_dir = os.path.dirname(path)
        zone_id  = os.path.basename(zone_dir).replace("thermal_zone", "")
        # Read human-readable type if available
        type_path = os.path.join(zone_dir, "type")
        try:
            zone_type = open(type_path).read().strip()
        except Exception:
            zone_type = "zone" + zone_id
        try:
            temp_raw = int(open(path).read().strip())
            temp_c   = round(temp_raw / 1000, 1)
            available = True
        except Exception:
            temp_c    = 0.0
            available = False
        zones.append({
            "id":        int(zone_id),
            "type":      zone_type,
            "temp":      temp_c,
            "available": available,
        })
    return zones


# ---------------------------------------------------------------------------
# Aggregate stats
# ---------------------------------------------------------------------------
def get_stats():
    temp, temp_available = get_cpu_temp()
    fan_rpm, fan_available = get_fan_rpm()
    cpu_usage = psutil.cpu_percent(interval=None)
    memory    = psutil.virtual_memory()
    disk      = psutil.disk_usage("/")
    cpu_freq  = psutil.cpu_freq()
    clock_mhz = round(cpu_freq.current) if cpu_freq else 0
    throttle  = get_throttled_status()

    def _level(val, warn, crit):
        if val >= crit:  return "Critical"
        if val >= warn:  return "Warning"
        return "Normal"

    stats = {
        # Thermal
        "temp":           temp,
        "temp_available": temp_available,
        "status_temp":    _level(temp, TEMP_WARN, TEMP_CRIT),
        # All thermal zones
        "thermal_zones":  get_all_thermal_zones(),
        # Fan
        "fan_rpm":        fan_rpm,
        "fan_available":  fan_available,
        "status_fan":     "Idle" if fan_rpm == 0 else "Running",
        # CPU
        "cpu_usage":      cpu_usage,
        "clock_speed":    clock_mhz,
        "status_cpu":     _level(cpu_usage, CPU_WARN, CPU_CRIT),
        # Memory
        "ram_usage":      memory.percent,
        "status_ram":     _level(memory.percent, RAM_WARN, RAM_CRIT),
        # Disk
        "disk_usage":     disk.percent,
        "disk_free":      round(disk.free  / (1024 ** 3), 1),
        "disk_total":     round(disk.total / (1024 ** 3), 1),
        "status_disk":    _level(disk.percent, DISK_WARN, DISK_CRIT),
        # Throttle
        "throttle_status":   throttle["label"],
        "throttle_healthy":  throttle["healthy"],
        "throttle_current":  throttle["current"],
        "throttle_historical": throttle["historical"],
        # Thresholds (for client-side awareness)
        "thresholds": {
            "temp_warn":  TEMP_WARN,  "temp_crit":  TEMP_CRIT,
            "cpu_warn":   CPU_WARN,   "cpu_crit":   CPU_CRIT,
            "ram_warn":   RAM_WARN,   "ram_crit":   RAM_CRIT,
            "disk_warn":  DISK_WARN,  "disk_crit":  DISK_CRIT,
        },
        # Processes
        "top_procs": get_top_processes(),
        # Meta
        "timestamp": datetime.now().astimezone().strftime("%H:%M:%S"),
    }
    _store_reading(stats)
    return stats


# Initialise DB on first import
_init_db()
