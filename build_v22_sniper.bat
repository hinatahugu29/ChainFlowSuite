@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V22 - Sniper Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V22_Suite"

echo Start Sniper Build Process in: %PROJECT_ROOT%
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowSniper.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1
taskkill /F /T /IM QtWebEngineProcess.exe >nul 2>&1

:: Delay to release handles
timeout /t 2 /nobreak >nul

if exist "%OUTPUT_DIR%\ChainFlowSniper" (
    echo [Clean] Removing old ChainFlowSniper...
    rmdir /s /q "%OUTPUT_DIR%\ChainFlowSniper"
)

:: Cleanup: dist and build
if exist "%PROJECT_ROOT%ChainFlowSniper_V3\dist" rmdir /s /q "%PROJECT_ROOT%ChainFlowSniper_V3\dist"
if exist "%PROJECT_ROOT%ChainFlowSniper_V3\build" rmdir /s /q "%PROJECT_ROOT%ChainFlowSniper_V3\build"

:: --- Build ---
echo.
echo [1/1] Building ChainFlowSniper_V3...
:: Copy master icon from Filer v22 to Sniper dir for PyInstaller
copy /Y "%PROJECT_ROOT%ChainFlowFiler_v22\app_icon.ico" "%PROJECT_ROOT%ChainFlowSniper_V3\app_icon.ico" >nul

cd /d "%PROJECT_ROOT%ChainFlowSniper_V3"
py -m PyInstaller ChainFlowSniper.spec --clean -y --log-level INFO
if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying ChainFlowSniper...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
xcopy /E /I /Y /Q "dist\ChainFlowSniper" "%OUTPUT_DIR%\ChainFlowSniper"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Sniper Build Completed Successfully!
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
