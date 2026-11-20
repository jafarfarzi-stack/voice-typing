@echo off
setlocal
cd /d "%~dp0"
title Voice Typing - Build EXE with PyInstaller

set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" (
    echo [X] .venv not found. Run install.bat first.
    pause
    exit /b 1
)

"%VPY%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [1/2] Installing PyInstaller ...
    "%VPY%" -m pip install pyinstaller --disable-pip-version-check
    if errorlevel 1 goto :fail
) else (
    echo [1/2] PyInstaller already installed.
)

echo [2/2] Building VoiceTyping.exe ...
"%VPY%" -m PyInstaller --noconfirm --clean --onedir --name VoiceTyping --windowed ^
  --hidden-import=model_paths ^
  --hidden-import=faster_whisper --hidden-import=ctranslate2 ^
  --hidden-import=vosk --hidden-import=onnxruntime ^
  --hidden-import=pystray._win32 --hidden-import=keyboard._win32 ^
  --collect-all=faster_whisper --collect-all=ctranslate2 ^
  --collect-all=vosk --collect-all=onnxruntime ^
  app.py
if errorlevel 1 goto :fail

echo.
echo Done: %CD%\dist\VoiceTyping\VoiceTyping.exe
echo Copy the whole dist\VoiceTyping folder next to your portable zip.
echo   For the old single-file exe: copy portable_models.bat next to it
echo   and run it once to link its models folder to %%USERPROFILE%%\.voice_typing_models.
pause
exit /b 0

:fail
echo.
echo [X] Build failed. See the messages above.
pause
exit /b 1
