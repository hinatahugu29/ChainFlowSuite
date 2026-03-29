import sys
import os

# プロジェクトルートをパスに追加して、パッケージとして認識させる
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from widgets.main_window import ChainFlowFiler

if __name__ == "__main__":
    # Windows Taskbar Icon Fix (v21.1)
    import ctypes
    try:
        myappid = 'ChainFlow.Filer.v22' # Standardized AppID
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    window = ChainFlowFiler()
    window.show()
    sys.exit(app.exec())
