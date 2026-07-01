@echo off
echo Initializing APL Migration Project...
start "Backend" cmd /c "cd backend && python main.py"
start "Frontend" cmd /c "npm run dev"
echo System Online.
