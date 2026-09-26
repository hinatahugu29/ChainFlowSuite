@echo off
setlocal
cd /d "%~dp0"

echo Starting Nuitka compile...

if exist "build_nuitka" rd /s /q "build_nuitka"
mkdir "build_nuitka"

py -m nuitka --standalone --plugin-enable=pyside6 --include-data-file=app_icon.ico=app_icon.ico --include-data-file=tools.json=tools.json --windows-icon-from-ico=app_icon.ico --windows-console-mode=disable --lto=yes --nofollow-import-to=PIL --nofollow-import-to=cryptography --nofollow-import-to=tkinter --nofollow-import-to=unittest --nofollow-import-to=pydoc --output-dir=build_nuitka --assume-yes-for-downloads main.py

if %errorlevel% neq 0 (
    echo Nuitka build failed.
    exit /b 1
)

echo Packaging launcher...
if exist "build_nuitka\Internal" rd /s /q "build_nuitka\Internal"
rename "build_nuitka\main.dist" "Internal"

(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run "Internal\main.exe", 0, False
) > "build_nuitka\ChainFlowFiler.vbs"

(
echo @echo off
echo start "" "Internal\main.exe"
) > "build_nuitka\ChainFlowFiler.bat"

set "TARGET_SUITE="
if exist "..\ChainFlow_V23_Suite" (
    set "TARGET_SUITE=..\ChainFlow_V23_Suite"
) else (
    if exist "..\ChainFlow_V19_Suite" (
        set "TARGET_SUITE=..\ChainFlow_V19_Suite"
    )
)

if "%TARGET_SUITE%"=="" (
    echo Target Suite not found. Skipping copy.
    goto :FINALIZE
)

echo Copying ChainFlowFiler to %TARGET_SUITE%...
if exist "%TARGET_SUITE%\ChainFlowFiler" rmdir /s /q "%TARGET_SUITE%\ChainFlowFiler"
mkdir "%TARGET_SUITE%\ChainFlowFiler"

xcopy /E /I /Y /Q "build_nuitka\Internal" "%TARGET_SUITE%\ChainFlowFiler\Internal" >nul
copy /y "build_nuitka\ChainFlowFiler.vbs" "%TARGET_SUITE%\ChainFlowFiler\" >nul
copy /y "build_nuitka\ChainFlowFiler.bat" "%TARGET_SUITE%\ChainFlowFiler\" >nul

echo Done.

:FINALIZE
endlocal
