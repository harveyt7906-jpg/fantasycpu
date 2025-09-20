# app.py
import os
import logging
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from dotenv import load_dotenv
import thanos

load_dotenv()
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Thanos"})


@app.route("/test_llm")
def test_llm():
    prompt = "Say 'FantasyCPU Rune Check'."
    return jsonify({"prompt": prompt, "response": thanos.llm_generate(prompt)})


@app.route("/dashboard")
def dashboard():
    week = request.args.get("week", None)
    return render_template(
        "dashboard.html", data=thanos.get_dashboard_data(week=week), week=week
    )


@app.route("/api/run/<role>", methods=["POST", "GET"])
def run_role(role):
    return jsonify(thanos.run_role(role))


@app.route("/api/run/all", methods=["POST", "GET"])
def run_all():
    return jsonify(thanos.run_all_roles())


@app.route("/api/run/trade", methods=["POST", "GET"])
def run_trade():
    return jsonify(thanos.run_trade_logic())


@app.route("/api/history")
def history():
    return jsonify(thanos.get_history())


@app.route("/api/scheduler", methods=["POST", "GET"])
def scheduler():
    return jsonify(thanos.run_scheduler())


@app.route("/api/panic", methods=["POST", "GET"])
def panic():
    return jsonify(thanos.run_panic())


@app.route("/api/refresh_tokens", methods=["POST", "GET"])
def refresh_tokens():
    return jsonify(thanos.refresh_tokens())


@app.route("/api/data_ingest", methods=["POST", "GET"])
def data_ingest():
    return jsonify(thanos.refresh_data())


@app.route("/api/alerts")
def alerts():
    return jsonify(thanos.get_alerts())


@app.route("/api/learning", methods=["POST", "GET"])
def learning():
    return jsonify(thanos.run_learning())


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Thanos app on port {port}")
    app.run(host="0.0.0.0", port=port)
