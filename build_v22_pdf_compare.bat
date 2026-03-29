@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V22 - PDF Compare Only Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V22_Suite"

echo Start PDF Compare Build Process for V22 in: %PROJECT_ROOT%
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowPDFCompare.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1

timeout /t 2 /nobreak >nul

if exist "%OUTPUT_DIR%\ChainFlowPDFCompare" (
    echo [Clean] Removing old ChainFlowPDFCompare...
    rmdir /s /q "%OUTPUT_DIR%\ChainFlowPDFCompare"
)

:: Clean build/dist
if exist "%PROJECT_ROOT%ChainFlowPDFCompare\dist" rmdir /s /q "%PROJECT_ROOT%ChainFlowPDFCompare\dist"
if exist "%PROJECT_ROOT%ChainFlowPDFCompare\build" rmdir /s /q "%PROJECT_ROOT%ChainFlowPDFCompare\build"

:: --- Build ---
echo.
echo [1/1] Building ChainFlowPDFCompare (Visual Diff Tool)...
copy /Y "%PROJECT_ROOT%ChainFlowFiler_v22\app_icon.ico" "%PROJECT_ROOT%ChainFlowPDFCompare\app_icon.ico" >nul

cd /d "%PROJECT_ROOT%ChainFlowPDFCompare"
py -m PyInstaller ChainFlowPDFCompare.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying ChainFlowPDFCompare to V22 Suite...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
xcopy /E /I /Y /Q "dist\ChainFlowPDFCompare" "%OUTPUT_DIR%\ChainFlowPDFCompare"

echo.
echo ==========================================
echo  PDF Compare Build Completed Successfully!
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
