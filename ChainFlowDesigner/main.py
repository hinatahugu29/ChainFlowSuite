import sys
from PySide6.QtWidgets import QApplication
from dtp_editor import DTPEditor

import logging

def main():
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
    logging.info("Starting ChainFlow Designer...")
    # Windows Taskbar Icon Fix (v21.1)
    import ctypes
    try:
        myappid = 'ChainFlow.Designer.v21'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("ChainFlow Designer")
    
    initial_path = None
    if len(sys.argv) > 1:
        initial_path = sys.argv[1]
    
    window = DTPEditor(initial_path=initial_path)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
