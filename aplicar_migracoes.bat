@echo off
cd /d "C:\Users\Lucas\Desktop\estoque helimarte"
call .venv\Scripts\activate.bat
set DJANGO_SETTINGS_MODULE=controle_estoque.settings
python manage.py migrate
pause
