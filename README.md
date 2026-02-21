# 🐧 Raspberry Pi 5 Cooling Dashboard

A lightweight Flask web dashboard for real-time monitoring of your **Raspberry Pi 5** CPU temperature and Active Cooler fan RPM.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-green?logo=flask)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%205-red?logo=raspberry-pi)

---

## Features

- **Live CPU Temperature** – Reads directly from `/sys/class/thermal/thermal_zone0/temp`
- **Fan RPM Monitoring** – Reads from the hwmon sysfs interface for the official Active Cooler
- **Color-coded Status** – Normal / Warning / Critical thresholds with dynamic card colors
- **Last 10 Readings Table** – Rolling history table updated in real-time
- **Auto-refresh** – Polls `/api/stats` every 3 seconds via JavaScript fetch
- **Responsive UI** – Works on desktop and mobile browsers
- **REST API** – `/api/stats` endpoint returns JSON for integration with other tools

---

## Temperature Thresholds

| Status   | Temp Range  | Card Color |
|----------|-------------|------------|
| Normal   | < 70°C      | Green      |
| Warning  | 70°C – 80°C | Orange     |
| Critical | > 80°C      | Red        |

---

## Requirements

- Raspberry Pi 5 (with official Active Cooler recommended)
- Python 3.8+
- Flask

Install dependencies:

```bash
pip install flask
```

---

## Usage

```bash
python app.py
```

Then open your browser and navigate to:

```
http://<raspberry-pi-ip>:8080
```

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
  "timestamp": "20:00:00 IST",
  "status_temp": "Normal",
  "status_fan": "Running"
}
```

---

## Project Structure

```
rpi5-cooling-dashboard/
├── app.py          # Main Flask application with embedded HTML template
├── .gitignore      # Python gitignore
└── README.md       # This file
```

---

## License

MIT
