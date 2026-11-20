@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
"c:\Users\necul\AppData\Local\Programs\Python\Python312\python.exe" "TRADUCE TOT - automat.py" --schimba-cheia
echo.
pause
