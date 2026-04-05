import glob
import subprocess
from datetime import datetime

import psutil

# ---------------------------------------------------------------------------
# Throttle / Power status
# ---------------------------------------------------------------------------

THROTTLE_BITS = {
    0x1: ("Under-voltage", False),
    0x2: ("Freq Capped", False),
    0x4: ("Throttled", False),
    0x10000: ("Under-voltage occurred", True),
    0x40000: ("Throttling occurred", True),
}


def get_throttled_status():
    """Return a structured dict describing current and historical throttle state."""
    try:
        out = subprocess.check_output(["vcgencmd", "get_throttled"]).decode().strip()
        status_hex = out.split("=")[1]
        status_int = int(status_hex, 16)
    except Exception:
        return {
            "label": "N/A",
            "healthy": False,
            "current": [],
            "historical": [],
            "available": False,
        }

    current = []
    historical = []
    for bit, (desc, is_historical) in THROTTLE_BITS.items():
        if status_int & bit:
            if is_historical:
                historical.append(desc)
            else:
                current.append(desc)

    all_issues = current + historical
    return {
        "label": "Healthy" if not all_issues else ", ".join(current) if current else "History: " + ", ".join(historical),
        "healthy": not bool(current),
        "current": current,
        "historical": historical,
        "available": True,
    }


# ---------------------------------------------------------------------------
# Process list
# ---------------------------------------------------------------------------

_PROC_INTERVAL_CACHE = {}


def get_top_processes(n=5):
    """Return top-N processes by CPU percent, primed over a 0.1 s interval."""
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
    """Read CPU temperature. Returns (value_float, available_bool)."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return round(int(f.read().strip()) / 1000, 1), True
    except Exception:
        return 0.0, False


def get_fan_rpm():
    """Read fan RPM from hwmon sysfs. Returns (value_int, available_bool)."""
    path = _resolve_fan_path()
    if not path:
        return 0, False
    try:
        with open(path, "r") as f:
            return int(f.read().strip()), True
    except Exception:
        return 0, False


# ---------------------------------------------------------------------------
# Aggregate stats
# ---------------------------------------------------------------------------


def get_stats():
    """Collect all metrics and return a flat dict for the API and template."""
    temp, temp_available = get_cpu_temp()
    fan_rpm, fan_available = get_fan_rpm()

    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_freq = psutil.cpu_freq()
    clock_mhz = round(cpu_freq.current) if cpu_freq else 0

    throttle = get_throttled_status()

    if temp >= 80:
        status_temp = "Critical"
    elif temp >= 70:
        status_temp = "Warning"
    else:
        status_temp = "Normal"

    return {
        # Thermal
        "temp": temp,
        "temp_available": temp_available,
        "status_temp": status_temp,
        # Fan
        "fan_rpm": fan_rpm,
        "fan_available": fan_available,
        "status_fan": "Idle" if fan_rpm == 0 else "Running",
        # CPU
        "cpu_usage": cpu_usage,
        "clock_speed": clock_mhz,
        # Memory
        "ram_usage": memory.percent,
        # Disk
        "disk_usage": disk.percent,
        "disk_free": round(disk.free / (1024 ** 3), 1),
        "disk_total": round(disk.total / (1024 ** 3), 1),
        # Throttle (structured)
        "throttle_status": throttle["label"],
        "throttle_healthy": throttle["healthy"],
        "throttle_current": throttle["current"],
        "throttle_historical": throttle["historical"],
        # Processes
        "top_procs": get_top_processes(),
        # Meta
        "timestamp": datetime.now().astimezone().strftime("%H:%M:%S"),
    }
