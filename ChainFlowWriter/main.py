import sys
import os
from PySide6.QtWidgets import QApplication

# Add parent directory to sys.path to allow running standalone or as a module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main_window import MainWindow

def main():
    # Windows Taskbar Icon Fix (v21.1)
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChainFlow.Writer.v21")
    except Exception:
        pass
        
    app = QApplication(sys.argv)
    
    # Handle command line argument for file path
    initial_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    window = MainWindow(initial_file)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
