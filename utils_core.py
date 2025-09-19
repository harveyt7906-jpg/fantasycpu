import os, json, time, requests
from functools import lru_cache

YAHOO_TEAM_KEY = os.getenv("YAHOO_TEAM_KEY")
YAHOO_TOKEN_FILE = os.getenv("YAHOO_TOKEN_FILE", "yahoo_token.json")

ODDS_PRIMARY = os.getenv("ODDS_PRIMARY", "sportsgameodds").lower()
SPORTSGAMEODDS_API_KEY = os.getenv("SPORTSGAMEODDS_API_KEY")
SPORTSDATAIO_API_KEY = os.getenv("SPORTSDATAIO_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

TOMORROWIO_API_KEY = os.getenv("TOMORROWIO_API_KEY")
VISUALCROSSING_API_KEY = os.getenv("VISUALCROSSING_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
STORMGLASS_API_KEY = os.getenv("STORMGLASS_API_KEY")


def _retry(call, tries=3, delay=0.75):
    for i in range(tries):
        try:
            return call()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(delay * (2**i))


def load_roster(week=1):
    if not os.path.exists(YAHOO_TOKEN_FILE):
        return {"error": "no_token"}
    with open(YAHOO_TOKEN_FILE, "r") as f:
        token_data = json.load(f)
    access_token = token_data.get("access_token")
    if not access_token or not YAHOO_TEAM_KEY:
        return {"error": "missing_token_or_team"}
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{YAHOO_TEAM_KEY}/roster;week={week}?format=json"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


TEAM_ZIP = {
    "Arizona Cardinals": "85305",
    "Atlanta Falcons": "30313",
    "Baltimore Ravens": "21230",
    "Buffalo Bills": "14203",
    "Carolina Panthers": "28202",
    "Chicago Bears": "60605",
    "Cincinnati Bengals": "45202",
    "Cleveland Browns": "44114",
    "Dallas Cowboys": "76011",
    "Denver Broncos": "80204",
    "Detroit Lions": "48226",
    "Green Bay Packers": "54304",
    "Houston Texans": "77054",
    "Indianapolis Colts": "46225",
    "Jacksonville Jaguars": "32202",
    "Kansas City Chiefs": "64129",
    "Las Vegas Raiders": "89118",
    "Los Angeles Chargers": "90301",
    "Los Angeles Rams": "90301",
    "Miami Dolphins": "33056",
    "Minnesota Vikings": "55415",
    "New England Patriots": "02035",
    "New Orleans Saints": "70112",
    "New York Giants": "07073",
    "New York Jets": "07073",
    "Philadelphia Eagles": "19148",
    "Pittsburgh Steelers": "15212",
    "San Francisco 49ers": "95054",
    "Seattle Seahawks": "98134",
    "Tampa Bay Buccaneers": "33607",
    "Tennessee Titans": "37213",
    "Washington Commanders": "20785",
}


@lru_cache(maxsize=256)
def fetch_weather_data(team="Buffalo Bills"):
    for p in [
        _fetch_visualcrossing,
        _fetch_tomorrowio,
        _fetch_openweather,
        _fetch_stormglass,
    ]:
        try:
            result = p(team)
            if result and "error" not in result:
                return result
        except Exception:
            continue
    return {"team": team, "error": "all_weather_failed"}


def _fetch_visualcrossing(team):
    if not VISUALCROSSING_API_KEY:
        return {"error": "missing_VISUALCROSSING_API_KEY"}
    zip_code = TEAM_ZIP.get(team, "10001")
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{zip_code}?unitGroup=us&key={VISUALCROSSING_API_KEY}&contentType=json"
    resp = requests.get(url, timeout=8)
    resp.raise_for_status()
    d = resp.json().get("currentConditions", {})
    return {
        "provider": "visualcrossing",
        "team": team,
        "temp": d.get("temp"),
        "wind": d.get("windspeed"),
        "forecast": d.get("conditions"),
    }


def _fetch_tomorrowio(team):
    if not TOMORROWIO_API_KEY:
        return {"error": "missing_TOMORROWIO_API_KEY"}
    zip_code = TEAM_ZIP.get(team, "10001")
    url = f"https://api.tomorrow.io/v4/weather/realtime?location={zip_code}&apikey={TOMORROWIO_API_KEY}"
    resp = requests.get(url, timeout=8)
    resp.raise_for_status()
    vals = resp.json().get("data", {}).get("values", {})
    return {
        "provider": "tomorrowio",
        "team": team,
        "temp": vals.get("temperature"),
        "wind": vals.get("windSpeed"),
        "forecast": vals.get("weatherCode"),
    }


def _fetch_openweather(team):
    if not OPENWEATHER_API_KEY:
        return {"error": "missing_OPENWEATHER_API_KEY"}
    zip_code = TEAM_ZIP.get(team, "10001")
    url = f"https://api.openweathermap.org/data/2.5/weather?zip={zip_code},US&appid={OPENWEATHER_API_KEY}&units=imperial"
    resp = requests.get(url, timeout=8)
    resp.raise_for_status()
    d = resp.json()
    return {
        "provider": "openweather",
        "team": team,
        "temp": d.get("main", {}).get("temp"),
        "wind": d.get("wind", {}).get("speed"),
        "forecast": (d.get("weather") or [{}])[0].get("main"),
    }


def _fetch_stormglass(team):
    if not STORMGLASS_API_KEY:
        return {"error": "missing_STORMGLASS_API_KEY"}
    url = "https://api.stormglass.io/v2/weather/point?lat=40.71&lng=-74.01&params=airTemperature,windSpeed"
    headers = {"Authorization": STORMGLASS_API_KEY}
    resp = requests.get(url, headers=headers, timeout=8)
    resp.raise_for_status()
    d = resp.json().get("hours", [{}])[0]
    return {
        "provider": "stormglass",
        "team": team,
        "temp": d.get("airTemperature", [{}])[0].get("value"),
        "wind": d.get("windSpeed", [{}])[0].get("value"),
        "forecast": "marine_conditions",
    }


def fetch_odds():
    if ODDS_PRIMARY == "sportsgameodds":
        data = fetch_sportsgameodds()
        if "error" not in data:
            return data
        return fetch_sportsdataio() or fetch_oddsapi()
    if ODDS_PRIMARY == "sportsdataio":
        data = fetch_sportsdataio()
        if "error" not in data:
            return data
        return fetch_sportsgameodds() or fetch_oddsapi()
    if ODDS_PRIMARY == "oddsapi":
        data = fetch_oddsapi()
        if "error" not in data:
            return data
        return fetch_sportsgameodds() or fetch_sportsdataio()
    return {"error": "invalid_ODDS_PRIMARY"}


def fetch_sportsgameodds():
    if not SPORTSGAMEODDS_API_KEY:
        return {"error": "missing_SPORTSGAMEODDS_API_KEY"}
    url = "https://api.sportsgameodds.com/v1/sports/nfl/odds"
    headers = {"X-API-Key": SPORTSGAMEODDS_API_KEY}
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        return {"provider": "sportsgameodds", "data": resp.json()}
    except Exception as e:
        return {"error": str(e)}


def fetch_sportsdataio():
    if not SPORTSDATAIO_API_KEY:
        return {"error": "missing_SPORTSDATAIO_API_KEY"}
    url = "https://api.sportsdata.io/v3/nfl/odds/json/GameOddsByWeek/2025REG/1"
    headers = {"Ocp-Apim-Subscription-Key": SPORTSDATAIO_API_KEY}
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        return {"provider": "sportsdataio", "data": resp.json()}
    except Exception as e:
        return {"error": str(e)}


def fetch_oddsapi():
    if not ODDS_API_KEY:
        return {"error": "missing_ODDS_API_KEY"}
    url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
    params = {"apiKey": ODDS_API_KEY, "regions": "us,uk,eu", "markets": "totals"}
    try:
        resp = requests.get(url, params=params, timeout=12)
        resp.raise_for_status()
        return {"provider": "theoddsapi", "data": resp.json()}
    except Exception as e:
        return {"error": str(e)}

def fetch_free_agents(week=1):
    if not os.path.exists(YAHOO_TOKEN_FILE):
        return {"error": "no_token"}
    with open(YAHOO_TOKEN_FILE, "r") as f:
        token_data = json.load(f)
    access_token = token_data.get("access_token")
    if not access_token or not YAHOO_LEAGUE_ID:
        return {"error": "missing_token_or_league"}
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{YAHOO_LEAGUE_ID}/players;status=FA;count=50?format=json"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def lookup_player(player_id):
    return {"id": player_id, "name": player_id.split("_")[-1]}
