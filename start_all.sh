#!/usr/bin/env bash
# ============================================
#  Starting ScholarAI - Unified Application
# ============================================
# Make sure Local Supabase is running first:
#   cd backend && supabase start

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo " Starting ScholarAI - Unified Application"
echo "============================================"
echo ""
echo "Make sure Local Supabase is running first:"
echo "  cd backend && supabase start"
echo ""

# Start Backend (port 8000)
echo "Starting Backend (port 8000)..."
cd "$SCRIPT_DIR/backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Start Frontend (port 5173)
echo "Starting Frontend (port 5173)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend:  http://localhost:8000/api/health"
echo "Frontend: http://localhost:5173"
echo ""

# Trap to clean up child processes on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait
}
trap cleanup EXIT INT TERM

# Wait for both processes
wait
