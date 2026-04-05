/* dashboard.js – live polling + persistent history chart + threshold alerts */
(function () {
  'use strict';

  const POLL_MS       = 3000;
  const STALE_MS      = 15000;
  const MAX_READINGS  = 15;

  // Thresholds injected by Flask template, fallback defaults
  const THR = window.THRESHOLDS || {
    temp_warn: 70, temp_crit: 80,
    cpu_warn: 70,  cpu_crit: 85,
    ram_warn: 70,  ram_crit: 85,
    disk_warn: 80, disk_crit: 90,
  };

  // CSS variable colour helpers
  const COLOR = {
    normal : 'var(--c-normal)',
    warn   : 'var(--c-warn)',
    crit   : 'var(--c-crit)',
    temp   : 'var(--c-temp)',
    fan    : 'var(--c-fan)',
    cpu    : 'var(--c-cpu)',
    ram    : 'var(--c-ram)',
    disk   : 'var(--c-disk)',
  };

  let chart;
  let lastUpdateAt  = Date.now();
  let activeHours   = 1;
  let historyFetching = false;

  // -------------------------------------------------------------------------
  // Chart
  // -------------------------------------------------------------------------
  function initChart() {
    const ctx = document.getElementById('historyChart').getContext('2d');
    chart = new Chart(ctx, {
      type: 'line',
      data: { labels: [], datasets: [
        { label: 'Temp °C',    data: [], borderColor: '#f85149', tension: 0.3, borderWidth: 2, pointRadius: 0, fill: false },
        { label: 'Fan /100',   data: [], borderColor: '#58a6ff', tension: 0.3, borderWidth: 1.5, pointRadius: 0, fill: false },
        { label: 'CPU %',      data: [], borderColor: '#bc8cff', tension: 0.3, borderWidth: 1.5, pointRadius: 0, fill: false },
        { label: 'RAM %',      data: [], borderColor: '#e3b341', tension: 0.3, borderWidth: 1.5, pointRadius: 0, fill: false },
      ]},
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        animation: { duration: 200 },
        scales: {
          x: { ticks: { maxTicksLimit: 8, color: '#8b949e', font: { size: 10 } }, grid: { color: '#21262d' } },
          y: { min: 0, max: 100, ticks: { stepSize: 25, color: '#8b949e', font: { size: 10 } }, grid: { color: '#21262d' } },
        },
        plugins: {
          legend: { position: 'bottom', labels: { color: '#8b949e', usePointStyle: true, boxWidth: 8, font: { size: 10 } } },
          tooltip: {
            callbacks: {
              label: function (c) {
                if (c.dataset.label.includes('Fan')) return 'Fan: ' + (c.parsed.y * 100).toFixed(0) + ' RPM';
                return c.dataset.label + ': ' + c.parsed.y;
              },
            },
          },
        },
      },
    });
  }

  function loadHistory(hours) {
    if (historyFetching) return;
    historyFetching = true;
    fetch('/api/history?hours=' + hours)
      .then(function (r) { return r.json(); })
      .then(function (rows) {
        const d = chart.data;
        d.labels = rows.map(function (r) { return r.ts; });
        d.datasets[0].data = rows.map(function (r) { return r.temp; });
        d.datasets[1].data = rows.map(function (r) { return +(r.fan_rpm / 100).toFixed(1); });
        d.datasets[2].data = rows.map(function (r) { return r.cpu; });
        d.datasets[3].data = rows.map(function (r) { return r.ram; });
        chart.update();
      })
      .catch(function () {})
      .finally(function () { historyFetching = false; });
  }

  // -------------------------------------------------------------------------
  // Time-range tabs
  // -------------------------------------------------------------------------
  function initTimeTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(function (btn) {
      btn.addEventListener('click', function () {
        tabs.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        activeHours = parseInt(btn.dataset.hours, 10);
        loadHistory(activeHours);
      });
    });
  }

  // -------------------------------------------------------------------------
  // Status helpers
  // -------------------------------------------------------------------------
  function statusOf(val, warn, crit) {
    if (val >= crit) return 'critical';
    if (val >= warn) return 'warning';
    return 'normal';
  }

  function setBadgeClass(el, status) {
    if (!el) return;
    el.className = 'card-badge';
    if (status === 'warning')  el.classList.add('warn');
    if (status === 'critical') el.classList.add('crit');
  }

  function setProgress(id, pct, warn, crit) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.width = pct + '%';
    el.style.background = pct >= crit ? COLOR.crit : pct >= warn ? COLOR.warn : COLOR.normal;
  }

  function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  function setCardStatus(id, status) {
    const el = document.getElementById(id);
    if (el) el.dataset.status = status;
  }

  // -------------------------------------------------------------------------
  // Live update
  // -------------------------------------------------------------------------
  function applyData(data) {
    lastUpdateAt = Date.now();

    // Header timestamp
    setText('lastUpdate', data.timestamp);

    // --- Temperature ---
    setText('tempValue', data.temp + '°C');
    setText('clockValue', data.clock_speed + ' MHz');
    const tempSt = statusOf(data.temp, THR.temp_warn, THR.temp_crit);
    setCardStatus('tempCard', tempSt);
    const tb = document.getElementById('throttleStatus');
    if (tb) {
      tb.textContent = data.throttle_status;
      setBadgeClass(tb, data.throttle_healthy ? 'normal' : 'critical');
    }

    // --- Fan ---
    setText('fanValue', data.fan_rpm + ' RPM');
    const fb = document.getElementById('fanStatus');
    if (fb) {
      fb.textContent = data.status_fan;
      setBadgeClass(fb, data.fan_available ? 'normal' : 'warn');
    }
    setCardStatus('fanCard', data.fan_available ? 'normal' : 'warn');

    // --- CPU ---
    setText('cpuValue', data.cpu_usage + '%');
    const cpuSt = statusOf(data.cpu_usage, THR.cpu_warn, THR.cpu_crit);
    setCardStatus('cpuCard', cpuSt);
    setBadgeClass(document.getElementById('cpuStatus'), cpuSt);
    setText('cpuStatus', data.status_cpu);
    setProgress('cpuFill', data.cpu_usage, THR.cpu_warn, THR.cpu_crit);

    // --- RAM ---
    setText('ramValue', data.ram_usage + '%');
    const ramSt = statusOf(data.ram_usage, THR.ram_warn, THR.ram_crit);
    setCardStatus('ramCard', ramSt);
    setBadgeClass(document.getElementById('ramStatus'), ramSt);
    setText('ramStatus', data.status_ram);
    setProgress('ramFill', data.ram_usage, THR.ram_warn, THR.ram_crit);

    // --- Disk ---
    setText('diskValue', data.disk_usage + '%');
    setText('diskFree', data.disk_free + ' GB free / ' + data.disk_total + ' GB');
    const diskSt = statusOf(data.disk_usage, THR.disk_warn, THR.disk_crit);
    setCardStatus('diskCard', diskSt);
    setBadgeClass(document.getElementById('diskStatus'), diskSt);
    setText('diskStatus', data.status_disk);
    setProgress('diskFill', data.disk_usage, THR.disk_warn, THR.disk_crit);

    // --- Top processes table ---
    const pt = document.querySelector('#procTable tbody');
    if (pt) {
      pt.innerHTML = (data.top_procs || []).map(function (p) {
        return '<tr><td>' + p.name + '</td><td class="num">' + p.cpu_percent + '%</td></tr>';
      }).join('');
    }

    // --- Recent readings table (last MAX_READINGS rows live) ---
    const rt = document.querySelector('#readingsTable tbody');
    if (rt) {
      rt.insertAdjacentHTML('afterbegin',
        '<tr>' +
          '<td>' + data.timestamp + '</td>' +
          '<td class="num">' + data.temp + '</td>' +
          '<td class="num">' + data.fan_rpm + '</td>' +
          '<td class="num">' + data.cpu_usage + '%</td>' +
          '<td class="num">' + data.ram_usage + '%</td>' +
        '</tr>'
      );
      while (rt.children.length > MAX_READINGS) rt.lastElementChild.remove();
    }

        // Render thermal zones
    renderThermalZones(data.thermal_zones);

    updateLive();
  }

  // -------------------------------------------------------------------------
  // Live indicator
  // -------------------------------------------------------------------------
  function updateLive() {
    const dot   = document.getElementById('liveDot');
    const badge = document.getElementById('liveBadge');
    const stale = Date.now() - lastUpdateAt > STALE_MS;
    if (dot)   dot.classList.toggle('stale', stale);
    if (badge) badge.classList.toggle('stale', stale);
  }

  // -------------------------------------------------------------------------
  // Polling
  // -------------------------------------------------------------------------
  function poll() {
    fetch('/api/stats')
      .then(function (r) { return r.json(); })
      .then(applyData)
      .catch(updateLive);
  }

  // -------------------------------------------------------------------------
  // Boot
  // -------------------------------------------------------------------------

