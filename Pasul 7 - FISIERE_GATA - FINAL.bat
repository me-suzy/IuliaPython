@echo off
setlocal enabledelayedexpansion
echo Pornirea scripturilor Python...
set PYTHON_PATH=c:\Users\necul\AppData\Local\Programs\Python\Python312\python.exe
set LOG_FILE=C:\Folder1\fisiere_gata\errors.log

:: Attempt to create a new log file with a unique name
set TIMESTAMP=%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set NEW_LOG_FILE=C:\Folder1\fisiere_gata\errors_%TIMESTAMP%.log
echo Logfile: %NEW_LOG_FILE% > %NEW_LOG_FILE%

set SCRIPTS[0]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\Sedinta 18\ENGLEZA\Parsing WEBSITE - EN.py
set SCRIPTS[1]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\Sedinta 4 internet\replace_nbsp_cu_un_singur_spatiu_in_tagurile.py
set SCRIPTS[2]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\Sedinta 4 internet\Sterge spatiile goale duble din tagurile (varianta FINALA).py
set SCRIPTS[3]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\Sedinta 9 (2022) (EMAIL)\BEBE-PARSING-Python (FARA SUBFOLDER).py
set SCRIPTS[4]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Schimba tagurile p class text obisnuit2 in H2 si H3.py
set SCRIPTS[5]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\inlocuieste-fisiere-gata-design-categorii.py
set SCRIPTS[6]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Inlocuieste fiecare icon-facebook jpg cu imaginea nou creata EN.py
set SCRIPTS[7]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\Sedinta 18\ENGLEZA\Ultimul_find_and_replace_1.py
set SCRIPTS[8]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\Sedinta 18\ENGLEZA\Categorii final 2025\Adauga imagine minimalizata in categorii EN - FIX.py

set /a count=0
set /a total=9
set /a errors=0

for /L %%i in (0,1,8) do (
    echo.
    echo ============================================================
    echo Rulare script !count! din %total%: !SCRIPTS[%%i]!
    echo ============================================================
    
%PYTHON_PATH% "!SCRIPTS[%%i]!"
if !ERRORLEVEL! NEQ 0 (
    echo [EROARE] Scriptul !SCRIPTS[%%i]! a esuat cu codul !ERRORLEVEL! >> %NEW_LOG_FILE%
    echo [EROARE] Scriptul a esuat cu codul !ERRORLEVEL!
    set /a errors+=1
) else (
    echo [OK] Script finalizat cu succes
)
    
    set /a count+=1
    
    REM Timeout mai lung dupa scriptul 7 (normalizare lead-uri)
    if %%i==7 (
        echo [ASTEPTARE] Pauza de 5 secunde dupa normalizare lead-uri...
        timeout /t 5 >nul
    ) else (
        timeout /t 2 >nul
    )
)

echo.
echo ============================================================
echo RAPORT FINAL
echo ============================================================
echo Total scripturi: %total%
echo Scripturi rulate cu succes: %count%
echo Scripturi cu erori: %errors%
echo.

if %errors% GTR 0 (
    echo [ATENTIE] Au aparut erori! Verificati %NEW_LOG_FILE%
) else (
    echo [SUCCES] Toate scripturile au rulat cu succes!
)

echo.
echo Log file: %NEW_LOG_FILE%
echo.
pause