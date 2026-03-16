@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 - PDF Studio Standalone Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite\Portable"

echo Start PDF Studio Standalone Build Process...
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowPDFStudio.exe >nul 2>&1
taskkill /F /T /IM ChainFlowPDFStudio_Portable.exe >nul 2>&1

:: --- Build ---
cd /d "%PROJECT_ROOT%ChainFlowPDFStudio"

:: Copy icon
copy /Y "%PROJECT_ROOT%app_icon.ico" "app_icon.ico" >nul

echo [1/1] Building ChainFlowPDFStudio_Portable.exe...
py -m PyInstaller --noconsole --onefile --name "ChainFlowPDFStudio_Portable" ^
    --icon "app_icon.ico" ^
    app\main.py --clean -y --log-level WARN

if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying to Portable folder...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
copy /Y "dist\ChainFlowPDFStudio_Portable.exe" "%OUTPUT_DIR%\ChainFlowPDFStudio_Portable.exe"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  PDF Studio Standalone Build Completed!
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
