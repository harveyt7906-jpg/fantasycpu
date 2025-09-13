#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
CLIENT_SECRET = os.getenv("YAHOO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("YAHOO_REFRESH_TOKEN")
REDIRECT_URI = os.getenv("YAHOO_REDIRECT_URI")

TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"

if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
    print("❌ Missing CLIENT_ID, CLIENT_SECRET, or REFRESH_TOKEN in .env")
    exit(1)

print("🔄 Refreshing Yahoo OAuth token...")

resp = requests.post(
    TOKEN_URL,
    auth=(CLIENT_ID, CLIENT_SECRET),
    data={
        "grant_type": "refresh_token",
        "redirect_uri": REDIRECT_URI,
        "refresh_token": REFRESH_TOKEN,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=15,
)

if resp.status_code != 200:
    print(f"❌ Failed: {resp.status_code} {resp.text}")
    exit(1)

data = resp.json()
new_access_token = data["access_token"]
new_refresh_token = data.get("refresh_token", REFRESH_TOKEN)

print("✅ Success, new tokens retrieved!")

# --- update .env file ---
env_path = ".env"
lines = []
with open(env_path, "r") as f:
    for line in f:
        if line.startswith("YAHOO_ACCESS_TOKEN="):
            lines.append(f"YAHOO_ACCESS_TOKEN={new_access_token}\n")
        elif line.startswith("YAHOO_REFRESH_TOKEN="):
            lines.append(f"YAHOO_REFRESH_TOKEN={new_refresh_token}\n")
        else:
            lines.append(line)

with open(env_path, "w") as f:
    f.writelines(lines)

print("📂 .env updated with new tokens")
print("✅ Refreshed Yahoo token OK — saved to yahoo_token.json")
