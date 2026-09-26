import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from core.main_window import MainWindow

def get_resource_path(relative_path):
    """PyInstallerの一次展開先（_MEIPASS）または現在のディレクトリからパスを取得"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def load_application_theme(app):
    """QApplicationレベルでテーマを適用（全ダイアログにも確実に反映）"""
    theme_path = get_resource_path(os.path.join("resources", "theme.qss"))
    if os.path.exists(theme_path):
        with open(theme_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

if __name__ == "__main__":
    # Windows Taskbar Icon Fix
    try:
        myappid = 'ChainFlow.Sniper.v3'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    load_application_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
