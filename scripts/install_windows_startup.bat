@echo off
REM LookAway Windows Startup Script
REM This script installs LookAway to run automatically at Windows startup

echo Installing LookAway to Windows startup...

REM Get the current directory
set "LOOKAWAY_DIR=%~dp0"
set "LOOKAWAY_DIR=%LOOKAWAY_DIR:~0,-1%"

REM Create startup shortcut
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_DIR%\LookAway.lnk"

REM Create VBS script to create shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\createShortcut.vbs"
echo sLinkFile = "%SHORTCUT_PATH%" >> "%TEMP%\createShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\createShortcut.vbs"
echo oLink.TargetPath = "python.exe" >> "%TEMP%\createShortcut.vbs"
echo oLink.Arguments = """%LOOKAWAY_DIR%\main.py"" start" >> "%TEMP%\createShortcut.vbs"
echo oLink.WorkingDirectory = "%LOOKAWAY_DIR%" >> "%TEMP%\createShortcut.vbs"
echo oLink.Description = "LookAway Eye Break Reminder" >> "%TEMP%\createShortcut.vbs"
echo oLink.Save >> "%TEMP%\createShortcut.vbs"

REM Execute VBS script
cscript //nologo "%TEMP%\createShortcut.vbs"

REM Clean up
del "%TEMP%\createShortcut.vbs"

if exist "%SHORTCUT_PATH%" (
    echo Successfully installed LookAway to startup!
    echo LookAway will start automatically when Windows starts.
    echo.
    echo To remove from startup, delete: %SHORTCUT_PATH%
) else (
    echo Failed to install startup shortcut.
    echo You may need to run this script as Administrator.
)

pause