// ------------------------------------------------------------------------- 
// Theme toggle
// -------------------------------------------------------------------------
function initTheme() {
    const toggle = document.getElementById('themeToggle');
    const icon = document.getElementById('themeIcon');
    const stored = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', stored);
    icon.textContent = stored === 'dark' ? '☀️' : '🌙';
    if (toggle) {
        toggle.addEventListener('click', function () {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            icon.textContent = next === 'dark' ? '☀️' : '🌙';
        });
    }
}

// -------------------------------------------------------------------------
// Thermal zones rendering
// -------------------------------------------------------------------------
function renderThermalZones(zones) {
    const container = document.getElementById('thermalZones');
    if (!container || !zones || zones.length === 0) return;
    container.innerHTML = zones.map(function (z) {
        return (
            '<div class="zone-item">' +
            '<div class="zone-label">' + z.type + ' (Zone ' + z.id + ')</div>' +
            '<div class="zone-temp">' + z.temp + '°C</div>' +
            '</div>'
        );
    }).join('');
}

// -------------------------------------------------------------------------
// CSV Export button
// -------------------------------------------------------------------------
function initCsvExport() {
    const btn = document.getElementById('exportCsvBtn');
    if (btn) {
        btn.addEventListener('click', function () {
            window.location.href = '/api/export/csv?hours=' + activeHours;
        });
    }
}
  initChart();
  initTimeTabs();
  loadHistory(activeHours);
  poll();
  setInterval(poll, POLL_MS);
  initTheme();
initCsvExport();
  setInterval(updateLive, 5000);
  // Refresh history every minute so chart stays up to date without full reload
  setInterval(function () { loadHistory(activeHours); }, 60000);

}());
