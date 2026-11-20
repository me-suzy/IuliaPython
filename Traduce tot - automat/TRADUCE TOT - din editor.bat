@echo off
rem Pornit de butonul "Translate" din Mini Dreamweaver. %1 = fisierul jurnal citit de editor.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set TRADUCE_TOT_MARCAJ=1
cd /d "%~dp0"
"c:\Users\necul\AppData\Local\Programs\Python\Python312\python.exe" -u "TRADUCE TOT - automat.py" > "%~1" 2>&1
