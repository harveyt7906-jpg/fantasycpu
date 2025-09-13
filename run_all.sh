#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source venv/bin/activate
python draft_assistant.py &          # engine
sleep 1
python draft_assistant_web.py &      # ui server
open http://127.0.0.1:5000
wait

