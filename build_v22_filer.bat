@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V22 - Filer Only Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V22_Suite"

echo Start Filer Build Process in: %PROJECT_ROOT%
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowFiler.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1
taskkill /F /T /IM QtWebEngineProcess.exe >nul 2>&1

:: プロセス終了とハンドル解放を待つための短い遅延
timeout /t 2 /nobreak >nul

if exist "%OUTPUT_DIR%\ChainFlowFiler" (
    echo [Clean] Removing old ChainFlowFiler...
    rmdir /s /q "%OUTPUT_DIR%\ChainFlowFiler"
)

:: 強力なクリーンアップ: dist と build を事前に消す
if exist "%PROJECT_ROOT%ChainFlowFiler_v22\dist" rmdir /s /q "%PROJECT_ROOT%ChainFlowFiler_v22\dist"
if exist "%PROJECT_ROOT%ChainFlowFiler_v22\dist_v22" rmdir /s /q "%PROJECT_ROOT%ChainFlowFiler_v22\dist_v22"
if exist "%PROJECT_ROOT%ChainFlowFiler_v22\build" rmdir /s /q "%PROJECT_ROOT%ChainFlowFiler_v22\build"

:: --- Build ---
echo.
echo [1/1] Building ChainFlowFiler (Main App)...
cd /d "%PROJECT_ROOT%ChainFlowFiler_v22"
py -m PyInstaller ChainFlowFiler_v22.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying ChainFlowFiler...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
xcopy /E /I /Y /Q "dist\ChainFlowFiler" "%OUTPUT_DIR%\ChainFlowFiler"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Filer Build Completed Successfully!
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
