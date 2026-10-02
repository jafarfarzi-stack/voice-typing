<#
    ساخت میان‌بر دسکتاپ برای اجرای تایپ صوتی
    Create a desktop shortcut for the voice typing app.

    اجرا در پوشه پروژه:
        powershell -ExecutionPolicy Bypass -File make_shortcut.ps1
#>

param(
    [string]$Name = "Voice Typing",
    [string]$PythonPath = "",
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppPath = Join-Path $ProjectDir "app.py"
$IconPath = Join-Path $ProjectDir "icon.ico"
$VenvPython = Join-Path $ProjectDir ".venv\Scripts\pythonw.exe"

# --- حذف میان‌بر ---
if ($Remove) {
    $lnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "$Name.lnk"
    if (Test-Path $lnk) {
        Remove-Item $lnk -Force
        Write-Host "Shortcut removed: $lnk" -ForegroundColor Yellow
    } else {
        Write-Host "No shortcut with that name found."
    }
    return
}

# --- بررسی وجود برنامه ---
if (-not (Test-Path $AppPath)) {
    throw "app.py not found: $AppPath"
}

# --- پیدا کردن پایتون ---
# اولویت: مسیر داده‌شده، بعد پایتونِ محیط مجازی، بعد مفسرهای سیستم
if ($PythonPath -and (Test-Path $PythonPath)) {
    $python = $PythonPath
}
elseif (Test-Path $VenvPython) {
    $python = $VenvPython
}
else {
    $found = $null
    foreach ($c in @("py", "python", "python3")) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd) { $found = $cmd.Source; break }
    }
    if (-not $found) {
        throw "No Python interpreter found. Install Python 3.9+ from python.org"
    }
    $python = $found
}

Write-Host "Python: $python"

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "$Name.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $python
$shortcut.Arguments = "`"$AppPath`""
$shortcut.WorkingDirectory = $ProjectDir
$shortcut.Description = "Offline Persian/English voice typing"
if (Test-Path $IconPath) {
    $shortcut.IconLocation = "$IconPath,0"
}
$shortcut.WindowStyle = 1
$shortcut.Save()

Write-Host ""
Write-Host "Shortcut created: $shortcutPath" -ForegroundColor Green
Write-Host "To remove it:  .\make_shortcut.ps1 -Remove"
