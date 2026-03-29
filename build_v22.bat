@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: ChainFlow V22 Suite Build Script
:: ==========================================

set "PROJECT_ROOT=%~dp0"
set "OUTPUT_DIR=%PROJECT_ROOT%ChainFlow_V22_Suite"
set "MASTER_ICON=%PROJECT_ROOT%app_icon.ico"

echo Start Build Process for V22 Suite in: %PROJECT_ROOT%
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
taskkill /F /T /IM ChainFlowSniper.exe >nul 2>&1
taskkill /F /T /IM python.exe >nul 2>&1
taskkill /F /T /IM QtWebEngineProcess.exe >nul 2>&1

:: Check if output directory is locked
if exist "%OUTPUT_DIR%" (
    echo [Check] Verifying output directory is not locked...
    ren "%OUTPUT_DIR%" "ChainFlow_V22_Suite_build_test" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ERROR: Output directory is currently locked by another process.
        echo Please close all ChainFlow apps or any folders/files inside:
        echo %OUTPUT_DIR%
        goto ERROR
    )
    :: Rename back so we can remove it properly
    ren "%OUTPUT_DIR%_build_test" "ChainFlow_V22_Suite" >nul 2>&1
    
    echo [Clean] Removing old output directory...
    rmdir /s /q "%OUTPUT_DIR%"
)
mkdir "%OUTPUT_DIR%"

:: Clean individual dist/build folders
echo [Clean] Scrubbing build artifacts...
for %%d in (ChainFlowFiler_v22 ChainFlowTool ChainFlowImage ChainFlowToDo ChainFlowSearch ChainFlowDesigner ChainFlowPDFCompare ChainFlowPDFStudio ChainFlowWriter_v9 ChainFlowSniper_V3) do (
    if exist "%%d\dist" rmdir /s /q "%%d\dist"
    if exist "%%d\build" rmdir /s /q "%%d\build"
)

:: --- 1. ChainFlowFiler (v22) ---
echo.
echo [1/10] Building ChainFlowFiler (Main Hub v22)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowFiler_v22\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowFiler_v22"
py -m PyInstaller ChainFlowFiler_v22.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowFiler" "%OUTPUT_DIR%\ChainFlowFiler"

:: --- 2. ChainFlowTool ---
echo.
echo [2/10] Building ChainFlowTool (Viewer/Editor)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowTool\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowTool"
py -m PyInstaller ChainFlowTool.spec --clean -y --distpath dist --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowTool" "%OUTPUT_DIR%\ChainFlowTool"

:: --- 3. ChainFlowImage ---
echo.
echo [3/10] Building ChainFlowImage (Image Utility)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowImage\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowImage"
py -m PyInstaller ChainFlowImage.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowImage" "%OUTPUT_DIR%\ChainFlowImage"

:: --- 4. ChainFlowToDo ---
echo.
echo [4/10] Building ChainFlowToDo (Task Manager)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowToDo\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowToDo"
py -m PyInstaller ChainFlowToDo.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowToDo" "%OUTPUT_DIR%\ChainFlowToDo"

:: --- 5. ChainFlowSearch ---
echo.
echo [5/10] Building ChainFlowSearch (Search Tool)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowSearch\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowSearch"
py -m PyInstaller ChainFlowSearch.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowSearch" "%OUTPUT_DIR%\ChainFlowSearch"

:: --- 6. ChainFlowDesigner ---
echo.
echo [6/10] Building ChainFlowDesigner (DTP Editor)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowDesigner\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowDesigner"
py -m PyInstaller ChainFlowDesigner.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowDesigner" "%OUTPUT_DIR%\ChainFlowDesigner"

:: --- 7. ChainFlowPDFCompare ---
echo.
echo [7/10] Building ChainFlowPDFCompare (Side-by-Side Review)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowPDFCompare\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowPDFCompare"
py -m PyInstaller ChainFlowPDFCompare.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowPDFCompare" "%OUTPUT_DIR%\ChainFlowPDFCompare"

:: --- 8. ChainFlowPDFStudio ---
echo.
echo [8/10] Building ChainFlowPDFStudio (PDF Tools)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowPDFStudio\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowPDFStudio"
py -m PyInstaller ChainFlowPDFStudio.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowPDFStudio" "%OUTPUT_DIR%\ChainFlowPDFStudio"

:: --- 9. ChainFlowWriter (v9) ---
echo.
echo [9/10] Building ChainFlowWriter (Markdown Editor v9)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowWriter_v9\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowWriter_v9"
py -m PyInstaller ChainFlowWriter.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowWriter" "%OUTPUT_DIR%\ChainFlowWriter"

:: --- 10. ChainFlowSniper (V3) ---
echo.
echo [10/10] Building ChainFlowSniper (Research Browser V3)...
copy /Y "%MASTER_ICON%" "%PROJECT_ROOT%ChainFlowSniper_V3\app_icon.ico" >nul
cd /d "%PROJECT_ROOT%ChainFlowSniper_V3"
py -m PyInstaller ChainFlowSniper.spec --clean -y --log-level WARN
if errorlevel 1 goto ERROR
xcopy /E /I /Y /Q "dist\ChainFlowSniper" "%OUTPUT_DIR%\ChainFlowSniper"

:: ==========================================
:: Post-Build Cleanup (Reduce file count and size)
:: ==========================================
echo.
echo [Cleanup] Removing unnecessary translation files for all apps...
for /d %%d in ("%OUTPUT_DIR%\*") do (
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
echo  All 10 Apps Completed Successfully!
echo  Suite V22 is ready at: %OUTPUT_DIR%
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
