@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 - Tool Only Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite"

echo Start Tool Build Process in: %PROJECT_ROOT%
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowTool.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1
taskkill /F /T /IM QtWebEngineProcess.exe >nul 2>&1

:: プロセス終了とハンドル解放を待つための短い遅延
timeout /t 2 /nobreak >nul

if exist "%OUTPUT_DIR%\ChainFlowTool" (
    echo [Clean] Removing old ChainFlowTool...
    rmdir /s /q "%OUTPUT_DIR%\ChainFlowTool"
)

:: 強力なクリーンアップ: dist と build を事前に消す
if exist "%PROJECT_ROOT%ChainFlowTool\dist" rmdir /s /q "%PROJECT_ROOT%ChainFlowTool\dist"
if exist "%PROJECT_ROOT%ChainFlowTool\dist_v21" rmdir /s /q "%PROJECT_ROOT%ChainFlowTool\dist_v21"
if exist "%PROJECT_ROOT%ChainFlowTool\build" rmdir /s /q "%PROJECT_ROOT%ChainFlowTool\build"

:: --- Build ---
echo.
echo [1/1] Building ChainFlowTool (Viewer/Editor)...
:: Copy master icon from Filer
copy /Y "%PROJECT_ROOT%ChainFlowFiler_v21\app_icon.ico" "%PROJECT_ROOT%ChainFlowTool\app_icon.ico" >nul

cd /d "%PROJECT_ROOT%ChainFlowTool"
py -m PyInstaller ChainFlowTool.spec --clean -y --distpath dist_v21 --log-level WARN
if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying ChainFlowTool...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
xcopy /E /I /Y /Q "dist_v21\ChainFlowTool" "%OUTPUT_DIR%\ChainFlowTool"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Tool Build Completed Successfully!
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
