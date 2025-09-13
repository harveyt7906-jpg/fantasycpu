#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "== Kill strays =="
lsof -i :5000 -t | xargs -r kill -9 || true
lsof -i :8080 -t | xargs -r kill -9 || true

echo "== Activate venv =="
source venv/bin/activate || source ./venv/bin/activate

echo "== Deps =="
pip install -q requests oauthlib requests-oauthlib flask python-dotenv beautifulsoup4

echo "== Ensure ECR =="
python ecr_fallback_build_from_pool.py || true

echo "== Clean stale out files =="
mkdir -p out
rm -f out/draft_board.json out/draftresults_raw.json

echo "== Launch engine =="
python draft_assistant.py

