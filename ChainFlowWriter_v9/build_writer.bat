@echo off
setlocal
echo Building ChainFlowWriter (Local)...

:: Ensure icon is present locally for build if needed, 
:: but usually the standalone script at root is preferred for production.
if not exist "app_icon.ico" (
    if exist "..\app_icon.ico" copy "..\app_icon.ico" "app_icon.ico"
)

py -m PyInstaller --noconsole --onefile --name "ChainFlowWriter" ^
    --icon "app_icon.ico" ^
    --add-data "app_icon.ico;." ^
    main.py --clean -y

echo.
echo Build Complete.
pause
