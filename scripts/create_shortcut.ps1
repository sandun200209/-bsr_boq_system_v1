param(
    [string]$ProjectDir = ""
)

if ([string]::IsNullOrWhiteSpace($ProjectDir)) {
    $ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "BSR Rate Hub.lnk"
$TargetPath = Join-Path $ProjectDir "start_windows.bat"
$IconPath = Join-Path $ProjectDir "assets\app_icon.ico"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $ProjectDir
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = "$IconPath,0"
}
$Shortcut.Description = "BSR Rate Hub - Sri Lanka BOQ Data System"
$Shortcut.Save()

Write-Host "[SUCCESS] Desktop shortcut created at: $ShortcutPath" -ForegroundColor Green
