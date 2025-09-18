import os
from flask import Flask, send_from_directory, request, jsonify
from dotenv import load_dotenv
from team_logic import run_team_logic
from waiver_logic import run_general_manager_logic
from scout_logic import run_scout_logic
from head_coach_logic import run_head_coach
from utils_core import load_roster, fetch_weather_data, fetch_odds
from learning import run_learning_cycle

load_dotenv()

app = Flask(__name__, static_folder="ui/dist", static_url_path="")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_proxy(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return {"ok": True, "status": "healthy"}, 200
@app.route("/api/team", methods=["GET"])
def team():
    roster = load_roster()
    weather = fetch_weather_data()
    odds = fetch_odds()
    result = run_team_logic(roster, weather, odds)
    return jsonify(result)


@app.route("/api/waivers", methods=["GET"])
def waivers():
    result = run_general_manager_logic()
    return jsonify(result)


@app.route("/api/scout", methods=["GET"])
def scout():
    result = run_scout_logic()
    return jsonify(result)


@app.route("/api/headcoach", methods=["GET"])
def headcoach():
    result = run_head_coach()
    return jsonify(result)


@app.route("/api/learn", methods=["POST"])
def learn():
    data = request.json if request.is_json else {}
    result = run_learning_cycle(data)
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
