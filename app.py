from flask import Flask, render_template_string, jsonify
import glob
from datetime import datetime
import psutil
import subprocess

app = Flask(__name__)


def get_throttled_status():
    try:
        # vcgencmd returns 'throttled=0x0'
        out = subprocess.check_output(['vcgencmd', 'get_throttled']).decode().strip()
        status_hex = out.split('=')[1]
        status_int = int(status_hex, 16)
        if status_int == 0:
            return "Healthy"
        
        # Bits: 0: under-voltage, 1: arm freq capped, 2: currently throttled
        # 16: under-voltage occurred, 18: throttling occurred, etc.
        reasons = []
        if status_int & 0x1: reasons.append("Under-voltage")
        if status_int & 0x2: reasons.append("Freq Capped")
        if status_int & 0x4: reasons.append("Throttled")
        if not reasons and status_int > 0: reasons.append("History: Warning")
        
        return ", ".join(reasons) if reasons else "Healthy"
    except Exception:
        return "N/A"


def get_top_processes():
    processes = []
    for proc in psutil.process_iter(['name', 'cpu_percent']):
        try:
            if proc.info['cpu_percent'] > 0.1:
                processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    # Sort and take top 5
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return processes[:5]


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

    # Core Metrics
    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    ram_usage = memory.percent

    # v1.2.0 Advanced Metrics
    disk = psutil.disk_usage('/')
    cpu_freq = psutil.cpu_freq()
    clock_mhz = round(cpu_freq.current) if cpu_freq else 0
    
    return {
        'temp': temp,
        'fan_rpm': fan_rpm,
        'cpu_usage': cpu_usage,
        'ram_usage': ram_usage,
        'disk_usage': disk.percent,
        'disk_free': round(disk.free / (1024**3), 1),
        'disk_total': round(disk.total / (1024**3), 1),
        'clock_speed': clock_mhz,
        'throttle_status': get_throttled_status(),
        'top_procs': get_top_processes(),
        'timestamp': datetime.now().astimezone().strftime('%H:%M:%S'),
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
            color: #212529;
            line-height: 1.6;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px 40px;
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
            font-size: 2.3rem;
            font-weight: 400;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }
        h1 i {
            color: #3498db;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }
        .metric-card {
            background: #ffffff;
            border-radius: 18px;
            padding: 20px 20px 18px;
            box-shadow: 0 10px 26px rgba(0,0,0,0.04);
            border-left: 5px solid #dee2e6;
            backdrop-filter: blur(8px);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 35px rgba(0,0,0,0.06);
        }
        .metric-critical { border-left-color: #e74c3c; }
        .metric-warning  { border-left-color: #f39c12; }
        .metric-normal   { border-left-color: #27ae60; }

        .metric-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 6px;
        }
        .metric-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            color: #ffffff;
        }
        .icon-temp { background: linear-gradient(135deg, #e74c3c, #c0392b); }
        .icon-fan  { background: linear-gradient(135deg, #3498db, #2980b9); }
        .icon-cpu  { background: linear-gradient(135deg, #9b59b6, #8e44ad); }
        .icon-ram  { background: linear-gradient(135deg, #f1c40f, #f39c12); }
        .icon-disk { background: linear-gradient(135deg, #2ecc71, #27ae60); }

        .metric-title {
            font-size: 1.05rem;
            color: #2c3e50;
            font-weight: 600;
        }
        .metric-subtitle {
            font-size: 0.8rem;
            color: #95a5a6;
            margin-top: 2px;
        }

        .metric-main {
            margin-top: 8px;
        }

        .metric-value {
            font-size: 2.3rem;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 3px;
            font-variant-numeric: tabular-nums;
            font-family: "SF Mono", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }
        .metric-value-small {
            font-size: 0.9rem;
            color: #7f8c8d;
            font-weight: 500;
        }

        .metric-status {
            font-size: 0.78rem;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            margin-top: 6px;
        }
        .status-normal {
            background: #d5f4e6;
            color: #27ae60;
        }
        .status-warning {
            background: #fef5d6;
            color: #f39c12;
        }
        .status-critical {
            background: #fadbd8;
            color: #e74c3c;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #ecf0f1;
            border-radius: 4px;
            margin-top: 10px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            width: 0%;
            transition: width 0.4s ease-out, background-color 0.25s ease-out;
        }

        .layout-main {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }

        .chart-container,
        .readings-section,
        .procs-section {
            background: #ffffff;
            border-radius: 18px;
            padding: 20px 20px 18px;
            box-shadow: 0 10px 26px rgba(0,0,0,0.04);
        }

        .chart-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 14px;
            font-weight: 600;
            color: #2c3e50;
            font-size: 0.95rem;
        }
        .chart-header i {
            color: #3498db;
        }

        .chart-wrapper {
            position: relative;
            width: 100%;
            height: 230px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            font-size: 0.9rem;
        }
        th, td {
            padding: 9px 10px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #7f8c8d;
            text-transform: uppercase;
            font-size: 0.75rem;
        }
        tbody tr:nth-child(even) {
            background-color: #fafafa;
        }
        td.numeric {
            text-align: right;
            font-variant-numeric: tabular-nums;
        }

        .footer-info {
            text-align: center;
            color: #7f8c8d;
            font-size: 0.84rem;
            margin-top: 18px;
        }
        .live-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .live-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background-color: #2ecc71;
            box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.5);
            transition: background-color 0.2s ease, box-shadow 0.2s ease;
        }
        .live-dot.stale {
            background-color: #e74c3c;
            box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.4);
        }

        @media (max-width: 900px) {
            .layout-main {
                grid-template-columns: 1fr;
            }
            .chart-wrapper {
                height: 210px;
            }
        }
        @media (max-width: 600px) {
            h1 {
                font-size: 1.8rem;
            }
            .metric-card {
                padding: 16px 16px 14px;
            }
            .metric-value {
                font-size: 1.9rem;
            }
            .chart-wrapper {
                height: 190px;
            }
            th, td {
                padding: 8px 8px;
            }
        }
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
                    <div>
                        <div class="metric-title">CPU Temperature</div>
                        <div class="metric-subtitle">Live core temp & throttling</div>
                    </div>
                </div>
                <div class="metric-main">
                    <div class="metric-value" style="color:#e74c3c" id="tempValue">--°C</div>
                    <div class="metric-value-small" id="clockValue">Clock: -- MHz</div>
                    <span class="metric-status status-normal" id="throttleStatus">{{ throttle_status }}</span>
                </div>
            </div>

            <!-- CPU Usage -->
            <div class="metric-card metric-normal" id="cpuCard">
                <div class="metric-header">
                    <div class="metric-icon icon-cpu"><i class="fas fa-gauge-high"></i></div>
                    <div>
                        <div class="metric-title">CPU Load</div>
                        <div class="metric-subtitle">Overall processor utilization</div>
                    </div>
                </div>
                <div class="metric-main">
                    <div class="metric-value" style="color:#9b59b6" id="cpuValue">--%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="cpuFill" style="background:#9b59b6"></div>
                    </div>
                </div>
            </div>

            <!-- RAM Usage -->
            <div class="metric-card metric-normal" id="ramCard">
                <div class="metric-header">
                    <div class="metric-icon icon-ram"><i class="fas fa-memory"></i></div>
                    <div>
                        <div class="metric-title">RAM Usage</div>
                        <div class="metric-subtitle">System memory consumption</div>
                    </div>
                </div>
                <div class="metric-main">
                    <div class="metric-value" style="color:#f39c12" id="ramValue">--%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="ramFill" style="background:#f39c12"></div>
                    </div>
                </div>
            </div>

            <!-- Disk Usage -->
            <div class="metric-card metric-normal" id="diskCard">
                <div class="metric-header">
                    <div class="metric-icon icon-disk"><i class="fas fa-hdd"></i></div>
                    <div>
                        <div class="metric-title">Storage Pulse</div>
                        <div class="metric-subtitle">Root filesystem usage</div>
                    </div>
                </div>
                <div class="metric-main">
                    <div class="metric-value" style="color:#27ae60" id="diskValue">--%</div>
                    <div class="metric-value-small" id="diskFree">Free: -- GB / -- GB</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="diskFill" style="background:#27ae60"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="layout-main">
            <div class="chart-container">
                <div class="chart-header"><i class="fas fa-chart-line"></i> Performance History</div>
                <div class="chart-wrapper">
                    <canvas id="historyChart"></canvas>
                </div>
            </div>
            
            <div class="procs-section">
                <div class="chart-header"><i class="fas fa-bolt"></i> Top Processes</div>
                <table id="procTable">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th style="text-align:right">CPU %</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>

        <div class="readings-section">
            <div class="chart-header"><i class="fas fa-list"></i> Recent Raw Readings</div>
            <table id="readingsTable">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Temp (°C)</th>
                        <th>Fan RPM</th>
                        <th>CPU Load</th>
                        <th>RAM Usage</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>

        <div class="footer-info">
            <span class="live-indicator">
                <span class="live-dot" id="liveDot"></span>
                <span>Auto-refreshing every 3s</span>
            </span>
            &nbsp;•&nbsp; Last update: <span id="lastUpdate">{{ timestamp }}</span>
        </div>
    </div>

    <script>
        let chart;
        const history = { labels: [], temp: [], fan: [], cpu: [], ram: [] };
        let lastUpdateTimestamp = Date.now();

        function initChart() {
            const ctx = document.getElementById('historyChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: history.labels,
                    datasets: [
                        {
                            label: 'Temp (°C)',
                            data: history.temp,
                            borderColor: '#e74c3c',
                            tension: 0.3,
                            borderWidth: 2.2,
                            pointRadius: 0
                        },
                        {
                            label: 'CPU %',
                            data: history.cpu,
                            borderColor: '#9b59b6',
                            tension: 0.3,
                            borderWidth: 1.7,
                            pointRadius: 0
                        },
                        {
                            label: 'RAM %',
                            data: history.ram,
                            borderColor: '#f1c40f',
                            tension: 0.3,
                            borderWidth: 1.7,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            position: 'left',
                            min: 0,
                            max: 100,
                            ticks: { stepSize: 20 }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { usePointStyle: true, boxWidth: 8, font: { size: 10 } }
                        }
                    }
                }
            });
        }

        function updateLiveIndicator() {
            const dot = document.getElementById('liveDot');
            const age = Date.now() - lastUpdateTimestamp;
            if (age > 15000) {
                dot.classList.add('stale');
            } else {
                dot.classList.remove('stale');
            }
        }

        function updateDashboard() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    lastUpdateTimestamp = Date.now();

                    document.getElementById('tempValue').textContent = data.temp + '°C';
                    document.getElementById('clockValue').textContent = 'Clock: ' + data.clock_speed + ' MHz';
                    document.getElementById('cpuValue').textContent = data.cpu_usage + '%';
                    document.getElementById('ramValue').textContent = data.ram_usage + '%';
                    document.getElementById('diskValue').textContent = data.disk_usage + '%';
                    document.getElementById('diskFree').textContent =
                        `Free: ${data.disk_free} GB / ${data.disk_total} GB`;
                    document.getElementById('lastUpdate').textContent = data.timestamp;

                    // Progress Bars + critical color hints
                    const cpuFill = document.getElementById('cpuFill');
                    const ramFill = document.getElementById('ramFill');
                    const diskFill = document.getElementById('diskFill');

                    cpuFill.style.width = data.cpu_usage + '%';
                    ramFill.style.width = data.ram_usage + '%';
                    diskFill.style.width = data.disk_usage + '%';

                    cpuFill.style.backgroundColor = data.cpu_usage > 85 ? '#e74c3c' : '#9b59b6';
                    ramFill.style.backgroundColor = data.ram_usage > 85 ? '#e74c3c' : '#f39c12';
                    diskFill.style.backgroundColor = data.disk_usage > 90 ? '#e74c3c' : '#27ae60';

                    // Throttle Badge + temp card class
                    const tb = document.getElementById('throttleStatus');
                    tb.textContent = data.throttle_status;
                    tb.className = 'metric-status ' +
                        (data.throttle_status === 'Healthy' ? 'status-normal' : 'status-critical');

                    const tempCard = document.getElementById('tempCard');
                    tempCard.className = 'metric-card ' +
                        (data.status_temp || 'Normal').toLowerCase().replace('critical', 'metric-critical')
                                                        .replace('warning', 'metric-warning')
                                                        .replace('normal', 'metric-normal');

                    // CPU/RAM card states (simple hint)
                    const cpuCard = document.getElementById('cpuCard');
                    const ramCard = document.getElementById('ramCard');
                    const diskCard = document.getElementById('diskCard');

                    cpuCard.className = 'metric-card ' + (data.cpu_usage > 85 ? 'metric-warning' : 'metric-normal');
                    ramCard.className = 'metric-card ' + (data.ram_usage > 85 ? 'metric-warning' : 'metric-normal');
                    diskCard.className = 'metric-card ' + (data.disk_usage > 90 ? 'metric-warning' : 'metric-normal');

                    // Top Processes
                    const pt = document.querySelector('#procTable tbody');
                    pt.innerHTML = data.top_procs.map(p =>
                        `<tr><td>${p.name}</td><td class="numeric" style="font-weight:bold">${p.cpu_percent}%</td></tr>`
                    ).join('');

                    // History Update
                    if (history.labels.length > 20) {
                        history.labels.shift();
                        history.temp.shift();
                        history.cpu.shift();
                        history.ram.shift();
                    }
                    history.labels.push(data.timestamp);
                    history.temp.push(data.temp);
                    history.cpu.push(data.cpu_usage);
                    history.ram.push(data.ram_usage);
                    chart.update();

                    // Table Update
                    const tbody = document.querySelector('#readingsTable tbody');
                    const row = `<tr>
                        <td>${data.timestamp}</td>
                        <td class="numeric">${data.temp}</td>
                        <td class="numeric">${data.fan_rpm}</td>
                        <td class="numeric">${data.cpu_usage}%</td>
                        <td class="numeric">${data.ram_usage}%</td>
                    </tr>`;
                    tbody.insertAdjacentHTML('afterbegin', row);
                    if (tbody.children.length > 10) tbody.lastElementChild.remove();

                    updateLiveIndicator();
                })
                .catch(() => {
                    updateLiveIndicator();
                });
        }

        initChart();
        updateDashboard();
        setInterval(updateDashboard, 3000);
        setInterval(updateLiveIndicator, 5000);
    </script>
</body>
</html>'''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
