#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json, time, uuid, argparse, sqlite3, logging
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache, wraps
from html import escape
from math import isnan

import requests
from flask import Flask, request, jsonify, has_request_context
from dotenv import load_dotenv

# ---------- env ----------
load_dotenv()

DEFAULT_LLM = os.getenv("DEFAULT_LLM", "claude")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")

CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
CLIENT_SECRET = os.getenv("YAHOO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("YAHOO_REDIRECT_URI", "https://localhost:8443/callback")
TOKEN_FILE = os.getenv("YAHOO_TOKEN_FILE", "yahoo_token.json")
TEAM_KEY = os.getenv("YAHOO_TEAM_KEY")

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

API_TOKEN = os.getenv("API_TOKEN")
DB_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL", "brain.db")
VERSION = os.getenv("BRAIN_VERSION", "2025.09.08-c")
PROMPTS_DIR = os.getenv("PROMPTS_DIR", "prompts")

AUTH_BASE = "https://api.login.yahoo.com/oauth2"
AUTH_URL = f"{AUTH_BASE}/request_auth"
TOKEN_URL = f"{AUTH_BASE}/get_token"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


# ---------- utils ----------
def now_ts() -> int:
    return int(time.time())


@app.before_request
def _req_id():
    request.req_id = uuid.uuid4().hex[:8]


@app.after_request
def _req_id_hdr(resp):
    resp.headers["X-Request-ID"] = getattr(request, "req_id", "-")
    return resp


def require_token(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        if API_TOKEN and request.headers.get("X-API-KEY") != API_TOKEN:
            return jsonify({"error": "unauthorized"}), 401
        return fn(*a, **k)

    return wrapper


def _retry(call, tries=3, delay=0.75):
    for i in range(tries):
        try:
            return call()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(delay * (2**i))


# ---------- prompt templates ----------
class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


# ---------- prompt templates ----------
def load_prompt(name: str, **vars) -> str:
    """
    Load a prompt template from prompts/<name>.txt and substitute only {{key}} placeholders.
    Literal braces { ... } in the template will not break formatting.
    """
    path = os.path.join(PROMPTS_DIR, f"{name}.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            tmpl = f.read()
        # Manual replacement: only swap {{key}} placeholders
        for k, v in vars.items():
            tmpl = tmpl.replace("{{" + k + "}}", str(v))
        return tmpl
    except FileNotFoundError:
        # sane fallbacks if prompt file is missing
        defaults = {
            "head_coach": (
                "You are the Head Coach for week {week}.\n"
                "Roster: {roster}\nWeather: {weather}\nOdds: {odds}\n"
                "Return JSON with keys: lineup, bench, rationale."
            ),
            "gm": (
                "You are the GM for week {week}. "
                "Suggest waiver targets and trade ideas. Return JSON."
            ),
            "scout": (
                "You are the Scout for week {week}. "
                "Call out tendencies, risks, and exploitation plans. Return JSON."
            ),
            "defense": (
                "You are the Defensive Coordinator for week {week}. "
                "Summarize threats, tendencies, pressure points, adjustments. Return JSON."
            ),
        }
        return defaults.get(name, "Act as an expert. Context: {context}").format(**vars)


# ---------- sqlite ----------
def db_exec(sql: str, params: Tuple = ()):
    con = sqlite3.connect(DB_URL)
    try:
        con.execute(
            """
          CREATE TABLE IF NOT EXISTS runs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER, kind TEXT, week INTEGER, json TEXT
          )"""
        )
        con.execute(sql, params)
        con.commit()
    finally:
        con.close()


def db_exec_many(sql: str, rows: list[tuple]):
    con = sqlite3.connect(DB_URL)
    try:
        con.executemany(sql, rows)
        con.commit()
    finally:
        con.close()


def save_run(kind: str, week: int, payload: dict):
    db_exec(
        "INSERT INTO runs(ts,kind,week,json) VALUES(?,?,?,?)",
        (now_ts(), kind, week, json.dumps(payload, ensure_ascii=False)),
    )


# ---------- yahoo oauth ----------
def load_token() -> Optional[dict]:
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_token(token_data: dict):
    token_data["obtained_at"] = now_ts()
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2, ensure_ascii=False)


def build_auth_url() -> str:
    return f"{AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&language=en-us"


def exchange_code_for_token(code: str) -> dict:
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "grant_type": "authorization_code",
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=15)
    resp.raise_for_status()
    td = resp.json()
    save_token(td)
    return td


def refresh_token(refresh_token_value: str) -> dict:
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "refresh_token": refresh_token_value,
        "grant_type": "refresh_token",
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=15)
    resp.raise_for_status()
    td = resp.json()
    save_token(td)
    return td


