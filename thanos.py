import os, json, subprocess
from datetime import datetime
from flask import Flask, jsonify, send_from_directory
import psycopg2
import numpy as np

import utils_core, team_logic, general_manager_logic, waiver_logic, scout_logic, learning, notifications
from thanos_council import consult_council
from llm_adapter import llm_generate

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

# ------------------ Role Runners ------------------
@app.route("/api/run/head_coach")
def api_head_coach():
    roster, odds, weather = (
        utils_core.load_roster(),
        utils_core.fetch_odds(),
        utils_core.fetch_weather_data(),
    )
    result = team_logic.run_head_coach_logic(roster, odds, weather, None)
    save_run_to_db("head_coach", result)
    return jsonify(result)

@app.route("/api/run/gm")
def api_gm():
    roster, odds, weather = (
        utils_core.load_roster(),
        utils_core.fetch_odds(),
        utils_core.fetch_weather_data(),
    )
    result = general_manager_logic.run_general_manager_logic(roster, odds, weather)
    save_run_to_db("gm", result)
    return jsonify(result)

@app.route("/api/run/waiver")
def api_waiver():
    roster, odds, weather = (
        utils_core.load_roster(),
        utils_core.fetch_odds(),
        utils_core.fetch_weather_data(),
    )
    result = waiver_logic.run_waiver_logic(roster, odds, weather)
    save_run_to_db("waiver", result)
    return jsonify(result)

@app.route("/api/run/scout")
def api_scout():
    roster, odds, weather = (
        utils_core.load_roster(),
        utils_core.fetch_odds(),
        utils_core.fetch_weather_data(),
    )
    result = scout_logic.run_scout_logic(roster, odds, weather)
    save_run_to_db("scout", result)
    return jsonify(result)

@app.route("/api/run/trade")
def api_trade():
    roster, odds, weather = (
        utils_core.load_roster(),
        utils_core.fetch_odds(),
        utils_core.fetch_weather_data(),
    )
    from trade_logic import run_trade_logic
    result = run_trade_logic(roster, odds, weather)
    save_run_to_db("trade", result)
    return jsonify(result)

@app.route("/api/run/learning")
def api_learning():
    result = learning.refine_strategy()
    save_run_to_db("learning", result)
    return jsonify(result)

@app.route("/api/run/defense")
def api_defense():
    result = {
        "role": "defense",
        "strategy": "Contain top WR, blitz selectively",
        "timestamp": datetime.utcnow().isoformat(),
    }
    save_run_to_db("defense", result)
    return jsonify(result)

@app.route("/api/run/psycho")
def api_psycho():
    result = {
        "role": "psychoanalyst",
        "opponent_tendencies": "Overconfident in RB usage, tilts if QB throws pick",
        "timestamp": datetime.utcnow().isoformat(),
    }
    save_run_to_db("psycho", result)
    return jsonify(result)

# ------------------ Council / Decree ------------------
@app.route("/api/decree")
def api_decree():
    roster, odds, weather = (
        utils_core.load_roster(),
        utils_core.fetch_odds(),
        utils_core.fetch_weather_data(),
    )
    bundle = {
        "head_coach": team_logic.run_head_coach_logic(roster, odds, weather, None),
        "gm": general_manager_logic.run_general_manager_logic(roster, odds, weather),
        "waiver": waiver_logic.run_waiver_logic(roster, odds, weather),
        "scout": scout_logic.run_scout_logic(roster, odds, weather),
        "trade": __import__("trade_logic").run_trade_logic(roster, odds, weather),
        "defense": {"role": "defense", "strategy": "Contain top WR, blitz selectively"},
        "psycho": {"role": "psychoanalyst", "opponent_tendencies": "Overconfident in RB usage"},
        "learning": learning.refine_strategy(),
    }
    council = consult_council("time_keepers", bundle)
    decree = {"timestamp": datetime.utcnow().isoformat(), "bundle": bundle, "decree": council}
    save_run_to_db("decree", decree)
    return jsonify(decree)

# ------------------ Utility ------------------
@app.route("/api/history")
def api_history():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT ts,kind,payload FROM runs ORDER BY ts DESC LIMIT 50")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    history = [{"ts": str(r[0]), "kind": r[1], "payload": r[2]} for r in rows]
    return jsonify(history)

@app.route("/api/season")
def api_season():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT payload FROM runs WHERE kind='head_coach' ORDER BY ts DESC LIMIT 100"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    win_probs = [
        r[0].get("logic", {}).get("win_prob", 0.5)
        for r in rows
        if isinstance(r[0], dict)
    ]
    if not win_probs:
        return jsonify({"error": "no data"})
    avg_win = float(np.mean(win_probs))
    outlook = {
        "games_sampled": len(win_probs),
        "avg_win_prob": avg_win,
        "playoff_odds": min(1.0, avg_win * 1.2),
        "champ_odds": min(1.0, avg_win * 0.8),
    }
    save_run_to_db("season", outlook)
    return jsonify(outlook)

@app.route("/api/scheduler")
def api_scheduler():
    from logic_runner import run_all
    result = run_all()
    save_run_to_db("scheduler", result)
    return jsonify(result)

@app.route("/api/panic")
def api_panic():
    out = subprocess.run(["bash", "panic.sh"], capture_output=True, text=True)
    return jsonify({"stdout": out.stdout, "stderr": out.stderr, "code": out.returncode})

@app.route("/api/refresh_tokens")
def api_refresh_tokens():
    out = subprocess.run(
        ["python", "refresh_yahoo_token.py"], capture_output=True, text=True
    )
    return jsonify({"stdout": out.stdout, "stderr": out.stderr, "code": out.returncode})

@app.route("/api/data_ingest")
def api_data_ingest():
    roster, odds, weather = (
        utils_core.load_roster(),
        utils_core.fetch_odds(),
        utils_core.fetch_weather_data(),
    )
    payload = {"roster": roster, "odds": odds, "weather": weather}
    save_run_to_db("data_ingest", payload)
    return jsonify(payload)

@app.route("/api/alerts")
def api_alerts():
    result = notifications.get_alerts()
    save_run_to_db("alerts", result)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
