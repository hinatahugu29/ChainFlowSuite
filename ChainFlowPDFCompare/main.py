import sys
from PySide6.QtWidgets import QApplication
from app.window import MainWindow
import os

def main():
    # v21.1: Set AppUserModelID to ensure taskbar consistency
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChainFlow.PDFCompare.v21")
    except Exception:
        pass

    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Handle initial command line argument (file or folder)
    if len(sys.argv) > 1:
        window.load_initial_target(sys.argv[1])
        
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
