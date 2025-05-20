@echo off
cd /d "C:\Users\Lucas\Desktop\estoque helimarte"
call .venv\Scripts\activate.bat
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" http://127.0.0.1:8000/
python manage.py runserver
pause