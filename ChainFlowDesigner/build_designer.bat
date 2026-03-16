@echo off
echo Building ChainFlowDesigner...
pyinstaller --clean --noconfirm ChainFlowDesigner.spec
echo Build Complete. Output is in dist/ChainFlowDesigner
pause
