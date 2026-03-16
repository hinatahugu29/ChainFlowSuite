@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 - PDF Compare Only Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite"

echo Start PDF Compare Build Process in: %PROJECT_ROOT%
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowPDFCompare.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1

:: プロセス終了とハンドル解放を待つための短い遅延
timeout /t 2 /nobreak >nul

if exist "%OUTPUT_DIR%\ChainFlowPDFCompare" (
    echo [Clean] Removing old ChainFlowPDFCompare...
    rmdir /s /q "%OUTPUT_DIR%\ChainFlowPDFCompare"
)

:: 強力なクリーンアップ: dist と build を事前に消す
if exist "%PROJECT_ROOT%ChainFlowPDFCompare\dist" rmdir /s /q "%PROJECT_ROOT%ChainFlowPDFCompare\dist"
if exist "%PROJECT_ROOT%ChainFlowPDFCompare\build" rmdir /s /q "%PROJECT_ROOT%ChainFlowPDFCompare\build"

:: --- Build ---
echo.
echo [1/1] Building ChainFlowPDFCompare (Advanced Multi-View PDF)...

:: Copy master icon
copy /Y "%PROJECT_ROOT%app_icon.ico" "%PROJECT_ROOT%ChainFlowPDFCompare\app_icon.ico" >nul

cd /d "%PROJECT_ROOT%ChainFlowPDFCompare"

:: Create PyInstaller spec or command
:: Using --noconsole for a GUI app
:: v21.1: Removed --onefile to align with suite structure (creating _internal folder)
:: v21.1: Using .spec file for consistent build settings (icon, data inclusions)
py -m PyInstaller ChainFlowPDFCompare.spec --clean -y --log-level WARN

if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying ChainFlowPDFCompare...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

:: v21.1: Copy the entire directory including _internal
if exist "%OUTPUT_DIR%\ChainFlowPDFCompare" rmdir /s /q "%OUTPUT_DIR%\ChainFlowPDFCompare"
xcopy /E /I /Y /Q "dist\ChainFlowPDFCompare" "%OUTPUT_DIR%\ChainFlowPDFCompare"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
:: ChainFlow PDF Compare Build Completed!
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
