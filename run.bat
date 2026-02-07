@echo off
cd /d "%~dp0"
chcp 65001

echo Configured for Windows...
echo Checking for virtual environment...

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Set Python UTF-8 for compatibility...
set PYTHONUTF8=1

echo Installing dependencies...
pip install -r requirements.txt

echo Starting Whisper Transcription Tool...
streamlit run app.py

pause
