@echo off
echo Building ChainFlowFiler v21...
pyinstaller --clean --noconfirm ChainFlowFiler_v21.spec
echo Build Complete. Output is in dist/ChainFlowFiler_v21
pause
