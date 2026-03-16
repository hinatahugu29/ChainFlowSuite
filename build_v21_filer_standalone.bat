@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 - Filer Standalone Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite\Portable"

echo Start Filer Standalone Build Process...
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowFiler.exe >nul 2>&1
taskkill /F /T /IM ChainFlowFiler_Portable.exe >nul 2>&1

:: --- Build ---
cd /d "%PROJECT_ROOT%ChainFlowFiler_v21"

:: Copy master icon
copy /Y "app_icon.ico" "app_icon.ico" >nul

echo [1/1] Building ChainFlowFiler_Portable.exe...
py -m PyInstaller --noconsole --onefile --name "ChainFlowFiler_Portable" ^
    --add-data "app_icon.ico;." ^
    --add-data "tools.json;." ^
    --icon "app_icon.ico" ^
    --hidden-import "pypdf" ^
    --hidden-import "ChainFlowDesigner" ^
    main.py --clean -y --log-level WARN

if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying to Portable folder...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
copy /Y "dist\ChainFlowFiler_Portable.exe" "%OUTPUT_DIR%\ChainFlowFiler_Portable.exe"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Filer Standalone Build Completed!
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
