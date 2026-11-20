@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Voice Typing - Link persistent model folder

REM For the portable EXE build: make the app's "models" folder point to a
REM stable folder in the user profile, so re-extracting the zip cannot delete
REM downloaded models. Run after every re-extraction of the zip.

set "TARGET=%USERPROFILE%\.voice_typing_models"
if not exist "%TARGET%" mkdir "%TARGET%" >nul 2>&1

echo Persistent model folder: %TARGET%
echo App folder:              %CD%
echo.

if exist "models" (
    fsutil reparsepoint query "models" >nul 2>&1
    if not errorlevel 1 (
        echo The "models" folder is already linked to the persistent folder.
        pause
        exit /b 0
    )
    dir /b "models" 2>nul | findstr . >nul
    if not errorlevel 1 (
        echo The "models" folder is not empty.
        choice /C YN /M "Copy its contents into the persistent folder first? [Y/N] "
        if errorlevel 2 goto :cancelled
        xcopy "models\*" "%TARGET%\" /E /I /Y /Q >nul
        if errorlevel 1 (
            echo Copy failed. Nothing was changed.
            pause
            exit /b 1
        )
    )
    rmdir /s /q "models" >nul 2>&1
)

mklink /J "models" "%TARGET%"
if errorlevel 1 (
    echo.
    echo Could not create the link. Try running this file as Administrator.
    pause
    exit /b 1
)

echo.
echo Done. The app now reads/writes models in:
echo   %TARGET%
echo Re-extracting the zip removes only the link, not the models.
echo Run this file again after re-extracting to restore the link.
pause
exit /b 0

:cancelled
echo Cancelled. Nothing was changed.
pause
