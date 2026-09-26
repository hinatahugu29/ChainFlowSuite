import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QTextEdit, 
                               QVBoxLayout, QWidget, QToolButton, QFileDialog, 
                               QMessageBox, QMenu, QPlainTextEdit)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon, QFont, QAction, QShortcut, QKeySequence

# Import storage manager
try:
    from storage import StorageManager
except ImportError:
    # Handle dev cases if running standalone manually
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from storage import StorageManager

def apply_dark_title_bar(window):
    """
    Windows 10/11のタイトルバーをダークモードにするためのWin32 API呼び出し。
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = window.winId()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
        
        value = ctypes.c_int(1)
        # Windows 11 / Win 10 20H1+
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE, 
            ctypes.byref(value), ctypes.sizeof(value)
        )
        if result != 0:
            # Fallback for older Win10
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                int(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, 
                ctypes.byref(value), ctypes.sizeof(value)
            )
    except Exception as e:
        print(f"Failed to apply dark title bar: {e}")

class ScratchPadWindow(QMainWindow):
    """
    ChainFlowPad: Non-volatile, tabbed scratchpad.
    """
    def __init__(self, initial_path=None):
        super().__init__()
        self.setWindowTitle("ChainFlowPad")
        self.resize(800, 600)
        self.initial_path = initial_path if initial_path and os.path.isdir(initial_path) else ""
        
        # --- Icon Settings ---
        icon_path = ""
        if getattr(sys, 'frozen', False):
            # Nuitka/PyInstaller standalone: look in executable dir
            icon_path = os.path.join(os.path.dirname(sys.executable), "app_icon.ico")
        else:
            # Dev mode: look one level above project root
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_icon.ico")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        # ---------------------------
        
        # Apply dark title bar
        apply_dark_title_bar(self)
        
        self.storage = StorageManager()
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.auto_save)
        
        self.setup_ui()
        self.apply_style()
        self.load_session()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Plus Button for New Tab
        self.add_tab_btn = QToolButton(self)
        self.add_tab_btn.setText("+")
        self.add_tab_btn.clicked.connect(self.add_empty_tab)
        self.tab_widget.setCornerWidget(self.add_tab_btn, Qt.TopLeftCorner)
        
        self.layout.addWidget(self.tab_widget)
        
        # Shortcuts
        self.new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        self.new_tab_shortcut.activated.connect(self.add_empty_tab)
        
        self.close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        self.close_tab_shortcut.activated.connect(self.close_current_tab)

    def close_current_tab(self):
        self.close_tab(self.tab_widget.currentIndex())

    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QTabWidget::pane {
                border-top: 1px solid #333333;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #888888;
                padding: 8px 15px;
                border: 1px solid #1e1e1e;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #cccccc;
                border-top: 2px solid #007acc;
            }
            QTabBar::tab:hover {
                background-color: #333333;
            }
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                padding: 10px;
                selection-background-color: #264f78;
            }
            QToolButton {
                background-color: transparent;
                color: #aaaaaa;
                border: none;
                padding: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #333333;
                color: #ffffff;
            }
            /* Custom ScrollBar (Simplistic VSCode style) */
            QScrollBar:vertical {
                border: none;
                background: #1e1e1e;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4f4f4f;
            }
        """)

    def add_empty_tab(self, title="Empty Note", content=""):
        idx = self.tab_widget.count() + 1
        if not title or title == "Empty Note":
            title = f"Scratch {idx}"
            
        editor = QPlainTextEdit()
        editor.setPlainText(content)
        editor.textChanged.connect(self.trigger_save)
        
        # Context Menu for Export
        editor.setContextMenuPolicy(Qt.CustomContextMenu)
        editor.customContextMenuRequested.connect(self.show_editor_menu)
        
        self.tab_widget.addTab(editor, title)
        self.tab_widget.setCurrentWidget(editor)
        return editor

    def close_tab(self, index):
        editor = self.tab_widget.widget(index)
        if editor and editor.toPlainText().strip():
            # Check for non-empty content - allow hesitation
            title = self.tab_widget.tabText(index)
            reply = QMessageBox.question(self, "Close Tab", 
                                       f"ノート '{title}' を閉じますか？\n中身は保存されず、破棄されます。",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
            self.trigger_save()
        else:
            # Clear if only one tab left and confirmed (or already empty)
            self.tab_widget.widget(0).setPlainText("")
            self.trigger_save()

    def show_editor_menu(self, pos):
        menu = QMenu(self)
        export_txt = QAction("Save as .txt", self)
        export_txt.triggered.connect(lambda: self.export_current_tab(".txt"))
        export_md = QAction("Save as .md", self)
        export_md.triggered.connect(lambda: self.export_current_tab(".md"))
        
        menu.addAction(export_txt)
        menu.addAction(export_md)
        menu.exec(self.tab_widget.currentWidget().mapToGlobal(pos))

    def export_current_tab(self, ext):
        content = self.tab_widget.currentWidget().toPlainText()
        # Use initial_path as the base if available
        start_dir = self.initial_path if self.initial_path else ""
        path, _ = QFileDialog.getSaveFileName(self, "Export Note", start_dir, f"Files (*{ext})")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, "Success", f"Saved to {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def trigger_save(self):
        # Debounce: save 500ms after last change
        self.save_timer.start(500)

    def auto_save(self):
        tabs_data = []
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            title = self.tab_widget.tabText(i)
            tabs_data.append({
                "title": title,
                "content": editor.toPlainText(),
                "active": (i == self.tab_widget.currentIndex())
            })
        self.storage.save_state(tabs_data)

    def load_session(self):
        data = self.storage.load_state()
        if not data:
            self.add_empty_tab()
            return
            
        active_idx = 0
        for i, tab in enumerate(data):
            editor = self.add_empty_tab(tab.get("title"), tab.get("content"))
            if tab.get("active", False):
                active_idx = i
                
        self.tab_widget.setCurrentIndex(active_idx)

    def on_tab_changed(self, index):
        self.trigger_save()

    def showEvent(self, event):
        super().showEvent(event)
        # Ensure title bar is dark when window is shown
        apply_dark_title_bar(self)

    def closeEvent(self, event):
        self.auto_save() # Final save
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Accept initial path as the first argument
    initial_path = None
    if len(sys.argv) > 1:
        # Check if the first arg is a directory
        possible_path = sys.argv[1]
        if os.path.exists(possible_path):
            initial_path = possible_path
            
    window = ScratchPadWindow(initial_path)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
