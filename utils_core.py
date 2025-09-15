import os, json, logging, subprocess, psycopg2
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
import utils_core, team_logic, waiver_logic, general_manager_logic, scout_logic, learning
import anthropic, openai

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Thanos")


def get_db_conn():
    return psycopg2.connect(DATABASE_URL)


def save_run_to_db(kind, payload):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS runs (
            id SERIAL PRIMARY KEY, kind TEXT, week INT, payload JSONB, ts TIMESTAMP DEFAULT NOW())"""
        )
        week = datetime.utcnow().isocalendar().week
        cur.execute(
            "INSERT INTO runs (kind, week, payload) VALUES (%s,%s,%s)",
            (kind, week, json.dumps(payload)),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"DB save failed: {e}")


def fetch_history(limit=10):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT kind, week, payload, ts FROM runs ORDER BY ts DESC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {"kind": r[0], "week": r[1], "payload": r[2], "ts": r[3].isoformat()}
            for r in rows
        ]
    except Exception as e:
        logger.error(f"DB fetch failed: {e}")
        return []


def llm_generate(prompt, max_tokens=500):
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        r = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text
    except:
        pass
    try:
        openai.api_key = OPENAI_API_KEY
        r = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return r["choices"][0]["message"]["content"]
    except:
        pass
    try:
        r = subprocess.run(
            ["ollama", "run", "llama3.1", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return r.stdout.strip()
    except:
        return "LLM unavailable"


def run_head_coach():
    return team_logic.run_head_coach_logic(
        utils_core.load_roster(),
        utils_core.fetch_vegas_odds(),
        utils_core.fetch_weather_data(),
    )


def run_general_manager():
    return general_manager_logic.run_general_manager_logic(
        utils_core.load_roster(),
        utils_core.fetch_vegas_odds(),
        utils_core.fetch_weather_data(),
    )


def run_scout():
    return scout_logic.run_scout_logic(
        utils_core.load_roster(),
        utils_core.fetch_vegas_odds(),
        utils_core.fetch_weather_data(),
    )


def run_defense():
    data = {
        "roster": utils_core.load_roster(),
        "odds": utils_core.fetch_vegas_odds(),
        "weather": utils_core.fetch_weather_data(),
    }
    return {"defense": llm_generate(f"Defense analysis: {json.dumps(data)[:2000]}")}


@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})


@app.route("/test_llm")
def test_llm():
    return jsonify({"llm_reply": llm_generate("Say: Thanos integration OK")})


@app.route("/api/run/<role>")
def api_run(role):
    if role == "head_coach":
        result = run_head_coach()
    elif role == "gm":
        result = run_general_manager()
    elif role == "scout":
        result = run_scout()
    elif role == "defense":
        result = run_defense()
    else:
        return jsonify({"error": "invalid role"}), 400
    save_run_to_db(role, result)
    return jsonify(result)


@app.route("/api/history")
def api_history():
    return jsonify(fetch_history(int(request.args.get("limit", 10))))


@app.route("/dashboard")
def dashboard():
    week = request.args.get("week", datetime.utcnow().isocalendar().week)
    data = {
        "head_coach": run_head_coach(),
        "gm": run_general_manager(),
        "scout": run_scout(),
        "defense": run_defense(),
    }
    save_run_to_db("dashboard", data)
    template = """<html><head><title>Thanos Dashboard</title>
    <style>body{background:#111;color:#eee;font-family:sans-serif}
    .tab{margin:20px;padding:10px;border:1px solid #444}h2{color:#6cf}</style></head>
    <body><h1>Thanos Dashboard - Week {{week}}</h1>
    {% for role,result in data.items() %}<div class="tab"><h2>{{role}}</h2>
    <pre>{{result | tojson(indent=2)}}</pre></div>{% endfor %}</body></html>"""
    return render_template_string(template, week=week, data=data)


def scheduled_run():
    results = {
        "head_coach": run_head_coach(),
        "gm": run_general_manager(),
        "scout": run_scout(),
        "defense": run_defense(),
    }
    save_run_to_db("nightly", results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
