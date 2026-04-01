import sys
import os

# 実行中のスクリプトのディレクトリを基準にパスを通す
current_dir = os.path.dirname(os.path.abspath(__file__))

# v23.2 Fix: Nuitka または PyInstaller 環境の判定 (Internal構成対応)
is_standalone = getattr(sys, 'frozen', False) or "__compiled__" in globals() or "main.exe" in sys.executable.lower()

if is_standalone and os.path.basename(current_dir).lower() == "internal":
    os.chdir(os.path.dirname(current_dir))
else:
    os.chdir(current_dir)

sys.path.append(current_dir)

from PySide6.QtWidgets import QApplication
from widgets.main_window import ChainFlowFiler as FilerMainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ChainFlow Filer V23.2 [Modular Refined]")
    
    # Windows AppUserModelID (for Taskbar grouping)
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChainFlow.Filer.v23.2")
    except ImportError:
        pass
        
    window = FilerMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
