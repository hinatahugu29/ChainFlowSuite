@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 - Writer Standalone Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "SOURCE_DIR=%PROJECT_ROOT%ChainFlowWriter_v8"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite"
set "APP_ICON=%PROJECT_ROOT%app_icon.ico"

echo Start Writer Standalone Build Process (v21.1)...
echo Source: %SOURCE_DIR%
echo Target: %OUTPUT_DIR%\ChainFlowWriter_Portable.exe
echo.

:: --- Clean Target ---
echo [Check] Terminating existing processes...
taskkill /F /T /IM ChainFlowWriter_Portable.exe >nul 2>&1
timeout /t 1 /nobreak >nul

:: --- Build ---
cd /d "%SOURCE_DIR%"

echo [1/1] Building ChainFlowWriter_Portable.exe (One-file)...
echo (This may take several minutes due to WebEngine compression)
py -m PyInstaller --noconsole --onefile --name "ChainFlowWriter_Portable" ^
    --icon "%APP_ICON%" ^
    --add-data "%APP_ICON%;." ^
    main.py --clean -y --log-level WARN

if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying to Suite folder...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
copy /Y "dist\ChainFlowWriter_Portable.exe" "%OUTPUT_DIR%\ChainFlowWriter_Portable.exe"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Writer Standalone Build Completed!
echo  Location: %OUTPUT_DIR%\ChainFlowWriter_Portable.exe
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
