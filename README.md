# 🐧 Raspberry Pi 5 Cooling Dashboard

A lightweight Flask web dashboard for real-time monitoring of your **Raspberry Pi 5** CPU temperature, Active Cooler fan RPM, and core system metrics.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-green?logo=flask)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%205-red?logo=raspberry-pi)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

---

## Features

- **Live CPU Temperature** – Reads directly from `/sys/class/thermal/thermal_zone0/temp`
- **Fan RPM Monitoring** – Reads from the hwmon sysfs interface for the official Active Cooler
- **Advanced System Metrics (v1.2.0)** – Real-time CPU clock speed (MHz), Disk usage (%), and Storage health (Free/Total GB)
- **Top Processes Viewer (v1.2.0)** – Auto-refreshing table showing the top 5 CPU-intensive processes
- **Historical Performance Chart (v1.2.0)** – Integrated Chart.js line graph for tracking Temp, CPU, and RAM trends
- **Color-coded Status** – Normal / Warning / Critical thresholds with dynamic card colors
- **Last 10 Readings Table** – Rolling history table updated in real-time
- **Auto-refresh** – Polls `/api/stats` every 3 seconds via JavaScript fetch
- **Responsive UI** – Works on desktop and mobile browsers
- **REST API** – `/api/stats` endpoint returns JSON for integration with other tools

---

## Temperature Thresholds

| Status | Temp Range | Card Color |
|----------|-------------|------------|
| Normal | < 70°C | Green |
| Warning | 70°C – 80°C | Orange |
| Critical | > 80°C | Red |

---

## Requirements

- Raspberry Pi 5 (with official Active Cooler recommended)
- Python 3.8+
- Flask, psutil

Install dependencies:
```bash
pip install flask psutil
```

## Usage

```bash
python app.py
```

Then open your browser and navigate to:
`http://<your-pi-ip>:8080`

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
Returns current sensor readings as JSON:
```json
{
  "temp": 52.3,
  "fan_rpm": 2400,
  "cpu_usage": 12.5,
  "ram_usage": 45.2,
  "disk_usage": 32.1,
  "disk_free": 15.2,
  "disk_total": 58.4,
  "clock_speed": 1500,
  "throttle_status": "Healthy",
  "top_procs": [
    {"name": "python3", "cpu_percent": 8.5}
  ],
  "timestamp": "20:00:00 IST",
  "status_temp": "Normal",
  "status_fan": "Running"
}
```

---

## Project Structure
```text
rpi5-cooling-dashboard/
├── app.py              # Main Flask application with embedded HTML template
├── .gitignore          # Python gitignore
├── CONTRIBUTING.md     # How to contribute
├── .github/
│   └── PULL_REQUEST_TEMPLATE.md # PR form template
└── README.md           # This file
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide and feature ideas.

## License
MIT
