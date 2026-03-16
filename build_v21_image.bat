@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 - Image Only Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite"

echo Start Image Build Process in: %PROJECT_ROOT%
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowImage.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1

:: プロセス終了とハンドル解放を待つための短い遅延
timeout /t 2 /nobreak >nul

if exist "%OUTPUT_DIR%\ChainFlowImage" (
    echo [Clean] Removing old ChainFlowImage...
    rmdir /s /q "%OUTPUT_DIR%\ChainFlowImage"
)

:: 強力なクリーンアップ: dist と build を事前に消す
if exist "%PROJECT_ROOT%ChainFlowImage\dist" rmdir /s /q "%PROJECT_ROOT%ChainFlowImage\dist"
if exist "%PROJECT_ROOT%ChainFlowImage\dist_v21" rmdir /s /q "%PROJECT_ROOT%ChainFlowImage\dist_v21"
if exist "%PROJECT_ROOT%ChainFlowImage\build" rmdir /s /q "%PROJECT_ROOT%ChainFlowImage\build"

:: --- Build ---
echo.
echo [1/1] Building ChainFlowImage (Image Utility)...
:: Copy master icon from Filer
copy /Y "%PROJECT_ROOT%ChainFlowFiler_v21\app_icon.ico" "%PROJECT_ROOT%ChainFlowImage\app_icon.ico" >nul

cd /d "%PROJECT_ROOT%ChainFlowImage"
py -m PyInstaller ChainFlowImage.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying ChainFlowImage...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
xcopy /E /I /Y /Q "dist\ChainFlowImage" "%OUTPUT_DIR%\ChainFlowImage"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Image Build Completed Successfully!
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
