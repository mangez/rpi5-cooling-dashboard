# Contributing to rpi5-cooling-dashboard

Thank you for your interest in contributing! This project is open to everyone — whether you want to fix a bug, propose a new feature, or improve the docs.

---

## How to Use It As-Is

Install dependencies and run:

```bash
git clone https://github.com/mangez/rpi5-cooling-dashboard.git
cd rpi5-cooling-dashboard
pip install -r requirements.txt
python app.py
```

Open `http://<your-pi-ip>:8080` in any browser. That's it.

> **Note:** `psutil` is not listed in `requirements.txt` (it is pre-installed on most Raspberry Pi OS images). If you get an import error, run `pip install psutil` manually.

---

## Project Layout

```text
rpi5-cooling-dashboard/
├── app.py                  # Flask app: routes /, /api/stats, /api/history, /health
├── services/
│   └── metrics.py          # Sensor reads, SQLite persistence, threshold logic
├── static/
│   ├── css/style.css       # Dark design system with CSS custom properties
│   └── js/dashboard.js     # Chart.js init, polling, history tabs, alert banner
├── templates/
│   └── dashboard.html      # Jinja2 template: topbar, metric cards, time-range tabs
├── Dockerfile
├── requirements.txt
├── CONTRIBUTING.md
├── .github/PULL_REQUEST_TEMPLATE.md
└── README.md
```

When adding a new feature, keep concerns separated:
- **Backend logic** (sensor reads, DB queries) belongs in `services/metrics.py`
- **Routes** belong in `app.py`
- **Templates** belong in `templates/dashboard.html`
- **Styles** belong in `static/css/style.css` (use CSS custom properties / tokens)
- **Client-side JS** belongs in `static/js/dashboard.js`

---

## How to Contribute a Feature (via Pull Request)

### 1. Fork the repository
Click the **Fork** button at the top-right of the repo page. This creates your own copy under your GitHub account.

### 2. Clone your fork
```bash
git clone https://github.com/<your-username>/rpi5-cooling-dashboard.git
cd rpi5-cooling-dashboard
```

### 3. Create a feature branch
Always branch off `main`. Use a descriptive name:
```bash
git checkout -b feature/add-gpu-temp-card
```

Branch naming conventions:
- `feature/` — new features
- `fix/` — bug fixes
- `docs/` — documentation changes
- `refactor/` — code improvements

### 4. Make your changes
- Keep changes focused — one feature or fix per PR
- Follow Python PEP 8 for `app.py` and `services/metrics.py`
- Use CSS custom properties (defined in `:root`) for any new colours or spacing in `style.css`
- Test on a real Raspberry Pi 5 if possible

### 5. Commit with a clear message
```bash
git add .
git commit -m "feat: add GPU temperature card"
```

Commit message prefixes:

| Prefix | Use for |
|--------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `refactor:` | Code cleanup |
| `style:` | UI/CSS changes |
| `chore:` | Maintenance tasks |

### 6. Push to your fork
```bash
git push origin feature/add-gpu-temp-card
```

### 7. Open a Pull Request
Go to the original repo at `https://github.com/mangez/rpi5-cooling-dashboard` and click **"Compare & pull request"**.

---

## Feature Ideas (Good First PRs)

Here are some ideas if you’re looking for a starting point:

- [x] CPU usage % metric card
- [x] Memory (RAM) usage card
- [x] Historical chart using Chart.js
- [x] Dark design system with CSS tokens
- [x] Configurable temperature / CPU / RAM / disk thresholds via environment variables
- [x] Alert banner when a metric exceeds its Critical threshold
- [x] Docker / docker-compose support
- [x] Persistent SQLite history with auto-pruning
- [x] Time-range tabs for history chart (1 h / 6 h / 24 h)
- [x] `/health` liveness endpoint
- [ ] Dark/light mode toggle
- [ ] Support for multiple thermal zones
- [ ] Export readings to CSV
- [ ] Telegram / webhook alert on Critical threshold breach
- [ ] GPU temperature monitoring (for systems with a discrete GPU)

Feel free to open an **Issue** first to discuss your idea before implementing it.

---

## Code of Conduct

- Be respectful and constructive in all interactions
- PRs are reviewed and merged at the maintainer’s discretion

## Questions?

Open a [GitHub Issue](https://github.com/mangez/rpi5-cooling-dashboard/issues) and tag it with the `question` label.
