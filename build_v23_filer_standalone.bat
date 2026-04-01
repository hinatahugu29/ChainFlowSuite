@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V23 - Filer Standalone Build (Hybrid Native)
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V23_Suite\Portable"

echo Start Filer V23 Standalone Build Process...
echo [Hybrid Native Edition: Python + Rust]
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowFiler.exe >nul 2>&1
taskkill /F /T /IM ChainFlowFiler_Portable.exe >nul 2>&1

:: --- Build ---
cd /d "%PROJECT_ROOT%ChainFlowFiler_v23"

:: Ensure Native Engine exists
if not exist "chainflow_core.pyd" (
    echo [ERROR] chainflow_core.pyd not found! 
    echo Please run build_native.bat first.
    pause
    exit /b 1
)

echo [1/1] Building ChainFlowFiler_V23_Portable.exe...
py -m PyInstaller --noconsole --onefile --name "ChainFlowFiler_V23" ^
    --add-data "app_icon.ico;." ^
    --add-data "tools.json;." ^
    --add-data "chainflow_core.pyd;." ^
    --icon "app_icon.ico" ^
    --hidden-import "pypdf" ^
    --hidden-import "ChainFlowDesigner" ^
    main.py --clean -y --log-level WARN

if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying to Portable folder...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
copy /Y "dist\ChainFlowFiler_V23.exe" "%OUTPUT_DIR%\ChainFlowFiler_V23.exe"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Filer V23 Standalone Build Completed!
echo  (Native Rust Core Integrated)
echo ==========================================
echo.
pause
exit /b 0

:ERROR
echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo       BUILD FAILED
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
pause
exit /b 1
