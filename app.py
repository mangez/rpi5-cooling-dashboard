import os

from flask import Flask, jsonify, render_template

from services.metrics import get_stats

app = Flask(__name__)


@app.route("/")
def dashboard():
    stats = get_stats()
    return render_template("dashboard.html", **stats)


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
