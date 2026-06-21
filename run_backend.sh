#!/usr/bin/env bash
echo "Starting Sahayak AI Backend Server..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
