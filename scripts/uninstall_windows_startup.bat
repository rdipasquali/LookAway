@echo off
REM LookAway Windows Uninstall Script

echo Removing LookAway from Windows startup...

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_DIR%\LookAway.lnk"

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    if not exist "%SHORTCUT_PATH%" (
        echo Successfully removed LookAway from startup!
    ) else (
        echo Failed to remove startup shortcut. You may need Administrator privileges.
    )
) else (
    echo LookAway startup shortcut not found.
)

pause