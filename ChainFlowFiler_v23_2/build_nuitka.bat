@echo off
setlocal
cd /d "%~dp0"

echo Building Deep Compiled v23.2 with Nuitka...
echo [Notice] This process takes several minutes as it converts Python to C.

:: Ensure build directory exists
if not exist "build_nuitka" mkdir "build_nuitka"

py -m nuitka ^
    --standalone ^
    --plugin-enable=pyside6 ^
    --include-data-file=app_icon.ico=app_icon.ico ^
    --include-data-file=tools.json=tools.json ^
    --windows-icon-from-ico=app_icon.ico ^
    --windows-console-mode=disable ^
    --lto=yes ^
    --output-dir=build_nuitka ^
    --assume-yes-for-downloads ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo Nuitka build failed. Please ensure 'nuitka' and 'zstandard' are installed:
    echo py -m pip install nuitka zstandard
    pause
    exit /b 1
)

echo.
echo Finalizing Suite-style distribution...

:: Rename the .dist folder to 'Internal' inside build_nuitka
if exist "build_nuitka\Internal" rd /s /q "build_nuitka\Internal"
rename "build_nuitka\main.dist" "Internal"

:: Create the SLEEK VBScript Launcher at the root of build_nuitka
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run "Internal\main.exe", 0, False
) > "build_nuitka\ChainFlowFiler_V23.2.vbs"

:: Create a Friendly Batch Launcher as backup
(
echo @echo off
echo start "" "Internal\main.exe"
) > "build_nuitka\ChainFlowFiler_V23.2.bat"

echo.
echo ----------------------------------------------------
echo Build Successful! [SUITE STYLE]
echo Distribution is ready in: build_nuitka\
echo - Internal/ (All dependencies)
echo - ChainFlowFiler_V23.2.vbs (Launcher - NO CONSOLE)
echo - ChainFlowFiler_V23.2.bat (Launcher - Standard)
echo ----------------------------------------------------
pause
