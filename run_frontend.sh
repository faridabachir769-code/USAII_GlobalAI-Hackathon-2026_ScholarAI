#!/usr/bin/env bash
echo "Starting ScholarAI Frontend (Vite + React)..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/frontend"
npm run dev
