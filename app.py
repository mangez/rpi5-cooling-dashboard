from flask import Flask, render_template_string, jsonify
import glob
from datetime import datetime

app = Flask(__name__)


def get_stats():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = round(int(f.read().strip()) / 1000, 1)
    except Exception:
        temp = 0.0

    fan_rpm = 0
    fan_paths = glob.glob('/sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input')
    if fan_paths:
        try:
            with open(fan_paths[0], 'r') as f:
                fan_rpm = int(f.read().strip())
        except Exception:
            pass

    return {
        'temp': temp,
        'fan_rpm': fan_rpm,
        'timestamp': datetime.now().astimezone().strftime('%H:%M:%S %Z'),
        'status_temp': 'Normal' if temp < 70 else 'Warning' if temp < 80 else 'Critical',
        'status_fan': 'Idle' if fan_rpm == 0 else 'Running'
    }


@app.route('/')
def dashboard():
    stats = get_stats()
    return render_template_string(HTML_TEMPLATE, **stats)


@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())


HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>🐧 Raspberry Pi 5 Cooling Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #212529; line-height: 1.6; min-height: 100vh;
    }
    .container { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
    h1 {
        text-align: center; color: #2c3e50; margin-bottom: 40px;
        font-size: 2.5rem; font-weight: 300; display: flex;
        align-items: center; justify-content: center; gap: 15px;
    }
    .metrics-grid {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 30px; margin-bottom: 40px;
    }
    .metric-card {
        background: rgba(255,255,255,0.95); border-radius: 20px;
        padding: 35px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border-left: 6px solid #dee2e6; backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0,0,0,0.15); }
    .metric-critical { border-left-color: #e74c3c; }
    .metric-warning { border-left-color: #f39c12; }
    .metric-normal { border-left-color: #27ae60; }
    .metric-header {
        display: flex; align-items: center; gap: 15px; margin-bottom: 20px;
    }
    .metric-icon {
        width: 60px; height: 60px; border-radius: 15px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.8rem; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .icon-temp { background: linear-gradient(135deg, #e74c3c, #c0392b); }
    .icon-fan { background: linear-gradient(135deg, #3498db, #2980b9); }
    .metric-title { font-size: 1.3rem; color: #2c3e50; font-weight: 600; }
    .metric-value {
        font-size: 4rem; font-weight: 800; line-height: 1;
        margin-bottom: 10px; font-variant-numeric: tabular-nums;
    }
    .temp-value { color: #e74c3c; }
    .fan-value { color: #3498db; }
    .metric-label { font-size: 1.2rem; color: #7f8c8d; margin-bottom: 8px; }
    .metric-status {
        font-size: 1rem; font-weight: 600; padding: 8px 16px;
        border-radius: 25px; display: inline-flex; align-items: center; gap: 6px;
    }
    .status-normal { background: #d5f4e6; color: #27ae60; }
    .status-warning { background: #fef5d6; color: #f39c12; }
    .status-critical { background: #fadbd8; color: #e74c3c; }
    .status-idle { background: #ecf0f1; color: #95a5a6; }
    .status-running { background: #d6eaf8; color: #3498db; }
    .chart-section {
        background: rgba(255,255,255,0.95); border-radius: 20px;
        padding: 35px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    .section-header {
        display: flex; align-items: center; gap: 12px;
        margin-bottom: 25px; color: #2c3e50; font-size: 1.4rem; font-weight: 600;
    }
    table { width: 100%; border-collapse: collapse; }
    th, td {
        padding: 16px 20px; text-align: left; border-bottom: 1px solid #ecf0f1;
    }
    th {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        font-weight: 600; color: #2c3e50; text-transform: uppercase;
        letter-spacing: 0.5px; font-size: 0.85rem;
    }
    tr:hover { background: rgba(52, 152, 219, 0.05); }
    .footer-info {
        text-align: center; color: #7f8c8d; font-size: 0.95rem;
        padding: 25px; background: rgba(255,255,255,0.7);
        border-radius: 15px; backdrop-filter: blur(10px);
    }
    @media (max-width: 768px) {
        .metrics-grid { grid-template-columns: 1fr; }
        .metric-value { font-size: 3rem; }
        h1 { font-size: 2rem; flex-direction: column; gap: 10px; }
        .metric-icon { width: 50px; height: 50px; font-size: 1.5rem; }
    }
    </style>
</head>
<body>
    <div class="container">
    <h1>
        <i class="fas fa-microchip" style="font-size: 3rem; color: #e74c3c;"></i>
        Raspberry Pi 5 Cooling Dashboard
    </h1>

    <div class="metrics-grid" id="metrics">
        <div class="metric-card metric-normal">
            <div class="metric-header">
                <div class="metric-icon icon-temp">
                    <i class="fas fa-thermometer-half"></i>
                </div>
                <div>
                    <div class="metric-title">CPU Temperature</div>
                    <div class="metric-label">Current core temperature</div>
                </div>
            </div>
            <div class="metric-value temp-value" id="tempValue">--°C</div>
            <span class="metric-status status-normal" id="tempStatus">
                <i class="fas fa-circle-check"></i> Normal
            </span>
        </div>

        <div class="metric-card metric-normal">
            <div class="metric-header">
                <div class="metric-icon icon-fan">
                    <i class="fas fa-fan"></i>
                </div>
                <div>
                    <div class="metric-title">Active Cooler</div>
                    <div class="metric-label">Fan rotation speed</div>
                </div>
            </div>
            <div class="metric-value fan-value" id="fanValue">-- RPM</div>
            <span class="metric-status status-idle" id="fanStatus">
                <i class="fas fa-power-off"></i> Idle
            </span>
        </div>
    </div>
    <div class="chart-section">
        <div class="section-header">
            <i class="fas fa-chart-line"></i>
            Recent Readings (Last 10)
        </div>
        <table id="readingsTable">
            <thead>
                <tr>
                    <th><i class="fas fa-clock"></i> Time</th>
                    <th><i class="fas fa-thermometer-half"></i> Temp (°C)</th>
                    <th><i class="fas fa-fan"></i> Fan (RPM)</th>
                    <th><i class="fas fa-info-circle"></i> Status</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
    <div class="footer-info">
        <div><i class="fas fa-sync-alt"></i> Last update: <span id="lastUpdate">{{ timestamp }}</span></div>
        <div><i class="fas fa-clock"></i> Auto-refresh every 3 seconds &bull; <i class="fas fa-raspberry-pi"></i> Raspberry Pi 5 Active Cooler</div>
    </div>
    </div>
    <script>
    const readings = [];
    function updateDashboard() {
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                document.getElementById('tempValue').textContent = data.temp + '°C';
                document.getElementById('fanValue').textContent = data.fan_rpm.toLocaleString() + ' RPM';
                document.getElementById('tempStatus').innerHTML =
                    `<i class="fas fa-${data.status_temp === 'Critical' ? 'exclamation-triangle' : data.status_temp === 'Warning' ? 'exclamation-circle' : 'circle-check'}"></i> ${data.status_temp}`;
                document.getElementById('fanStatus').innerHTML =
                    `<i class="fas fa-${data.status_fan === 'Idle' ? 'power-off' : 'play-circle'}"></i> ${data.status_fan}`;
                document.getElementById('lastUpdate').textContent = data.timestamp;

                const tempCard = document.querySelector('.metric-card:nth-child(1)');
                const fanCard = document.querySelector('.metric-card:nth-child(2)');
                tempCard.className = 'metric-card ' + (data.temp > 80 ? 'metric-critical' : data.temp > 70 ? 'metric-warning' : 'metric-normal');
                fanCard.className = 'metric-card ' + (data.fan_rpm > 5500 ? 'metric-critical' : data.fan_rpm > 4500 ? 'metric-warning' : 'metric-normal');

                document.getElementById('tempStatus').className = 'metric-status status-' +
                    (data.temp > 80 ? 'critical' : data.temp > 70 ? 'warning' : 'normal');
                document.getElementById('fanStatus').className = 'metric-status status-' +
                    (data.status_fan === 'Idle' ? 'idle' : 'running');

                readings.unshift({time: data.timestamp, temp: data.temp, fan: data.fan_rpm, status: data.status_temp});
                if (readings.length > 10) readings.pop();

                const tbody = document.querySelector('#readingsTable tbody');
                tbody.innerHTML = readings.map(r =>
                    `<tr>
                        <td><i class="fas fa-clock text-xs"></i> ${r.time}</td>
                        <td><i class="fas fa-thermometer-${r.temp > 70 ? 'three-quarters' : 'half'} text-xs"></i> ${r.temp}</td>
                        <td><i class="fas fa-tachometer-alt text-xs"></i> ${r.fan.toLocaleString()}</td>
                        <td>${r.status}</td>
                    </tr>`
                ).join('');
            });
    }

    updateDashboard();
    setInterval(updateDashboard, 3000);
    </script>
</body>
</html>'''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
