@echo off
set "PYTHON=c:\work\Deep Agent\deepagent_1\Scripts\python.exe"

echo Starting Backend Server...
cd "c:\work\Deep Agent"
"%PYTHON%" -m uvicorn tour_assist.api:app --host localhost --port 8000 --reload
pause
