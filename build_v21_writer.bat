@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 - Writer Build (Non-Standalone)
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "SOURCE_DIR=%PROJECT_ROOT%ChainFlowWriter_v7"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite"
set "APP_ICON=%PROJECT_ROOT%app_icon.ico"

echo Start Writer Build Process (v21.1)...
echo Source: %SOURCE_DIR%
echo Output: %OUTPUT_DIR%\ChainFlowWriter
echo.

:: --- Clean Target ---
echo [Check] Terminating existing processes...
taskkill /F /T /IM ChainFlowWriter.exe >nul 2>&1
timeout /t 1 /nobreak >nul

:: Check if directory is locked
if exist "%OUTPUT_DIR%\ChainFlowWriter" (
    ren "%OUTPUT_DIR%\ChainFlowWriter" "ChainFlowWriter_build_test" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ERROR: Output directory is currently locked.
        echo Please close ChainFlowWriter or any open folders inside it.
        goto ERROR
    )
    ren "%OUTPUT_DIR%\ChainFlowWriter_build_test" "ChainFlowWriter" >nul 2>&1
)

:: --- Build ---
cd /d "%SOURCE_DIR%"

echo [1/1] Building ChainFlowWriter (Multi-file)...
py -m PyInstaller --noconsole --name "ChainFlowWriter" ^
    --icon "%APP_ICON%" ^
    --add-data "%APP_ICON%;." ^
    main.py --clean -y --log-level WARN

if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying to Suite folder...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
if exist "%OUTPUT_DIR%\ChainFlowWriter" rmdir /s /q "%OUTPUT_DIR%\ChainFlowWriter"
xcopy /E /I /Y /Q "dist\ChainFlowWriter" "%OUTPUT_DIR%\ChainFlowWriter"
if errorlevel 1 goto ERROR

:: --- Cleanup Translations (v21.1 Size Optimization) ---
echo [Cleanup] Removing unnecessary translation files...
set "TRANS_DIR=%OUTPUT_DIR%\ChainFlowWriter\_internal\PySide6\translations"
if exist "%TRANS_DIR%" (
    pushd "%TRANS_DIR%"
    for %%f in (*.*) do (
        echo %%~nf | findstr /i /b "qt_ja qt_en qtbase_ja qtbase_en" >nul
        if errorlevel 1 del /q "%%f" >nul 2>&1
    )
    popd
)

echo.
echo ==========================================
echo  Writer Build Completed!
echo  Location: %OUTPUT_DIR%\ChainFlowWriter
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
