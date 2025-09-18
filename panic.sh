#!/bin/bash
echo "Panic triggered at $(date)"
git fetch --all
git reset --hard origin/main
pkill -f gunicorn || true
