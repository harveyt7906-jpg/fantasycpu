#!/usr/bin/env python3
import os, sys, json, requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
CLIENT_SECRET = os.getenv("YAHOO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("YAHOO_REFRESH_TOKEN")
REDIRECT_URI = os.getenv("YAHOO_REDIRECT_URI")
ENV_PATH = ".env"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
JSON_PATH = "yahoo_token.json"


def refresh():
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        return {"error": "Missing CLIENT_ID, CLIENT_SECRET, or REFRESH_TOKEN in .env"}

    try:
        resp = requests.post(
            TOKEN_URL,
            auth=(CLIENT_ID, CLIENT_SECRET),
            data={
                "grant_type": "refresh_token",
                "redirect_uri": REDIRECT_URI,
                "refresh_token": REFRESH_TOKEN,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )
    except Exception as e:
        return {"error": f"Request failed: {e}"}

    if resp.status_code != 200:
        return {"error": f"{resp.status_code} {resp.text}"}

    data = resp.json()
    new_access_token = data.get("access_token")
    new_refresh_token = data.get("refresh_token", REFRESH_TOKEN)

    # Update .env
    lines = []
    with open(ENV_PATH, "r") as f:
        for line in f:
            if line.startswith("YAHOO_ACCESS_TOKEN="):
                lines.append(f"YAHOO_ACCESS_TOKEN={new_access_token}\n")
            elif line.startswith("YAHOO_REFRESH_TOKEN="):
                lines.append(f"YAHOO_REFRESH_TOKEN={new_refresh_token}\n")
            else:
                lines.append(line)
    with open(ENV_PATH, "w") as f:
        f.writelines(lines)

    # Save yahoo_token.json
    payload = {
        "updated": datetime.utcnow().isoformat(),
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "expires_in": data.get("expires_in"),
        "token_type": data.get("token_type"),
    }
    with open(JSON_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    return {"status": "ok", "saved_to": [ENV_PATH, JSON_PATH]}


if __name__ == "__main__":
    result = refresh()
    if "error" in result:
        print("❌", result["error"])
        sys.exit(1)
    print("✅ Yahoo tokens refreshed and saved:", result)
