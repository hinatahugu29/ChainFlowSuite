@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V22 - Tool Standalone Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V22_Suite\Portable"

echo Start Tool Standalone Build Process (V22)...
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowTool.exe >nul 2>&1
taskkill /F /T /IM ChainFlowTool_Portable.exe >nul 2>&1

:: --- Build ---
cd /d "%PROJECT_ROOT%ChainFlowTool"

:: Copy icon from Filer v22
copy /Y "%PROJECT_ROOT%ChainFlowFiler_v22\app_icon.ico" "app_icon.ico" >nul

echo [1/1] Building ChainFlowTool_Portable.exe...
py -m PyInstaller --noconsole --onefile --name "ChainFlowTool_Portable" ^
    --icon "app_icon.ico" ^
    editor.py --clean -y --log-level WARN

if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying to V22 Portable folder...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
copy /Y "dist\ChainFlowTool_Portable.exe" "%OUTPUT_DIR%\ChainFlowTool_Portable.exe"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Tool Standalone Build Completed!
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
