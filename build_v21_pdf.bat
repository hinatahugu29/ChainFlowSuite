@echo off
setlocal
cd /d %~dp0

:: ==========================================
:: Build Script for ChainFlowPDFStudio (v21)
:: ==========================================

echo [INFO] Cleaning up previous build artifacts...
if exist "build\ChainFlowPDFStudio" rmdir /s /q "build\ChainFlowPDFStudio"
if exist "dist\ChainFlowPDFStudio" rmdir /s /q "dist\ChainFlowPDFStudio"

echo [INFO] Copying Master Icon from Suite Root...
if exist "app_icon.ico" (
    copy /y "app_icon.ico" "ChainFlowPDFStudio\app_icon.ico" >nul
    echo      - Icon copied to ChainFlowPDFStudio\app_icon.ico
) else (
    echo [WARN] Master icon 'app_icon.ico' not found in root. Skipping copy.
)

echo [INFO] Building ChainFlowPDFStudio...
cd ChainFlowPDFStudio
py -m PyInstaller --clean --noconfirm ChainFlowPDFStudio.spec
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed.
    pause
    exit /b %ERRORLEVEL%
)
cd ..

echo [INFO] Build Complete.

:: --- Deploy to Suite ---
set "OUTPUT_DIR=%~dp0ChainFlow_V21_Suite"
echo [INFO] Deploying to Suite: %OUTPUT_DIR%

if exist "%OUTPUT_DIR%\ChainFlowPDFStudio" (
    echo [INFO] Removing old version from Suite...
    rmdir /s /q "%OUTPUT_DIR%\ChainFlowPDFStudio"
)

echo [INFO] Copying new version...
xcopy /E /I /Y /Q "ChainFlowPDFStudio\dist\ChainFlowPDFStudio" "%OUTPUT_DIR%\ChainFlowPDFStudio"

echo [INFO] Deployment Complete.
pause
