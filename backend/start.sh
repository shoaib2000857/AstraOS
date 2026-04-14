#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
# Activate venv if exists
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi
python -m app.db init_db
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
