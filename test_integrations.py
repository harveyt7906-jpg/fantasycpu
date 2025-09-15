# test_integrations.py
import os
import json
from dotenv import load_dotenv
import requests

# Local imports
from utils_core import load_roster

# Load environment variables
load_dotenv()

# Keys
YAHOO_TEAM_KEY = os.getenv("YAHOO_TEAM_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


# ---- Yahoo Test ----
def test_yahoo_roster():
    try:
        roster = load_roster()
        print("\n✅ Yahoo Roster Test:")
        print(json.dumps(roster, indent=2)[:500])  # Preview first 500 chars
    except Exception as e:
        print("\n❌ Yahoo Roster Test Failed:", e)


# ---- Odds API Test ----
def test_vegas_odds():
    try:
        url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regions=us&oddsFormat=american&apiKey={ODDS_API_KEY}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        print("\n✅ Vegas Odds Test:")
        print(json.dumps(data[:1], indent=2))  # Show first game
    except Exception as e:
        print("\n❌ Vegas Odds Test Failed:", e)


# ---- OpenWeather Test ----
def test_weather():
    try:
        # Example: Green Bay, WI (Lambeau Field)
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Green%20Bay,US&appid={OPENWEATHER_API_KEY}&units=imperial"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        print("\n✅ Weather API Test:")
        print(json.dumps(data, indent=2)[:500])
    except Exception as e:
        print("\n❌ Weather API Test Failed:", e)


# ---- Claude Haiku Test ----
def test_claude():
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Reply with 'FantasyCPU Integration OK'"}
            ],
        )
        print("\n✅ Claude Haiku Test:")
        print(resp.content[0].text)
    except Exception as e:
        print("\n❌ Claude Haiku Test Failed:", e)


if __name__ == "__main__":
    print("=== Running Integration Tests ===")
    test_yahoo_roster()
    test_vegas_odds()
    test_weather()
    test_claude()
    print("\n=== Tests Complete ===")
