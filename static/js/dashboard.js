/* dashboard.js – handles Chart.js initialisation and live polling */

(function () {
  'use strict';

  const POLL_INTERVAL_MS = 3000;
  const STALE_THRESHOLD_MS = 15000;
  const MAX_HISTORY = 20;
  const MAX_READINGS = 10;

  const history = { labels: [], temp: [], fan: [], cpu: [], ram: [] };
  let chart;
  let lastUpdateAt = Date.now();

  // -------------------------------------------------------------------------
  // Chart initialisation
  // -------------------------------------------------------------------------
  function initChart() {
    const ctx = document.getElementById('historyChart').getContext('2d');
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: history.labels,
        datasets: [
          {
            label: 'Temp (\u00b0C)',
            data: history.temp,
            borderColor: '#e74c3c',
            tension: 0.3,
            borderWidth: 2.2,
            pointRadius: 0,
          },
          {
            label: 'Fan RPM / 100',
            data: history.fan,
            borderColor: '#3498db',
            tension: 0.3,
            borderWidth: 1.7,
            pointRadius: 0,
          },
          {
            label: 'CPU %',
            data: history.cpu,
            borderColor: '#9b59b6',
            tension: 0.3,
            borderWidth: 1.7,
            pointRadius: 0,
          },
          {
            label: 'RAM %',
            data: history.ram,
            borderColor: '#f1c40f',
            tension: 0.3,
            borderWidth: 1.7,
            pointRadius: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        scales: {
          y: { type: 'linear', position: 'left', min: 0, max: 100, ticks: { stepSize: 20 } },
        },
        plugins: {
          legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, font: { size: 10 } } },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                const label = ctx.dataset.label || '';
                if (label.includes('Fan')) return label + ': ' + (ctx.parsed.y * 100).toFixed(0) + ' RPM';
                return label + ': ' + ctx.parsed.y;
              },
            },
          },
        },
      },
    });
  }

  // -------------------------------------------------------------------------
  // Card state helpers
  // -------------------------------------------------------------------------
  function setCardClass(id, stateClass) {
    const el = document.getElementById(id);
    if (el) el.className = 'metric-card ' + stateClass;
  }

  function levelClass(value, warnThreshold, critThreshold) {
    if (value >= critThreshold) return 'metric-critical';
    if (value >= warnThreshold) return 'metric-warning';
    return 'metric-normal';
  }

  // -------------------------------------------------------------------------
  // DOM update
  // -------------------------------------------------------------------------
  function applyData(data) {
    lastUpdateAt = Date.now();

    // Values
    setText('tempValue', data.temp + '\u00b0C');
    setText('clockValue', 'Clock: ' + data.clock_speed + ' MHz');
    setText('fanValue', data.fan_rpm + ' RPM');
    setText('cpuValue', data.cpu_usage + '%');
    setText('ramValue', data.ram_usage + '%');
    setText('diskValue', data.disk_usage + '%');
    setText('diskFree', 'Free: ' + data.disk_free + ' GB / ' + data.disk_total + ' GB');
    setText('lastUpdate', data.timestamp);

    // Throttle badge
    const tb = document.getElementById('throttleStatus');
    if (tb) {
      tb.textContent = data.throttle_status;
      tb.className = 'metric-status ' + (data.throttle_healthy ? 'status-normal' : 'status-critical');
    }

    // Fan status badge
    const fb = document.getElementById('fanStatus');
    if (fb) {
      fb.textContent = data.status_fan;
      fb.className = 'metric-status ' + (data.status_fan === 'Idle' ? 'status-warning' : 'status-normal');
    }

    // Progress bars
    setProgress('cpuFill', data.cpu_usage, '#9b59b6', '#e74c3c', 85);
    setProgress('ramFill', data.ram_usage, '#f39c12', '#e74c3c', 85);
    setProgress('diskFill', data.disk_usage, '#27ae60', '#e74c3c', 90);

    // Card border states
    const tempState = (data.status_temp || 'Normal').toLowerCase().replace('critical', 'metric-critical').replace('warning', 'metric-warning').replace('normal', 'metric-normal');
    setCardClass('tempCard', tempState);
    setCardClass('cpuCard', levelClass(data.cpu_usage, 70, 85));
    setCardClass('ramCard', levelClass(data.ram_usage, 70, 85));
    setCardClass('diskCard', levelClass(data.disk_usage, 80, 90));
    setCardClass('fanCard', data.fan_available ? 'metric-normal' : 'metric-warning');

    // Top processes table
    const pt = document.querySelector('#procTable tbody');
    if (pt) {
      pt.innerHTML = (data.top_procs || []).map(function (p) {
        return '<tr><td>' + p.name + '</td><td class="numeric" style="font-weight:bold">' + p.cpu_percent + '%</td></tr>';
      }).join('');
    }

    // History chart
    trimHistory();
    history.labels.push(data.timestamp);
    history.temp.push(data.temp);
    history.fan.push(+(data.fan_rpm / 100).toFixed(1));
    history.cpu.push(data.cpu_usage);
    history.ram.push(data.ram_usage);
    chart.update();

    // Raw readings table
    const tbody = document.querySelector('#readingsTable tbody');
    if (tbody) {
      const row = '<tr>' +
        '<td>' + data.timestamp + '</td>' +
        '<td class="numeric">' + data.temp + '</td>' +
        '<td class="numeric">' + data.fan_rpm + '</td>' +
        '<td class="numeric">' + data.cpu_usage + '%</td>' +
        '<td class="numeric">' + data.ram_usage + '%</td>' +
        '</tr>';
      tbody.insertAdjacentHTML('afterbegin', row);
      while (tbody.children.length > MAX_READINGS) tbody.lastElementChild.remove();
    }

    updateLiveDot();
  }

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------
  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function setProgress(id, value, normalColor, critColor, threshold) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.width = value + '%';
    el.style.backgroundColor = value >= threshold ? critColor : normalColor;
  }

  function trimHistory() {
    if (history.labels.length >= MAX_HISTORY) {
      history.labels.shift();
      history.temp.shift();
      history.fan.shift();
      history.cpu.shift();
      history.ram.shift();
    }
  }

  function updateLiveDot() {
    const dot = document.getElementById('liveDot');
    if (!dot) return;
    const age = Date.now() - lastUpdateAt;
    dot.classList.toggle('stale', age > STALE_THRESHOLD_MS);
  }

  // -------------------------------------------------------------------------
  // Polling
  // -------------------------------------------------------------------------
  function poll() {
    fetch('/api/stats')
      .then(function (r) { return r.json(); })
      .then(applyData)
      .catch(updateLiveDot);
  }

  // -------------------------------------------------------------------------
  // Boot
  // -------------------------------------------------------------------------
  initChart();
  poll();
  setInterval(poll, POLL_INTERVAL_MS);
  setInterval(updateLiveDot, 5000);
}());
