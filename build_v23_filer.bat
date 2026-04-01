@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V23 - Filer Onedir Build (with Native Core)
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V23_Suite"

echo Start Filer v23 Onedir Build Process...
echo [Hybrid Native Edition: Python + Rust Engine]
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowFiler.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1

:: --- Build ---
cd /d "%PROJECT_ROOT%ChainFlowFiler_v23"

:: Ensure Native Engine exists
if not exist "chainflow_core.pyd" (
    echo [ERROR] chainflow_core.pyd not found in project root! 
    echo Please run build_native.bat FIRST.
    pause
    exit /b 1
)

echo.
echo [1/1] Building ChainFlowFiler (Main App Directory)...
py -m PyInstaller ChainFlowFiler_v23.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying ChainFlowFiler_v23...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
if exist "%OUTPUT_DIR%\ChainFlowFiler_v23" rmdir /s /q "%OUTPUT_DIR%\ChainFlowFiler_v23"
xcopy /E /I /Y /Q "dist\ChainFlowFiler" "%OUTPUT_DIR%\ChainFlowFiler_v23"

if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo  Filer V23 Build Completed Successfully!
echo  (Includes _internal folder and Native Core)
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
