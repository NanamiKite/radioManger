$ErrorActionPreference = 'Stop'
$packageDir = $PSScriptRoot
$desktopLauncher = Join-Path $packageDir 'RadioManager.vbs'
$webLauncher = Join-Path $packageDir 'start.bat'
$iconPath = Join-Path $packageDir 'backend\frontend_dist\favicon.ico'

if (Test-Path $desktopLauncher) {
    $launcher = $desktopLauncher
} elseif (Test-Path $webLauncher) {
    $launcher = $webLauncher
} else {
    throw 'Run this script from an extracted RadioManager release package.'
}
if (-not (Test-Path $iconPath)) {
    throw "Application icon not found: $iconPath"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $packageDir 'RadioManager.lnk'))
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $packageDir
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = 'RadioManager - Amateur Radio QSO Log'
$shortcut.Save()
Write-Host 'Created RadioManager.lnk. Keep the extracted folder in place; you can copy the shortcut to your desktop.'
