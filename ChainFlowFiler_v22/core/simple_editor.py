import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPlainTextEdit, QLabel, QPushButton, QFrame, QSplitter, 
                               QListWidget, QListWidgetItem, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QAction, QKeySequence, QShortcut

class SimpleEditor(QMainWindow):
    """
    Lite version of ChainFlow Editor for standalone usage.
    Features: Text Editing, Markdown Snippets, Dark Theme.
    No WebEngine, No Live Preview.
    """
    def __init__(self, file_path=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        
        self.setWindowTitle("ChainFlow Editor (Lite)")
        self.resize(900, 600)
        
        # Icon
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(os.path.dirname(sys.executable), "app_icon.ico")
        else:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # UI Integration
        # Dark Title Bar moved to showEvent for Windows compatibility (v19.2)

        self.setup_ui()
        self.apply_theme()
        
        if self.file_path and os.path.exists(self.file_path):
            self.load_file(self.file_path)

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header = QFrame()
        self.header.setFixedHeight(40)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        self.title_label = QLabel("Lite Editor")
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        
        self.help_btn = QPushButton("Helper")
        self.help_btn.setFixedSize(60, 24)
        self.help_btn.setCheckable(True)
        self.help_btn.setChecked(True)
        self.help_btn.setStyleSheet("background-color: #333; color: #ccc; border: none;")
        self.help_btn.clicked.connect(self.toggle_help)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedSize(60, 24)
        self.save_btn.setStyleSheet("background-color: #0e639c; color: white; border: none;")
        self.save_btn.clicked.connect(self.save_file)
        
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.help_btn)
        header_layout.addWidget(self.save_btn)
        
        layout.addWidget(self.header)
        
        # Splitter (Editor | Snippets)
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Editor
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setStyleSheet("border: none; background-color: #1e1e1e; color: #d4d4d4; padding: 10px;")
        self.splitter.addWidget(self.editor)
        
        # Helper Pane
        self.help_list = QListWidget()
        self.help_list.setFixedWidth(220)
        self.help_list.setFrameStyle(QFrame.NoFrame)
        self.help_list.setStyleSheet("background-color: #252526; color: #ccc; padding: 5px;")
        self.help_list.itemDoubleClicked.connect(self.insert_snippet)
        self.populate_help()
        self.splitter.addWidget(self.help_list)
        
        # Initial size
        self.splitter.setSizes([700, 200])
        layout.addWidget(self.splitter)
        
        # Save Shortcut
        # Save Shortcut
        # Use QShortcut directly for more reliable triggering compared to QAction
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.setContext(Qt.WindowShortcut)
        self.shortcut_save.activated.connect(self.save_file)

    def populate_help(self):
        shortcuts = [
            ("Header 1", "#", "\n# "),
            ("Header 2", "##", "\n## "),
            ("Bold", "**text**", "**text**"),
            ("Italic", "*text*", "*text*"),
            ("List", "- item", "\n- "),
            ("Task", "- [ ]", "\n- [ ] "),
            ("Code Block", "```", "\n```\ncode\n```\n"),
            ("Link", "[]()", "[text](url)"),
            ("Image", "![]()", "![alt](url)"),
            ("Table", "| A | B |", "\n| Header 1 | Header 2 |\n| -------- | -------- |\n| Cell 1   | Cell 2   |\n"),
            ("Line", "---", "\n---\n"),
        ]
        
        for name, key, snippet in shortcuts:
            item = QListWidgetItem(f"{name} ({key})")
            item.setData(Qt.UserRole, snippet)
            item.setToolTip(f"Double-click to insert:\n{snippet}")
            self.help_list.addItem(item)

    def insert_snippet(self, item):
        snippet = item.data(Qt.UserRole)
        if snippet:
            self.editor.insertPlainText(snippet)
            self.editor.setFocus()

    def toggle_help(self):
        self.help_list.setVisible(self.help_btn.isChecked())

    def load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.status_label.setText(f" - {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")

    def save_file(self):
        if not self.file_path:
            return # Save As not implemented for lite
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.status_label.setText(f" - Saved")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #cccccc; }
            QPushButton { background-color: #333; color: #ccc; border: 1px solid #444; border-radius: 4px; }
            QPushButton:hover { background-color: #444; }
            QPushButton:checked { background-color: #094771; }
            
            QScrollBar:vertical { border: none; background: #1e1e1e; width: 12px; margin: 0px; }
            QScrollBar::handle:vertical { background: #424242; min-height: 20px; border-radius: 6px; margin: 2px; }
            QScrollBar::handle:vertical:hover { background: #686868; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)

    def showEvent(self, event):
        try:
            from widgets.ui_utils import apply_dark_title_bar
            apply_dark_title_bar(self)
        except Exception as e:
            # print(f"SimpleEditor: Failed to apply dark title bar: {e}")
            pass
        super().showEvent(event)
