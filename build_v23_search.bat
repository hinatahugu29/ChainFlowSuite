@echo off
setlocal

echo Packaging ChainFlowSearch V23 (Hybrid Native)...

:: Check for native core
if not exist "ChainFlowSearch_v23\chainflow_search_core.pyd" (
    echo [ERROR] Native core not found. Please run build_native.bat first.
    pause
    exit /b 1
)

:: Run PyInstaller
:: --onedir: creates a folder with an EXE (fastest startup)
:: --add-data: include the native pyd in the root
:: --noconsole: windows app mode
pyinstaller --noconfirm --onedir --windowed ^
    --name "ChainFlowSearch_v23" ^
    --distpath "ChainFlow_V23_Suite" ^
    --icon "ChainFlowSearch_v23/app_icon.ico" ^
    --add-data "ChainFlowSearch_v23/chainflow_search_core.pyd;." ^
    --add-data "ChainFlowSearch_v23/app_icon.ico;." ^
    "ChainFlowSearch_v23/main.py"

if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] ChainFlowSearch V23 is ready in dist/ChainFlowSearch_v23/
) else (
    echo [ERROR] Packaging failed.
)

pause