def get_active_token() -> Optional[str]:
    token = load_token()
    if not token:
        return None
    obtained = token.get("obtained_at", now_ts())
    exp = int(token.get("expires_in", 3600))
    if time.time() > obtained + exp - 60:
        token = refresh_token(token["refresh_token"])
    return token.get("access_token")


# ---------- team / city mappings ----------
TEAM_CITY = {
    "Buffalo Bills": "Buffalo",
    "Kansas City Chiefs": "Kansas City",
    "Dallas Cowboys": "Dallas",
    "San Francisco 49ers": "San Francisco",
    "Philadelphia Eagles": "Philadelphia",
    "New York Jets": "New York",
    "New York Giants": "New York",
    "Miami Dolphins": "Miami",
}
PLAYER_TEAM = {}


def city_for_player(p: str) -> str:
    t = PLAYER_TEAM.get(p, "")
    return TEAM_CITY.get(t, t or p)


def team_for_player(p: str) -> str:
    return PLAYER_TEAM.get(p, p)


# ---------- live fetchers ----------
def _parse_yahoo_players(data: dict) -> List[str]:
    players: List[str] = []
    try:
        fc = data.get("fantasy_content", {})
        team_list = fc.get("team", [])
        team_dict = None
        for el in team_list:
            if isinstance(el, dict):
                team_dict = el
                break
        if not team_dict:
            return players
        roster = team_dict.get("roster", {})
        plist = roster.get("players", [])
        for item in plist:
            if not isinstance(item, dict):
                continue
            p = item.get("player", [])
            for part in p:
                if isinstance(part, dict) and "name" in part:
                    name = part["name"]
                    full = (
                        name.get("full")
                        or " ".join(
                            [name.get("first", ""), name.get("last", "")]
                        ).strip()
                    )
                    if full:
                        players.append(full)
                    break
    except Exception:
        return players
    return players


