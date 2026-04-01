@echo off
setlocal
cd /d "%~dp0native"
echo Building Native Core (Rust/PyO3) v23.2...
:: v23.2: Add --interpreter py to explicitly use the py launcher
py -m maturin build --release --interpreter py
if %errorlevel% neq 0 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Finalizing native module...
:: Find dll/pyd and copy to root
if exist "target\release\chainflow_core.dll" (
    copy /y "target\release\chainflow_core.dll" "..\chainflow_core.pyd" >nul
    copy /y "target\release\chainflow_core.dll" "target\release\chainflow_core.pyd" >nul
)

echo Native Core Build Complete.
echo [V23.2] Native Engine is now READY in the project root.
pause
