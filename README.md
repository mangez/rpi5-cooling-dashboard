# 🐧 Raspberry Pi 5 Cooling Dashboard

A lightweight Flask web dashboard for real-time monitoring of your **Raspberry Pi 5** CPU temperature, Active Cooler fan RPM, and core system metrics — with **persistent SQLite history**, configurable thresholds, and a modern dark UI.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-green?logo=flask)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%205-red?logo=raspberry-pi)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

---

## Features

- **Live CPU Temperature** – Reads directly from `/sys/class/thermal/thermal_zone0/temp`
- **Fan RPM Monitoring** – Reads from the hwmon sysfs interface for the official Active Cooler
- **Advanced System Metrics** – Real-time CPU clock speed (MHz), Disk usage (%), and Storage health (Free/Total GB)
- **Top Processes Viewer** – Auto-refreshing table showing the top 5 CPU-intensive processes
- **Historical Performance Chart** – Chart.js line graph with time-range tabs (1 h / 6 h / 24 h)
- **Persistent SQLite History** – Readings stored in `/tmp/rpi_dashboard.db`; auto-pruned after 7 days (configurable)
- **Configurable Thresholds** – Warn/Critical levels for Temp, CPU, RAM, and Disk via environment variables
- **Alert Banner** – On-screen warning when any metric exceeds its Critical threshold
- **Color-coded Status** – Normal / Warning / Critical with dynamic card colors
- **Throttle Status** – Reads `vcgencmd get_throttled` for under-voltage / frequency-cap detection
- **Health Endpoint** – `/health` returns `{"status": "ok"}` for uptime monitoring
- **Auto-refresh** – Polls `/api/stats` every 3 seconds; history chart refreshes every 60 seconds
- **Responsive UI** – Modern dark design system, works on desktop and mobile browsers
- **REST API** – `/api/stats` and `/api/history` endpoints for integration with other tools

---

## Threshold Defaults

All thresholds are overridable via environment variables (see [Configuration](#configuration)).

| Metric | Warn | Critical |
|--------|------|----------|
| Temperature | ≥ 70°C | ≥ 80°C |
| CPU Usage | ≥ 70% | ≥ 85% |
| RAM Usage | ≥ 70% | ≥ 85% |
| Disk Usage | ≥ 80% | ≥ 90% |

---

## Requirements

- Raspberry Pi 5 (with official Active Cooler recommended)
- Python 3.8+
- Flask ≥ 2.0, psutil

Install dependencies:
```bash
pip install -r requirements.txt
# or manually:
pip install flask psutil
```

---

## Usage

```bash
python app.py
```

Then open your browser and navigate to: `http://<your-pi-ip>:8080`

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | HTTP port |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode |
| `HISTORY_DB_PATH` | `/tmp/rpi_dashboard.db` | SQLite database path |
| `HISTORY_DAYS` | `7` | Days of history to retain |
| `TEMP_WARN` | `70` | Temperature warning threshold (°C) |
| `TEMP_CRIT` | `80` | Temperature critical threshold (°C) |
| `CPU_WARN` | `70` | CPU usage warning threshold (%) |
| `CPU_CRIT` | `85` | CPU usage critical threshold (%) |
| `RAM_WARN` | `70` | RAM usage warning threshold (%) |
| `RAM_CRIT` | `85` | RAM usage critical threshold (%) |
| `DISK_WARN` | `80` | Disk usage warning threshold (%) |
| `DISK_CRIT` | `90` | Disk usage critical threshold (%) |

### Run as a systemd service (optional)

Create `/etc/systemd/system/cooling-dashboard.service`:
```ini
[Unit]
Description=RPi5 Cooling Dashboard
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/rpi5-cooling-dashboard/app.py
WorkingDirectory=/home/pi/rpi5-cooling-dashboard
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable cooling-dashboard
sudo systemctl start cooling-dashboard
```

---

## API

### `GET /api/stats`

Returns the current snapshot of all sensor readings:

```json
{
  "temp": 52.3,
  "temp_available": true,
  "status_temp": "Normal",
  "fan_rpm": 2400,
  "fan_available": true,
  "status_fan": "Running",
  "cpu_usage": 12.5,
  "clock_speed": 1500,
  "status_cpu": "Normal",
  "ram_usage": 45.2,
  "status_ram": "Normal",
  "disk_usage": 32.1,
  "disk_free": 15.2,
  "disk_total": 58.4,
  "status_disk": "Normal",
  "throttle_status": "Healthy",
  "throttle_healthy": true,
  "throttle_current": [],
  "throttle_historical": [],
  "thresholds": {
    "temp_warn": 70, "temp_crit": 80,
    "cpu_warn": 70,  "cpu_crit": 85,
    "ram_warn": 70,  "ram_crit": 85,
    "disk_warn": 80, "disk_crit": 90
  },
  "top_procs": [{"name": "python3", "cpu_percent": 8.5}],
  "timestamp": "20:00:00"
}
```

### `GET /api/history?hours=1`

Returns persisted readings for the last N hours (default: 1, max: 168):

```json
[
  {
    "ts": "20:00:00",
    "epoch": 1743861600,
    "temp": 52.3,
    "fan_rpm": 2400,
    "cpu": 12.5,
    "ram": 45.2,
    "disk": 32.1,
    "clock_mhz": 1500
  }
]
```

### `GET /health`

Simple liveness probe:

```json
{"status": "ok"}
```

---

## Project Structure

```text
rpi5-cooling-dashboard/
├── app.py                  # Flask app: routes /, /api/stats, /api/history, /health
├── services/
│   └── metrics.py          # Sensor reads, SQLite persistence, threshold logic
├── static/
│   ├── css/
│   │   └── style.css       # Dark design system with CSS custom properties
│   └── js/
│       └── dashboard.js    # Chart.js init, polling, history tabs, alert banner
├── templates/
│   └── dashboard.html      # Jinja2 template: topbar, metric cards, time-range tabs
├── Dockerfile              # Docker support
├── requirements.txt        # Python dependencies (flask>=2.0)
├── .gitignore
├── CONTRIBUTING.md
├── .github/
│   └── PULL_REQUEST_TEMPLATE.md
└── README.md               # This file
```

---

## Docker

A `Dockerfile` is included. To build and run:

```bash
docker build -t rpi5-cooling-dashboard .
docker run -d --privileged -p 8080:8080 rpi5-cooling-dashboard
```

> **Note:** `--privileged` is required to access hardware sysfs paths for temperature and fan RPM.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide and feature ideas.

## License

MIT
