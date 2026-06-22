@echo off
echo ============================================
echo  Starting ScholarAI - Unified Application
echo ============================================
echo.
echo Make sure Local Supabase is running first:
echo   cd backend ^&^& supabase start
echo.
echo Starting Backend (port 8000)...
start "ScholarAI-Backend" cmd /c "cd /d %~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
echo Starting Frontend (port 5173)...
start "ScholarAI-Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"
echo.
echo Backend:  http://localhost:8000/api/health
echo Frontend: http://localhost:5173
echo.
pause
