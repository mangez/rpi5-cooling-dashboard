from flask import Flask, render_template_string, jsonify
import glob
from datetime import datetime
import psutil

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

    # New Metrics
    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    ram_usage = memory.percent

    return {
        'temp': temp,
        'fan_rpm': fan_rpm,
        'cpu_usage': cpu_usage,
        'ram_usage': ram_usage,
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
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
        display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px; margin-bottom: 30px;
    }
    .metric-card {
        background: rgba(255,255,255,0.95); border-radius: 20px;
        padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border-left: 6px solid #dee2e6; backdrop-filter: blur(10px);
        transition: transform 0.2s ease;
    }
    .metric-card:hover { transform: translateY(-3px); }
    .metric-critical { border-left-color: #e74c3c; }
    .metric-warning { border-left-color: #f39c12; }
    .metric-normal { border-left-color: #27ae60; }
    .metric-header { display: flex; align-items: center; gap: 12px; margin-bottom: 15px; }
    .metric-icon {
        width: 45px; height: 45px; border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.4rem; color: white;
    }
    .icon-temp { background: linear-gradient(135deg, #e74c3c, #c0392b); }
    .icon-fan { background: linear-gradient(135deg, #3498db, #2980b9); }
    .icon-cpu { background: linear-gradient(135deg, #9b59b6, #8e44ad); }
    .icon-ram { background: linear-gradient(135deg, #f1c40f, #f39c12); }
    .metric-title { font-size: 1.1rem; color: #2c3e50; font-weight: 600; }
    .metric-value {
        font-size: 2.5rem; font-weight: 800; line-height: 1.2;
        margin-bottom: 5px; font-variant-numeric: tabular-nums;
    }
    .temp-value { color: #e74c3c; }
    .fan-value { color: #3498db; }
    .cpu-value { color: #9b59b6; }
    .ram-value { color: #f39c12; }
    .metric-status {
        font-size: 0.85rem; font-weight: 600; padding: 4px 12px;
        border-radius: 20px; display: inline-flex; align-items: center; gap: 5px;
    }
    .status-normal { background: #d5f4e6; color: #27ae60; }
    .status-warning { background: #fef5d6; color: #f39c12; }
    .status-critical { background: #fadbd8; color: #e74c3c; }
    .chart-container {
        background: rgba(255,255,255,0.95); border-radius: 20px;
        padding: 25px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }
    .chart-header { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; font-weight: 600; color: #2c3e50; }
    .readings-section {
        background: rgba(255,255,255,0.95); border-radius: 20px;
        padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ecf0f1; font-size: 0.9rem; }
    th { background: #f8f9fa; font-weight: 600; color: #7f8c8d; text-transform: uppercase; font-size: 0.75rem; }
    .footer-info { text-align: center; color: #7f8c8d; font-size: 0.85rem; margin-top: 30px; padding-bottom: 30px; }
    </style>
</head>
<body>
    <div class="container">
        <h1><i class="fas fa-microchip"></i> Raspberry Pi 5 Cooling Dashboard</h1>

        <div class="metrics-grid">
            <!-- CPU Temp -->
            <div class="metric-card metric-normal" id="tempCard">
                <div class="metric-header">
                    <div class="metric-icon icon-temp"><i class="fas fa-thermometer-half"></i></div>
                    <div class="metric-title">CPU Temp</div>
                </div>
                <div class="metric-value temp-value" id="tempValue">--°C</div>
                <span class="metric-status status-normal" id="tempStatus">Normal</span>
            </div>

            <!-- Fan RPM -->
            <div class="metric-card metric-normal" id="fanCard">
                <div class="metric-header">
                    <div class="metric-icon icon-fan"><i class="fas fa-fan"></i></div>
                    <div class="metric-title">Fan Speed</div>
                </div>
                <div class="metric-value fan-value" id="fanValue">-- RPM</div>
                <span class="metric-status status-normal" id="fanStatus">Running</span>
            </div>

            <!-- CPU Usage -->
            <div class="metric-card metric-normal" id="cpuCard">
                <div class="metric-header">
                    <div class="metric-icon icon-cpu"><i class="fas fa-processor"></i></div>
                    <div class="metric-title">CPU Load</div>
                </div>
                <div class="metric-value cpu-value" id="cpuValue">--%</div>
                <span class="metric-status status-normal" id="cpuStatus">Normal</span>
            </div>

            <!-- RAM Usage -->
            <div class="metric-card metric-normal" id="ramCard">
                <div class="metric-header">
                    <div class="metric-icon icon-ram"><i class="fas fa-memory"></i></div>
                    <div class="metric-title">RAM Usage</div>
                </div>
                <div class="metric-value ram-value" id="ramValue">--%</div>
                <span class="metric-status status-normal" id="ramStatus">Normal</span>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-header"><i class="fas fa-chart-line"></i> Performance History (Last 30 mins)</div>
            <canvas id="historyChart" height="100"></canvas>
        </div>

        <div class="readings-section">
            <div class="chart-header"><i class="fas fa-list"></i> Recent Raw Readings</div>
            <table id="readingsTable">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Temp</th>
                        <th>Fan</th>
                        <th>CPU %</th>
                        <th>RAM %</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>

        <div class="footer-info">
            Auto-refreshing every 3s • Last update: <span id="lastUpdate">{{ timestamp }}</span>
        </div>
    </div>

    <script>
    let chart;
    const history = { labels: [], temp: [], fan: [], cpu: [], ram: [] };

    function initChart() {
        const ctx = document.getElementById('historyChart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: history.labels,
                datasets: [
                    { label: 'Temp (°C)', data: history.temp, borderColor: '#e74c3c', tension: 0.3, yAxisID: 'y' },
                    { label: 'CPU %', data: history.cpu, borderColor: '#9b59b6', tension: 0.3, yAxisID: 'y' },
                    { label: 'RAM %', data: history.ram, borderColor: '#f1c40f', tension: 0.3, yAxisID: 'y' },
                    { label: 'Fan RPM', data: history.fan, borderColor: '#3498db', tension: 0.3, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { type: 'linear', position: 'left', min: 0, max: 100 },
                    y1: { type: 'linear', position: 'right', min: 0, grid: { drawOnChartArea: false } }
                },
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    function updateDashboard() {
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                // Update Values
                document.getElementById('tempValue').textContent = data.temp + '°C';
                document.getElementById('fanValue').textContent = data.fan_rpm.toLocaleString() + ' RPM';
                document.getElementById('cpuValue').textContent = data.cpu_usage + '%';
                document.getElementById('ramValue').textContent = data.ram_usage + '%';
                document.getElementById('lastUpdate').textContent = data.timestamp;

                // Update Card Status Styles
                const setStatus = (id, val, w, c) => {
                    const card = document.getElementById(id + 'Card');
                    const status = document.getElementById(id + 'Status');
                    const s = val > c ? 'critical' : val > w ? 'warning' : 'normal';
                    card.className = `metric-card metric-${s}`;
                    status.className = `metric-status status-${s}`;
                    status.textContent = s.charAt(0).toUpperCase() + s.slice(1);
                };

                setStatus('temp', data.temp, 70, 80);
                setStatus('cpu', data.cpu_usage, 80, 95);
                setStatus('ram', data.ram_usage, 80, 95);
                
                const fanCard = document.getElementById('fanCard');
                const fanStatus = document.getElementById('fanStatus');
                const fs = data.fan_rpm > 5500 ? 'critical' : data.fan_rpm > 4500 ? 'warning' : 'normal';
                fanCard.className = `metric-card metric-${fs}`;
                fanStatus.className = `metric-status status-${data.fan_rpm > 0 ? (fs === 'normal' ? 'normal' : fs) : 'normal'}`;
                fanStatus.textContent = data.fan_rpm > 0 ? 'Running' : 'Idle';

                // Update Chart
                if (history.labels.length > 20) {
                    history.labels.shift(); history.temp.shift(); history.fan.shift(); history.cpu.shift(); history.ram.shift();
                }
                history.labels.push(data.timestamp);
                history.temp.push(data.temp);
                history.fan.push(data.fan_rpm);
                history.cpu.push(data.cpu_usage);
                history.ram.push(data.ram_usage);
                chart.update();

                // Update Table
                const tbody = document.querySelector('#readingsTable tbody');
                const row = `<tr><td>${data.timestamp}</td><td>${data.temp}</td><td>${data.fan_rpm}</td><td>${data.cpu_usage}</td><td>${data.ram_usage}</td></tr>`;
                tbody.insertAdjacentHTML('afterbegin', row);
                if (tbody.children.length > 10) tbody.lastElementChild.remove();
            });
    }

    initChart();
    updateDashboard();
    setInterval(updateDashboard, 3000);
    </script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
