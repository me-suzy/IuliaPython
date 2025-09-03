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
set SCRIPTS[6]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Iulia Python\Inlocuieste fiecare icon-facebook jpg cu imaginea nou creata.py
set SCRIPTS[7]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\Sedinta 18\ENGLEZA\Ultimul find and replace 2.py
set /a count=0
set /a total=8
set /a errors=0
for /L %%i in (0,1,7) do (
    echo Rulare script !count! din %total%: !SCRIPTS[%%i]!
    %PYTHON_PATH% "!SCRIPTS[%%i]!" 2>> %NEW_LOG_FILE%
    if !ERRORLEVEL! NEQ 0 (
        echo Eroare la rularea scriptului !SCRIPTS[%%i]! >> %NEW_LOG_FILE%
        echo Eroare la rularea scriptului !SCRIPTS[%%i]!
        set /a errors+=1
    ) else (
        echo Script finalizat cu succes: !SCRIPTS[%%i]!
    )
    set /a count+=1
    timeout /t 2 >nul
)
echo.
echo Toate scripturile au fost rulate.
echo Total scripturi: %total%
echo Scripturi cu erori: %errors%
echo Scripturi rulate cu succes: %count%
if %errors% GTR 0 (
    echo ATENȚIE: Au apărut erori la rularea unor scripturi! Verificați %NEW_LOG_FILE% pentru detalii.
) else (
    echo Toate scripturile au rulat cu succes!
)
echo.
echo Log file: %NEW_LOG_FILE%
pause