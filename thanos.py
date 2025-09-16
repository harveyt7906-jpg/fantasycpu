import os, json
from datetime import datetime
from flask import Flask, jsonify, send_from_directory
import psycopg2
import numpy as np
import utils_core, team_logic, general_manager_logic, waiver_logic, scout_logic, learning
from thanos_council import consult_council

app = Flask(__name__, static_folder="static")
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
        cur.execute(
            "INSERT INTO runs (kind,payload) VALUES (%s,%s)",
            (kind, json.dumps(payload)),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB save failed: {e}")

# ------------------ React UI ------------------
@app.route("/")
def serve_ui():
    return send_from_directory(app.static_folder, "index.html")

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_react(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# ------------------ Health ------------------
@app.route("/api/health")
def api_health():
    status = {"status": "ok", "db": "ok", "timestamp": datetime.utcnow().isoformat()}
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        status["db"] = f"error: {e}"
    return jsonify(status)

# ------------------ API ------------------
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

@app.route("/api/decree")
def api_decree():
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
        bundle = {
            "head_coach": head,
            "gm": gm,
            "waiver": waiver,
            "scout": scout,
            "learning": learn,
        }
        council = consult_council("time_keepers", bundle)
        decree = {"bundle": bundle, "decree": council}
        save_run_to_db("decree", decree)
        return jsonify(decree)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history")
def api_history():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT ts,kind,payload FROM runs ORDER BY ts DESC LIMIT 50")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        history = [{"ts": str(r[0]), "kind": r[1], "payload": r[2]} for r in rows]
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/season")
def api_season():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT payload FROM runs WHERE kind='head_coach' ORDER BY ts DESC LIMIT 100")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        win_probs = [
            r[0].get("logic", {}).get("win_prob", 0.5)
            for r in rows if isinstance(r[0], dict)
        ]
        if not win_probs:
            return jsonify({"error": "no data"})
        avg_win = float(np.mean(win_probs))
        playoff_odds = min(1.0, avg_win * 1.2)
        champ_odds = min(1.0, avg_win * 0.8)
        outlook = {
            "games_sampled": len(win_probs),
            "avg_win_prob": avg_win,
            "playoff_odds": playoff_odds,
            "champ_odds": champ_odds,
        }
        return jsonify(outlook)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
