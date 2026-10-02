@echo off
setlocal EnableDelayedExpansion
chcp 437 >nul 2>&1
cd /d "%~dp0"

title Voice Typing - Installer

echo.
echo ============================================================
echo    Voice Typing  -  Offline Persian / English
echo    Installer
echo ============================================================
echo.

REM ---------- 1) find a suitable python ----------
REM We need 3.9 - 3.13. PyAudio and Vosk have no prebuilt wheels for 3.14+,
REM so on newer interpreters pip has to compile them and fails.
set "PY="
set "PYVER="

REM Prefer py -3.13 .. -3.9, then plain py -3 / python (only if in range)
for %%V in (3.13 3.12 3.11 3.10 3.9) do (
    if not defined PY (
        py -%%V -c "import sys; sys.exit(0 if (3,9)<=sys.version_info[:2]<=(3,13) else 1)" >nul 2>&1
        if not errorlevel 1 set "PY=py -%%V"
    )
)

if not defined PY (
    py -3 -c "import sys; sys.exit(0 if (3,9)<=sys.version_info[:2]<=(3,13) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
    python -c "import sys; sys.exit(0 if (3,9)<=sys.version_info[:2]<=(3,13) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)

if not defined PY (
    echo [X] No suitable Python found.
    echo.
    echo     You need Python 3.9 to 3.13. Python 3.14 and newer do not have
    echo     prebuilt packages for PyAudio, which this app needs.
    echo.
    echo     1) Download Python 3.12 from:  https://www.python.org/downloads/
    echo     2) IMPORTANT: tick "Add python.exe to PATH" during setup
    echo     3) Run this file again
    echo.
    echo     If you already have 3.14, you can run:
    echo         py -3.12 -m venv .venv
    echo         .venv\Scripts\python -m pip install -r requirements.txt
    echo         .venv\Scripts\python app.py
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('%PY% -c "import sys;print(sys.version.split()[0])"') do set "PYVER=%%v"
echo [1/5] Python %PYVER% found (%PY%).

REM ---------- 2) virtual environment ----------
REM A venv left over from a different interpreter version is unusable.
if exist ".venv\pyvenv.cfg" (
    findstr /c:"version %PYVER%" ".venv\pyvenv.cfg" >nul 2>&1
    if errorlevel 1 (
        echo [2/5] Removing .venv - it was made with a different Python version ...
        rmdir /s /q ".venv"
    )
)
if exist ".venv\Scripts\python.exe" (
    echo [2/5] Virtual environment already exists - reusing it.
) else (
    echo [2/5] Creating virtual environment in .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [X] Could not create the virtual environment.
        echo     If you are on Windows 11, enable "Virtual Machine Platform"
        echo     in Features Optional, then try again.
        pause
        exit /b 1
    )
)
set "VPY=.venv\Scripts\python.exe"

REM ---------- 3) upgrade pip ----------
echo [3/5] Upgrading pip ...
"%VPY%" -m pip install --upgrade pip --quiet --disable-pip-version-check
if errorlevel 1 goto :pipfail

REM ---------- 4) dependencies ----------
echo [4/5] Installing packages. This can take a few minutes ...
"%VPY%" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 goto :pipfail

echo       Checking that PyAudio works ...
"%VPY%" -c "import pyaudio" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [!] PyAudio could not be imported. On Windows you often need:
    echo       "Microsoft Visual C++ Redistributable" - the latest one from:
    echo       https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist
    echo.
    echo       Everything else installed fine, so try running the app first.
    echo.
)

REM ---------- 5) desktop shortcut ----------
echo [5/5] Creating desktop shortcut ...
powershell -ExecutionPolicy Bypass -File "%~dp0make_shortcut.ps1" -PythonPath "%~dp0.venv\Scripts\pythonw.exe" >nul 2>&1
if errorlevel 1 (
    echo       Could not create the shortcut automatically.
    echo       You can still start the app with:  .venv\Scripts\python app.py
) else (
    echo       Done.
)

echo.
echo ============================================================
echo    Installation finished.
echo ============================================================
echo.
echo   Start:    "Voice Typing" shortcut on your desktop
echo   Hotkey:   F8
echo.
echo   First run asks whether to download a speech model.
echo   After that no internet is needed.
echo.
echo   Remove everything:  run uninstall.bat
echo.
pause

start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0app.py"
exit /b 0

:pipfail
echo.
echo [X] Package installation failed.
echo.
echo     Most likely cause: you are on Python 3.14 or newer, which has no
echo     prebuilt packages for PyAudio. Delete the .venv folder and run
echo     this file again, or use Python 3.12 directly:
echo.
echo         py -3.12 -m venv .venv
echo         .venv\Scripts\python -m pip install -r requirements.txt
echo         .venv\Scripts\python app.py
echo.
pause
exit /b 1