def fetch_yahoo_roster(week: int) -> Dict[str, Any]:
    def _call():
        tok = get_active_token()
        if not tok:
            return {"players": [], "week": week, "error": "no_token"}
        if not TEAM_KEY:
            return {"players": [], "week": week, "error": "missing_TEAM_KEY"}
        url = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{TEAM_KEY}/roster;week={week}?format=json"
        hdr = {"Authorization": f"Bearer {tok}", "Accept": "application/json"}
        resp = requests.get(url, headers=hdr, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {"players": _parse_yahoo_players(data), "week": week}

    try:
        return _retry(_call, tries=3, delay=0.75)
    except Exception as e:
        return {"players": [], "week": week, "error": str(e)}


@lru_cache(maxsize=256)
def fetch_weather_data(city: str) -> Dict[str, Any]:
    def _call():
        if not OPENWEATHER_API_KEY:
            return {"where": city, "error": "missing_OPENWEATHER_API_KEY"}
        q = requests.utils.quote(city)
        url = f"https://api.openweathermap.org/data/2.5/weather?q={q}&appid={OPENWEATHER_API_KEY}&units=imperial"
        resp = requests.get(url, timeout=12)
        if resp.status_code == 404:
            return {"where": city, "error": "city_not_found"}
        resp.raise_for_status()
        d = resp.json()
        return {
            "where": city,
            "forecast": (d.get("weather") or [{}])[0].get("main", "unknown"),
            "temp": float(d.get("main", {}).get("temp", 0.0)),
            "wind": float(d.get("wind", {}).get("speed", 0.0)),
        }

    try:
        return _retry(_call, tries=3, delay=0.6)
    except Exception as e:
        return {"where": city, "error": str(e)}


def _find_team_game_odds(data: List[dict], team: str):
    t = team.lower()
    for game in data:
        home = (game.get("home_team") or "").lower()
        away = (game.get("away_team") or "").lower()
        if t in (home, away):
            return game, ("home" if t == home else "away")
    return None


@lru_cache(maxsize=256)
def fetch_vegas_odds(team: str) -> Dict[str, Any]:
    def _call():
        if not ODDS_API_KEY:
            return {
                "team": team,
                "implied_total": None,
                "error": "missing_ODDS_API_KEY",
            }
        url = (
            "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
            f"?apiKey={ODDS_API_KEY}&regions=us&markets=totals&oddsFormat=american"
        )
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        games = resp.json()
        found = _find_team_game_odds(games, team)
        if not found:
            return {"team": team, "implied_total": None, "error": "team_not_found"}
        game, side = found
        home_team, away_team = game.get("home_team", ""), game.get("away_team", "")
        total_points = None
        try:
            bmk = (game.get("bookmakers") or [])[0]
            market = (bmk.get("markets") or [])[0]
            for o in market.get("outcomes") or []:
                if "point" in o:
                    total_points = float(o["point"])
                    break
        except Exception:
            total_points = None
        opponent = away_team if side == "home" else home_team
        implied = total_points / 2.0 if total_points is not None else None
        return {
            "team": team,
            "opponent": opponent,
            "side": side,
            "game_total": total_points,
            "implied_total": implied,
        }

    try:
        return _retry(_call, tries=3, delay=0.6)
    except Exception as e:
        return {"team": team, "implied_total": None, "error": str(e)}


# ---------- llm adapter ----------
def choose_llm() -> str:
    if has_request_context():
        llm = request.args.get("llm", DEFAULT_LLM).lower()
    else:
        llm = DEFAULT_LLM
    return llm if llm in ("claude", "ollama", "openai") else "claude"


def llm_generate(prompt: str, max_tokens: int = 600) -> str:
    if ANTHROPIC_API_KEY:
        try:
            import anthropic

            client = anthropic.Anthropic(
                api_key=ANTHROPIC_API_KEY,
                default_headers={"anthropic-version": "2023-06-01"},
            )
            resp = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            if resp and resp.content:
                return resp.content[0].text
        except Exception as e:
            logging.warning(f"Claude failed: {e}")
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logging.error(f"OpenAI failed: {e}")
            return f"LLM unavailable: {e}"
    return "No LLM available"


@app.route("/health", methods=["GET"])
def health():
    query = "Health check: confirm LLM pipeline is alive."
    response_data = {
        "status": "ok",
        "service": "fantasycpu",
        "version": VERSION,
        "primary_model": "claude-3-haiku-20240307",
        "fallback_model": "gpt-4o-mini",
        "response": None,
        "error": None,
    }
    try:
        response_data["response"] = llm_generate(query, max_tokens=32)
    except Exception as e:
        response_data["status"] = "fail"
        response_data["error"] = str(e)
    return jsonify(response_data)


@app.route("/test_llm", methods=["GET"])
def test_llm():
    query = "Test run: confirm LLM pipeline is operational."
    response_data = {
        "status": "ok",
        "query": query,
        "primary_model": "claude-3-haiku-20240307",
        "fallback_model": "gpt-4o-mini",
        "response": None,
        "error": None,
    }
    try:
        response_data["response"] = llm_generate(query, max_tokens=128)
    except Exception as e:
        response_data["status"] = "fail"
        response_data["error"] = str(e)
    return jsonify(response_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
