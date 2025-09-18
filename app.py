from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import utils_core
import team_logic
import waiver_logic
import trade_logic
import scout_logic
import learning

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return jsonify({"message": "FantasyCPU backend is running"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/insights", methods=["GET"])
def insights():
    data = {
        "team": team_logic.analyze_team(),
        "waivers": waiver_logic.run_general_manager_logic(),
        "trades": trade_logic.evaluate_trades(),
        "scout": scout_logic.run_scout_logic(),
    }
    return jsonify(data)


@app.route("/api/waivers", methods=["GET"])
def waivers():
    return jsonify(waiver_logic.run_general_manager_logic())


@app.route("/api/trades", methods=["GET"])
def trades():
    return jsonify(trade_logic.evaluate_trades())


@app.route("/api/scout", methods=["GET"])
def scout():
    return jsonify(scout_logic.run_scout_logic())


@app.route("/api/learn", methods=["POST"])
def learn():
    payload = request.json or {}
    results = learning.run_learning_cycle(payload)
    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
