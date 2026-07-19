@echo off
cd /d "%~dp0"

echo ============================================
echo   Building PC Telemetry
echo ============================================
echo   Working folder: %cd%
echo.

echo [1/4] Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: pip install -r requirements.txt failed. See above.
    pause
    exit /b 1
)

python -m pip install pyinstaller
if errorlevel 1 (
    echo.
    echo ERROR: pip install pyinstaller failed. See above.
    pause
    exit /b 1
)

echo.
echo [2/4] Building TelemetriaPC.exe (console version, for debugging)...
python -m PyInstaller --onefile --name TelemetriaPC --add-data "static;static" --collect-all uvicorn --collect-all fastapi --collect-all starlette --console server.py
if errorlevel 1 (
    echo.
    echo ============================================
    echo   BUILD FAILED on TelemetriaPC.exe - see above
    echo ============================================
    pause
    exit /b 1
)

echo.
echo [3/4] Building TelemetriaPCTray.exe (background, system tray, no console)...
python -m PyInstaller --onefile --name TelemetriaPCTray --add-data "static;static" --collect-all uvicorn --collect-all fastapi --collect-all starlette --collect-all pystray --windowed tray_app.py
if errorlevel 1 (
    echo.
    echo ============================================
    echo   BUILD FAILED on TelemetriaPCTray.exe - see above
    echo ============================================
    pause
    exit /b 1
)

echo.
echo [4/4] Done! Checking dist folder...
echo.
if exist dist\TelemetriaPC.exe (
    echo   Console version: %cd%\dist\TelemetriaPC.exe
) else (
    echo   WARNING: dist\TelemetriaPC.exe not found.
)
if exist dist\TelemetriaPCTray.exe (
    echo   Tray version:    %cd%\dist\TelemetriaPCTray.exe   ^<- use this one day-to-day
) else (
    echo   WARNING: dist\TelemetriaPCTray.exe not found.
)
echo.
echo NOTE: Windows Defender / SmartScreen may flag these .exe files on
echo first run (common with unsigned PyInstaller executables). Choose
echo "More info" -^> "Run anyway". See README.md for details.
echo.
pause
