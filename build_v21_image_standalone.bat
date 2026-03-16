@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 - Image Standalone Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite\Portable"

echo Start Image Standalone Build Process...
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowImage.exe >nul 2>&1
taskkill /F /T /IM ChainFlowImage_Portable.exe >nul 2>&1

:: --- Build ---
cd /d "%PROJECT_ROOT%ChainFlowImage"

:: Copy icon
copy /Y "%PROJECT_ROOT%ChainFlowFiler_v21\app_icon.ico" "app_icon.ico" >nul

echo [1/1] Building ChainFlowImage_Portable.exe...
py -m PyInstaller --noconsole --onefile --name "ChainFlowImage_Portable" ^
    --icon "app_icon.ico" ^
    image_tool.py --clean -y --log-level WARN

if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying to Portable folder...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
copy /Y "dist\ChainFlowImage_Portable.exe" "%OUTPUT_DIR%\ChainFlowImage_Portable.exe"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Image Standalone Build Completed!
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
