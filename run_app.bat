@echo off
set "PYTHON=c:\work\Deep Agent\deepagent_1\Scripts\python.exe"

echo Starting Deep Tour Agent System...
echo --------------------------------
echo 1. Starting Backend (API) in a new window...
start "DeepAgent Backend" "%PYTHON%" -m uvicorn tour_assist.api:app --host localhost --port 8000 --reload

echo 2. Waiting for backend to initialize (5s)...
timeout /t 5 >nul

echo 3. Starting Frontend (Streamlit)...
"%PYTHON%" -m streamlit run app.py
pause
