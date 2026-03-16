@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 - PDF Compare Standalone Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite\Portable"

echo Start PDF Compare Standalone Build Process...
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowPDFCompare_Portable.exe >nul 2>&1

:: ショートディレイ
timeout /t 2 /nobreak >nul

:: dist と build を事前に消す（競合回避のため個別名称でビルド）
if exist "%PROJECT_ROOT%ChainFlowPDFCompare\dist_portable" rmdir /s /q "%PROJECT_ROOT%ChainFlowPDFCompare\dist_portable"
if exist "%PROJECT_ROOT%ChainFlowPDFCompare\build_portable" rmdir /s /q "%PROJECT_ROOT%ChainFlowPDFCompare\build_portable"

:: --- Build ---
echo.
echo [1/1] Building Standalone EXE (Portable Version)...

:: Copy master icon
copy /Y "%PROJECT_ROOT%app_icon.ico" "%PROJECT_ROOT%ChainFlowPDFCompare\app_icon.ico" >nul

cd /d "%PROJECT_ROOT%ChainFlowPDFCompare"

:: Build as Portable Single EXE
py -m PyInstaller --noconsole --onefile --name "ChainFlowPDFCompare_Portable" ^
    --add-data "app;app" ^
    --add-data "app_icon.ico;." ^
    --icon "app_icon.ico" ^
    --distpath "dist_portable" ^
    --workpath "build_portable" ^
    main.py --clean -y --log-level WARN

if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying Standalone EXE to Suite/Portable...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

copy /Y "dist_portable\ChainFlowPDFCompare_Portable.exe" "%OUTPUT_DIR%\ChainFlowPDFCompare_Portable.exe"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
:: ChainFlow PDF Compare Portable Build Completed!
echo Destination: %OUTPUT_DIR%\ChainFlowPDFCompare_Portable.exe
echo ==========================================
echo.
pause
exit /b 0

:ERROR
echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo       PORTABLE BUILD FAILED
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
pause
exit /b 1
