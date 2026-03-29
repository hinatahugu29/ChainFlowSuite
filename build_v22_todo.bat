@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V22 - ToDo Only Build
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V22_Suite"

echo Start ToDo Build Process for V22 in: %PROJECT_ROOT%
echo Output Directory: %OUTPUT_DIR%
echo.

:: --- Clean Target ---
taskkill /F /T /IM ChainFlowToDo.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1

timeout /t 2 /nobreak >nul

if exist "%OUTPUT_DIR%\ChainFlowToDo" (
    echo [Clean] Removing old ChainFlowToDo...
    rmdir /s /q "%OUTPUT_DIR%\ChainFlowToDo"
)

:: Clean build/dist
if exist "%PROJECT_ROOT%ChainFlowToDo\dist" rmdir /s /q "%PROJECT_ROOT%ChainFlowToDo\dist"
if exist "%PROJECT_ROOT%ChainFlowToDo\build" rmdir /s /q "%PROJECT_ROOT%ChainFlowToDo\build"

:: --- Build ---
echo.
echo [1/1] Building ChainFlowToDo (Task Manager)...
copy /Y "%PROJECT_ROOT%ChainFlowFiler_v22\app_icon.ico" "%PROJECT_ROOT%ChainFlowToDo\app_icon.ico" >nul

cd /d "%PROJECT_ROOT%ChainFlowToDo"
py -m PyInstaller ChainFlowToDo.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR

:: --- Deploy ---
echo [Deploy] Copying ChainFlowToDo to V22 Suite...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
xcopy /E /I /Y /Q "dist\ChainFlowToDo" "%OUTPUT_DIR%\ChainFlowToDo"

echo.
echo ==========================================
echo  ToDo Build Completed Successfully!
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
