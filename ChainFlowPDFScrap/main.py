import sys
import os
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

def main():
    # Set AppUserModelID for Windows taskbar icon consistency
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChainFlow.PDFScrap.1.0")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("ChainFlow PDF Scrap")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
