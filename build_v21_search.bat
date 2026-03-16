@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 - Search Only Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite"

echo Start Search Build Process in: %PROJECT_ROOT%
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowSearch.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1
taskkill /F /T /IM QtWebEngineProcess.exe >nul 2>&1

:: プロセス終了とハンドル解放を待つための短い遅延
timeout /t 2 /nobreak >nul

if exist "%OUTPUT_DIR%\ChainFlowSearch" (
    echo [Clean] Removing old ChainFlowSearch...
    rmdir /s /q "%OUTPUT_DIR%\ChainFlowSearch"
)

:: 強力なクリーンアップ: dist と build を事前に消す
if exist "%PROJECT_ROOT%ChainFlowSearch\dist" rmdir /s /q "%PROJECT_ROOT%ChainFlowSearch\dist"
if exist "%PROJECT_ROOT%ChainFlowSearch\dist_v21" rmdir /s /q "%PROJECT_ROOT%ChainFlowSearch\dist_v21"
if exist "%PROJECT_ROOT%ChainFlowSearch\build" rmdir /s /q "%PROJECT_ROOT%ChainFlowSearch\build"

:: --- Build ---
echo.
echo [1/1] Building ChainFlowSearch (Search Tool)...
:: Copy master icon from Filer
copy /Y "%PROJECT_ROOT%ChainFlowFiler_v21\app_icon.ico" "%PROJECT_ROOT%ChainFlowSearch\app_icon.ico" >nul

cd /d "%PROJECT_ROOT%ChainFlowSearch"
py -m PyInstaller ChainFlowSearch.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying ChainFlowSearch...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
xcopy /E /I /Y /Q "dist\ChainFlowSearch" "%OUTPUT_DIR%\ChainFlowSearch"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Search Build Completed Successfully!
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
