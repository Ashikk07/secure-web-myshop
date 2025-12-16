@echo off
call venv\Scripts\activate
set DJANGO_SETTINGS_MODULE=myshop.settings
python manage.py makemigrations orders
python manage.py migrate orders
pause
