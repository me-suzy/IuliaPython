@echo off
setlocal enabledelayedexpansion
echo Pornirea scripturilor Python...
set PYTHON_PATH=c:\Users\necul\AppData\Local\Programs\Python\Python312\python.exe
set LOG_FILE=C:\Folder1\fisiere_gata\errors.log
:: Creare fișier log cu nume unic
set TIMESTAMP=%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set NEW_LOG_FILE=C:\Folder1\fisiere_gata\errors_%TIMESTAMP%.log
echo Logfile: %NEW_LOG_FILE% > %NEW_LOG_FILE%

:: Lista scripturilor în ordine
set SCRIPTS[0]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Iulia Python\Pasul 2 - Converteste bebe.docx in fisiere html (dupa ce ai tradus in engleza cu Google).py
set SCRIPTS[1]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Iulia Python\Pasul 3 - ADAUGA LINK-urile din RO in OUTPUT si invers (doar daca ai DATA si CATEGORIILE).py
set SCRIPTS[2]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Iulia Python\Pasul 4 - Preia DATA si Numele categoriilor din RO si le pune in fisierele noi EN.py
set SCRIPTS[3]=e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Iulia Python\Pasul 5 - Duce fiecare articol in fisierul categorii din care face parte si apoi in index FINAL.py

set /a count=0
set /a total=4
set /a errors=0

:: Rulăm scripturile (Pasul 2-5)
for /L %%i in (0,1,3) do (
    echo.
    echo ===================================================
    echo Rulare script !count! din %total%: !SCRIPTS[%%i]!
    echo ===================================================
    
    "%PYTHON_PATH%" "!SCRIPTS[%%i]!" 2>> "%NEW_LOG_FILE%"
    
    if !ERRORLEVEL! NEQ 0 (
        echo Eroare la rularea scriptului !SCRIPTS[%%i]! >> "%NEW_LOG_FILE%"
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