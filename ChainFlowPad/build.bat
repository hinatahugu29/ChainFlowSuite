@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo  ChainFlowPad Build (PyInstaller onedir)
echo ==========================================
echo.

:: 1. Cleanup
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: 2. Run PyInstaller
echo [1/2] Compiling with PyInstaller...
py -m PyInstaller ChainFlowPad.spec --clean -y --log-level WARN
if %errorlevel% neq 0 (
    echo.
    echo [Error] Build Failed!
    pause
    exit /b %errorlevel%
)

:: 3. Finalize: Switch to Suite Style (Internal Folder + Launcher)
echo [2/2] Finalizing Suite Style...

:: Cleanup and Prepare Internal folder
if exist "Internal" rd /s /q "Internal"
if exist "dist\ChainFlowPad" (
    move "dist\ChainFlowPad" "Internal" >nul
)

:: Copy icon to Internal for window icon loading
if exist "..\app_icon.ico" (
    copy /y "..\app_icon.ico" "Internal\app_icon.ico" >nul
)

:: Create Friendly Batch Launcher at the root
(
echo @echo off
echo start "" "Internal\ChainFlowPad.exe"
) > "ChainFlowPad.bat"

:: Clean PyInstaller temporary folders
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"

:: --- Deploy to V23 Suite ---
set "V23_SUITE_DIR=..\ChainFlow_V23_Suite"
if exist "%V23_SUITE_DIR%" (
    echo [Deploy] Copying ChainFlowPad ^(Suite Style^) to V23 Suite...
    if exist "%V23_SUITE_DIR%\ChainFlowPad" rmdir /s /q "%V23_SUITE_DIR%\ChainFlowPad"
    mkdir "%V23_SUITE_DIR%\ChainFlowPad"
    xcopy /E /I /Y /Q "Internal" "%V23_SUITE_DIR%\ChainFlowPad\Internal" >nul
    copy /y "ChainFlowPad.bat" "%V23_SUITE_DIR%\ChainFlowPad\" >nul
)

echo.
echo ==========================================
echo  Build Completed! [SUITE STYLE]
echo  - Internal/ (All dependencies)
echo  - ChainFlowPad.bat (Launcher)
echo ==========================================
echo.
pause
