<#
    ساخت میان‌بر دسکتاپ برای اجرای تایپ صوتی
    Create a desktop shortcut for the voice typing app.

    اجرا در پوشه پروژه:
        powershell -ExecutionPolicy Bypass -File make_shortcut.ps1
#>

param(
    [string]$Name = "Voice Typing",
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppPath = Join-Path $ProjectDir "app.py"
$IconPath = Join-Path $ProjectDir "icon.ico"

function Get-PythonPath {
    $candidates = @()
    foreach ($c in @("py", "python", "python3")) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd) { $candidates += $cmd.Source }
    }
    if (-not $candidates) {
        throw "هیچ مفسر پایتونی پیدا نشد. پایتون را نصب کنید یا با -PythonPath مشخص کنید."
    }
    return $candidates[0]
}

# --- حذف میان‌بر ---
if ($Remove) {
    $lnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "$Name.lnk"
    if (Test-Path $lnk) {
        Remove-Item $lnk -Force
        Write-Host "میان‌بر حذف شد: $lnk" -ForegroundColor Yellow
    } else {
        Write-Host "میان‌بری با این نام پیدا نشد."
    }
    return
}

# --- بررسی وجود برنامه ---
if (-not (Test-Path $AppPath)) {
    throw "app.py پیدا نشد: $AppPath"
}

$python = Get-PythonPath
Write-Host "پایتون: $python"

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
Write-Host "میان‌بر ساخته شد: $shortcutPath" -ForegroundColor Green
Write-Host "برای حذف:  .\make_shortcut.ps1 -Remove"
