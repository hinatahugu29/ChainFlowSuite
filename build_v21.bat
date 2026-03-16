@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V21 Suite Build Script
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V21_Suite"
set "MASTER_ICON=%PROJECT_ROOT%app_icon.ico"

echo Start Build Process in: %PROJECT_ROOT%
echo Output Directory: %OUTPUT_DIR%
echo Master Icon: %MASTER_ICON%
echo.

:: --- Clean Start ---
echo [System] Terminating all ChainFlow processes...
taskkill /F /T /IM ChainFlowFiler.exe >nul 2>&1
taskkill /F /T /IM ChainFlowTool.exe >nul 2>&1
taskkill /F /T /IM ChainFlowImage.exe >nul 2>&1
taskkill /F /T /IM ChainFlowToDo.exe >nul 2>&1
taskkill /F /T /IM ChainFlowSearch.exe >nul 2>&1
taskkill /F /T /IM ChainFlowDesigner.exe >nul 2>&1
taskkill /F /T /IM ChainFlowPDFCompare.exe >nul 2>&1
taskkill /F /T /IM ChainFlowPDFStudio.exe >nul 2>&1
taskkill /F /T /IM ChainFlowWriter.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1
taskkill /F /T /IM QtWebEngineProcess.exe >nul 2>&1

:: Check if output directory is locked
if exist "%OUTPUT_DIR%" (
    echo [Check] Verifying output directory is not locked...
    ren "%OUTPUT_DIR%" "ChainFlow_V21_Suite_build_test" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ERROR: Output directory is currently locked by another process.
        echo Please close all ChainFlow apps or any folders/files inside:
        echo %OUTPUT_DIR%
        goto ERROR
    )
    :: Rename back so we can remove it properly
    ren "%OUTPUT_DIR%_build_test" "ChainFlow_V21_Suite" >nul 2>&1
    
    echo [Clean] Removing old output directory...
    rmdir /s /q "%OUTPUT_DIR%"
)
mkdir "%OUTPUT_DIR%"

:: Clean individual dist/build folders
echo [Clean] Scrubbing build artifacts...
for %%d in (ChainFlowFiler_v21 ChainFlowTool ChainFlowImage ChainFlowToDo ChainFlowSearch ChainFlowDesigner ChainFlowPDFCompare ChainFlowPDFStudio ChainFlowWriter) do (
    if exist "%%d\dist" rmdir /s /q "%%d\dist"
    if exist "%%d\dist_v21" rmdir /s /q "%%d\dist_v21"
    if exist "%%d\build" rmdir /s /q "%%d\build"
)

:: --- 1. ChainFlowFiler ---
echo.
echo [1/9] Building ChainFlowFiler (Main App)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowFiler_v21\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowFiler_v21"
py -m PyInstaller ChainFlowFiler_v21.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowFiler" "%OUTPUT_DIR%\ChainFlowFiler"

:: --- 2. ChainFlowTool ---
echo.
echo [2/9] Building ChainFlowTool (Viewer/Editor)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowTool\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowTool"
py -m PyInstaller ChainFlowTool.spec --clean -y --distpath dist --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowTool" "%OUTPUT_DIR%\ChainFlowTool"

:: --- 3. ChainFlowImage ---
echo.
echo [3/9] Building ChainFlowImage (Image Utility)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowImage\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowImage"
py -m PyInstaller ChainFlowImage.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowImage" "%OUTPUT_DIR%\ChainFlowImage"

:: --- 4. ChainFlowToDo ---
echo.
echo [4/9] Building ChainFlowToDo (Task Manager)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowToDo\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowToDo"
py -m PyInstaller ChainFlowToDo.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowToDo" "%OUTPUT_DIR%\ChainFlowToDo"

:: --- 5. ChainFlowSearch ---
echo.
echo [5/9] Building ChainFlowSearch (Search Tool)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowSearch\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowSearch"
py -m PyInstaller ChainFlowSearch.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowSearch" "%OUTPUT_DIR%\ChainFlowSearch"

:: --- 6. ChainFlowDesigner ---
echo.
echo [6/9] Building ChainFlowDesigner (DTP Editor)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowDesigner\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowDesigner"
py -m PyInstaller ChainFlowDesigner.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowDesigner" "%OUTPUT_DIR%\ChainFlowDesigner"

:: --- 7. ChainFlowPDFCompare ---
echo.
echo [7/9] Building ChainFlowPDFCompare (Side-by-Side Review)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowPDFCompare\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowPDFCompare"
py -m PyInstaller ChainFlowPDFCompare.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowPDFCompare" "%OUTPUT_DIR%\ChainFlowPDFCompare"

:: --- 8. ChainFlowPDFStudio ---
echo.
echo [8/9] Building ChainFlowPDFStudio (PDF Tools)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowPDFStudio\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowPDFStudio"
py -m PyInstaller ChainFlowPDFStudio.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowPDFStudio" "%OUTPUT_DIR%\ChainFlowPDFStudio"

:: --- 9. ChainFlowWriter ---
echo.
echo [9/9] Building ChainFlowWriter (Markdown Editor)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowWriter\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowWriter"
:: Build using PyInstaller with explicit settings
py -m PyInstaller --noconsole --name "ChainFlowWriter" ^
    --icon "app_icon.ico" ^
    --add-data "app_icon.ico;." ^
    main.py --clean -y --log-level WARN

if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowWriter" "%OUTPUT_DIR%\ChainFlowWriter"

:: ==========================================
:: Post-Build Cleanup (v21.1: Reduce file count and size)
:: ==========================================
echo.
echo [Cleanup] Removing unnecessary translation files for all apps...
for /d %%d in ("%OUTPUT_DIR%\*") do (
    :: Check for PySide6 translations in _internal directory (common in multi-file build)
    if exist "%%d\_internal\PySide6\translations" (
        pushd "%%d\_internal\PySide6\translations"
        for %%f in (*.*) do (
            echo %%~nf | findstr /i /b "qt_ja qt_en qtbase_ja qtbase_en" >nul
            if errorlevel 1 del /q "%%f" >nul 2>&1
        )
        popd
    )
)
echo [Cleanup] Done.

:: --- Finalize ---
echo.
echo ==========================================
echo  All 9 Apps Completed Successfully!
echo  Suite is ready at: %OUTPUT_DIR%
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
