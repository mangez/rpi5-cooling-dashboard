import os

from flask import Flask, jsonify, render_template, request

from services.metrics import get_history, get_stats

app = Flask(__name__)


@app.route("/")
def dashboard():
    stats = get_stats()
    return render_template("dashboard.html", **stats)


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


@app.route("/api/history")
def api_history():
    """Return persisted readings. Query param: ?hours=1 (default 1, max 168)."""
    try:
        hours = min(int(request.args.get("hours", 1)), 168)
    except (TypeError, ValueError):
        hours = 1
    return jsonify(get_history(hours))


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
