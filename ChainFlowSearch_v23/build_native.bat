@echo off
setlocal enabledelayedexpansion

:: 1. Go to script directory
cd /d "%~dp0"

echo Building Native Search Core (Rust/PyO3) v23...

:: 2. Enter native folder
cd native
if %ERRORLEVEL% neq 0 (
    echo [ERROR] native folder not found.
    pause
    exit /b 1
)

:: 3. Maturin build
maturin build --release --interpreter python

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Maturin build failed.
    pause
    exit /b %ERRORLEVEL%
)

:: 4. Copy artifact to root
echo Finalizing native module...

for /r "target" %%f in (*chainflow_search_core*.pyd) do (
    copy /y "%%f" "..\chainflow_search_core.pyd" > nul
    echo [OK] %%~nxf copied.
)

if not exist "..\chainflow_search_core.pyd" (
    echo [ERROR] .pyd file could not be located.
)

echo Native Search Engine Build Complete.
pause
