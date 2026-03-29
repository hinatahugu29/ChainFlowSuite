@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V22 - Designer Only Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V22_Suite"

echo Start Designer Build Process for V22 in: %PROJECT_ROOT%
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowDesigner.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1
taskkill /F /T /IM QtWebEngineProcess.exe >nul 2>&1

timeout /t 2 /nobreak >nul

if exist "%OUTPUT_DIR%\ChainFlowDesigner" (
    echo [Clean] Removing old ChainFlowDesigner...
    rmdir /s /q "%OUTPUT_DIR%\ChainFlowDesigner"
)

:: Clean build/dist in local folder
if exist "%PROJECT_ROOT%ChainFlowDesigner\dist" rmdir /s /q "%PROJECT_ROOT%ChainFlowDesigner\dist"
if exist "%PROJECT_ROOT%ChainFlowDesigner\build" rmdir /s /q "%PROJECT_ROOT%ChainFlowDesigner\build"

:: --- Build ---
echo.
echo [1/1] Building ChainFlowDesigner (DTP Editor)...
copy /Y "%PROJECT_ROOT%ChainFlowFiler_v22\app_icon.ico" "%PROJECT_ROOT%ChainFlowDesigner\app_icon.ico" >nul

cd /d "%PROJECT_ROOT%ChainFlowDesigner"
py -m PyInstaller ChainFlowDesigner.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying ChainFlowDesigner to V22 Suite...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
xcopy /E /I /Y /Q "dist\ChainFlowDesigner" "%OUTPUT_DIR%\ChainFlowDesigner"

echo.
echo ==========================================
echo  Designer Build Completed Successfully!
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
