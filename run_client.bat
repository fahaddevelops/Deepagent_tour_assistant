@echo off
set "PYTHON=c:\work\Deep Agent\deepagent_1\Scripts\python.exe"

echo Starting Streamlit Client...
cd "c:\work\Deep Agent"
"%PYTHON%" -m streamlit run app.py
pause
