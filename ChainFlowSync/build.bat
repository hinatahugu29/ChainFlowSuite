@echo off
setlocal
echo ==========================================
echo  ChainFlowSync Production Build v0.1
echo ==========================================
echo.

:: 1. Build Rust Engine
echo [1/3] Building Rust Sync Engine (Release)...
cd /d "%~dp0engine"
cargo build --release
if %errorlevel% neq 0 (
    echo Rust Build Failed!
    pause
    exit /b %errorlevel%
)
cd /d "%~dp0"

:: 2. Ensure icon is present
if not exist "%~dp0app_icon.ico" (
    echo [Warning] app_icon.ico not found. Using default icon.
)

:: 3. Run PyInstaller
echo.
echo [2/3] Bundling with PyInstaller...
:: Clean old build/dist
if exist "%~dp0build" rmdir /s /q "%~dp0build"
if exist "%~dp0dist" rmdir /s /q "%~dp0dist"

py -m PyInstaller "%~dp0ChainFlowSync.spec" --clean -y --log-level WARN
if %errorlevel% neq 0 (
    echo PyInstaller Build Failed!
    pause
    exit /b %errorlevel%
)

:: 4. Finalize
echo.
echo [3/3] Finalizing...
echo Output is ready at: dist\ChainFlowSync
echo.
echo ==========================================
echo  Build Completed Successfully!
echo ==========================================
pause
