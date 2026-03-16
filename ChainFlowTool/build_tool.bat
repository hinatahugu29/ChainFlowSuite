@echo off
echo Starting Build for ChainFlow Tool...

cd /d "%~dp0"

echo Building ChainFlowTool...
pyinstaller --clean --noconfirm ChainFlowTool.spec

echo Build Complete!
pause
