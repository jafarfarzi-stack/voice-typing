@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Voice Typing - Uninstaller

echo.
echo ============================================================
echo    Voice Typing  -  Remove
echo ============================================================
echo.
echo This will delete:
echo   - the .venv folder (Python packages, about 500 MB)
echo   - the desktop shortcut
echo.
echo Your text, settings, log and downloaded models are KEPT:
echo   %%USERPROFILE%%\.voice_typing_config.json
echo   %%USERPROFILE%%\.voice_typing.log
echo   %%USERPROFILE%%\.voice_typing_models  (persistent model folder)
echo.
set /p OK="Delete the .venv folder and shortcut? [y/N] "
if /i not "%OK%"=="y" (
    echo Cancelled. Nothing was changed.
    pause
    exit /b 0
)

echo.
echo Removing desktop shortcut ...
powershell -ExecutionPolicy Bypass -File "%~dp0make_shortcut.ps1" -Remove >nul 2>&1

if exist ".venv" (
    echo Removing .venv (this takes a moment) ...
    rmdir /s /q ".venv"
    if exist ".venv" (
        echo [!] .venv could not be fully removed.
        echo     Close the app and delete the folder manually.
    ) else (
        echo Removed.
    )
) else (
    echo No .venv folder found.
)

if exist "models" (
    set /p DELMODELS="Delete old models in the app folder too? (frees space) [y/N] "
    if /i "!DELMODELS!"=="y" (
        echo Removing app-folder models ...
        rmdir /s /q "models"
        echo Removed.
    ) else (
        echo App-folder models kept.
    )
)
echo.
echo Models in %%USERPROFILE%%\.voice_typing_models are never removed by this script.

echo.
echo ============================================================
echo    Done.
echo ============================================================
echo.
pause
