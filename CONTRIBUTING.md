# Contributing to rpi5-cooling-dashboard

Thank you for your interest in contributing! This project is open to everyone — whether you want to fix a bug, propose a new feature, or improve the docs.

---

## How to Use It As-Is

No installation beyond Python and Flask is required:

```bash
git clone https://github.com/mangez/rpi5-cooling-dashboard.git
cd rpi5-cooling-dashboard
pip install flask
python app.py
```

Open `http://<your-pi-ip>:8080` in any browser. That's it.

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
git checkout -b feature/add-cpu-usage-chart
```

Branch naming conventions:
- `feature/<short-description>` — new features
- `fix/<short-description>` — bug fixes
- `docs/<short-description>` — documentation changes
- `refactor/<short-description>` — code improvements

### 4. Make your changes

- Keep changes focused — one feature or fix per PR
- Follow the existing code style (Python PEP 8, inline CSS/JS in `HTML_TEMPLATE`)
- Test on a real Raspberry Pi 5 if possible, or note that it was tested in a simulated environment

### 5. Commit with a clear message

```bash
git add .
git commit -m "feat: add CPU usage percentage card"
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
git push origin feature/add-cpu-usage-chart
```

### 7. Open a Pull Request

Go to the original repo at `https://github.com/mangez/rpi5-cooling-dashboard` and click **"Compare & pull request"**.

Fill in the PR template:
- What does this PR do?
- How was it tested?
- Any screenshots (for UI changes)?

---

## Feature Ideas (Good First PRs)

Here are some ideas if you're looking for a starting point:

- [ ] CPU usage % metric card
- [ ] Memory (RAM) usage card
- [ ] Historical chart using Chart.js or similar
- [ ] Dark/light mode toggle
- [ ] Configurable temperature thresholds via environment variables
- [ ] Alert / notification when temp exceeds Critical threshold
- [ ] Docker / docker-compose support
- [ ] Support for multiple thermal zones
- [ ] Export readings to CSV

Feel free to open an **Issue** first to discuss your idea before implementing it.

---

## Code of Conduct

- Be respectful and constructive in all interactions
- PRs are reviewed and merged at the maintainer's discretion
- All contributions are welcome regardless of skill level

---

## Questions?

Open a [GitHub Issue](https://github.com/mangez/rpi5-cooling-dashboard/issues) and tag it with the `question` label.
