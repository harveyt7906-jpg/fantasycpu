import os, json
from datetime import datetime
from flask import Flask, jsonify
import psycopg2
import utils_core, team_logic, general_manager_logic, waiver_logic, scout_logic, learning

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_conn():
    return psycopg2.connect(DATABASE_URL)

def save_run_to_db(kind, payload):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS runs (id SERIAL PRIMARY KEY, ts TIMESTAMP DEFAULT NOW(), kind TEXT, payload JSONB)"
        )
        cur.execute("INSERT INTO runs (kind,payload) VALUES (%s,%s)", (kind, json.dumps(payload)))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB save failed: {e}")

@app.route("/")
def index():
    return jsonify({"message": "Thanos AI Council online"})

@app.route("/api/run/head_coach")
def api_head_coach():
    try:
        roster = utils_core.load_roster()
        odds = utils_core.fetch_vegas_odds()
        weather = utils_core.fetch_weather_data()
        opponent = None
        result = team_logic.run_head_coach_logic(roster, odds, weather, opponent)
        save_run_to_db("head_coach", result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/run/gm")
def api_gm():
    try:
        roster = utils_core.load_roster()
        odds = utils_core.fetch_vegas_odds()
        weather = utils_core.fetch_weather_data()
        result = general_manager_logic.run_general_manager_logic(roster, odds, weather)
        save_run_to_db("gm", result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/run/waiver")
def api_waiver():
    try:
        roster = utils_core.load_roster()
        odds = utils_core.fetch_vegas_odds()
        weather = utils_core.fetch_weather_data()
        result = waiver_logic.run_waiver_logic(roster, odds, weather)
        save_run_to_db("waiver", result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/run/scout")
def api_scout():
    try:
        roster = utils_core.load_roster()
        odds = utils_core.fetch_vegas_odds()
        weather = utils_core.fetch_weather_data()
        opponent = None
        result = scout_logic.run_scout_logic(opponent if opponent else roster, odds, weather)
        save_run_to_db("scout", result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/run/learning")
def api_learning():
    try:
        result = learning.refine_strategy()
        save_run_to_db("learning", result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/run/nightly")
def api_nightly():
    try:
        roster = utils_core.load_roster()
        odds = utils_core.fetch_vegas_odds()
        weather = utils_core.fetch_weather_data()
        opponent = None

        head = team_logic.run_head_coach_logic(roster, odds, weather, opponent)
        gm = general_manager_logic.run_general_manager_logic(roster, odds, weather)
        waiver = waiver_logic.run_waiver_logic(roster, odds, weather)
        scout = scout_logic.run_scout_logic(opponent if opponent else roster, odds, weather)
        learn = learning.refine_strategy()

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "head_coach": head,
            "gm": gm,
            "waiver": waiver,
            "scout": scout,
            "learning": learn,
        }
        save_run_to_db("nightly_manual", results)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
