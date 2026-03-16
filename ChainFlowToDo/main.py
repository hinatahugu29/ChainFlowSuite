import sys
import os
import json
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QCheckBox, QLineEdit, QScrollArea, 
                               QFrame, QProgressBar, QComboBox, QMessageBox, QMenu)
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve, QEvent
from PySide6.QtGui import QIcon, QFont, QAction, QKeySequence, QShortcut, QColor

# --- Data Model ---
from todo_model import ToDoModel

class TaskWidget(QFrame):
    deleted = Signal()
    changed = Signal()

    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(45)
        self.setObjectName("TaskItem")
        self.setStyleSheet("""
            QFrame#TaskItem {
                background-color: transparent;
                border-bottom: 1px solid #333;
            }
            QFrame#TaskItem:hover {
                background-color: #2a2d2e;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        # Checkbox
        self.cb = QCheckBox()
        self.cb.setChecked(self.task_data.get("checked", False))
        self.cb.stateChanged.connect(self.on_toggle)
        self.cb.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }")
        layout.addWidget(self.cb)

        # Priority Badge
        prio = self.task_data.get("priority", "low")
        self.prio_label = QLabel(prio.upper())
        self.prio_label.setFixedSize(50, 20)
        self.prio_label.setAlignment(Qt.AlignCenter)
        self.prio_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.update_priority_style(prio)
        layout.addWidget(self.prio_label)

        # Text
        self.text_label = QLabel(self.task_data.get("text", ""))
        self.text_label.setStyleSheet("color: #ccc; font-size: 11pt;")
        if self.cb.isChecked():
            self.text_label.setStyleSheet("color: #666; font-size: 11pt; text-decoration: line-through;")
        layout.addWidget(self.text_label, 1)

        # Timestamp
        self.time_label = QLabel(self.task_data.get("added", ""))
        self.time_label.setStyleSheet("color: #555; font-size: 9pt;")
        layout.addWidget(self.time_label)

        # Delete Button
        self.del_btn = QPushButton("×")
        self.del_btn.setFixedSize(30, 30)
        self.del_btn.setStyleSheet("""
            QPushButton { 
                background: transparent; color: #888; border: none; font-size: 16pt; 
            }
            QPushButton:hover { color: #e74c3c; }
        """)
        self.del_btn.clicked.connect(self.deleted.emit)
        layout.addWidget(self.del_btn)

    def update_priority_style(self, prio):
        colors = {
            "high": ("#e74c3c", "#fff"),
            "medium": ("#f39c12", "#fff"),
            "low": ("#2ecc71", "#fff")
        }
        bg, fg = colors.get(prio, ("#555", "#fff"))
        self.prio_label.setStyleSheet(f"background-color: {bg}; color: {fg}; border_radius: 4px;")

    def on_toggle(self, state):
        self.task_data["checked"] = (state == Qt.Checked.value)
        if self.task_data["checked"]:
            self.text_label.setStyleSheet("color: #666; font-size: 11pt; text-decoration: line-through;")
        else:
            self.text_label.setStyleSheet("color: #ccc; font-size: 11pt;")
        self.changed.emit()

class CategoryWidget(QFrame):
    changed = Signal()
    deleted = Signal()

    def __init__(self, cat_data, parent=None):
        super().__init__(parent)
        self.cat_data = cat_data
        self.is_expanded = cat_data.get("open", True)
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("CategoryOuter")
        self.setStyleSheet("QFrame#CategoryOuter { background-color: #252526; border-radius: 8px; margin-bottom: 10px; }")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header
        self.header = QFrame()
        self.header.setFixedHeight(50)
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.setStyleSheet("""
            QFrame { 
                background-color: #153b93; 
                border-top-left-radius: 8px; border-top-right-radius: 8px; 
            }
            QFrame:hover { background-color: #1a4bb0; }
        """)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(15, 0, 15, 0)

        self.title_label = QLabel(self.cat_data["name"])
        self.title_label.setStyleSheet("color: white; font-weight: bold; font-size: 12pt;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.progress_label = QLabel("0/0 (0%)")
        self.progress_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 9pt;")
        header_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(120, 8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: rgba(0,0,0,0.2); border: none; border-radius: 4px; }
            QProgressBar::chunk { background: #2ecc71; border-radius: 4px; }
        """)
        header_layout.addWidget(self.progress_bar)

        self.main_layout.addWidget(self.header)

        # Content Area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(0)
        
        self.tasks_container = QVBoxLayout()
        self.content_layout.addLayout(self.tasks_container)

        # Add Task Input
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(10, 10, 10, 10)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("新しい項目を追加...")
        self.task_input.setStyleSheet("""
            QLineEdit { 
                background: #3c3c3c; color: #ccc; border: 1px solid #444; 
                padding: 8px; border-radius: 4px; 
            }
        """)
        self.task_input.returnPressed.connect(self.add_task)
        
        self.prio_combo = QComboBox()
        self.prio_combo.addItems(["low", "medium", "high"])
        self.prio_combo.setStyleSheet("""
            QComboBox { 
                background: #3c3c3c; color: #ccc; border: 1px solid #444; 
                padding: 6px; border-radius: 4px; 
            }
        """)

        self.add_btn = QPushButton("＋")
        self.add_btn.setFixedSize(40, 34)
        self.add_btn.setStyleSheet("background: #2ecc71; color: white; border-radius: 4px; font-weight: bold;")
        self.add_btn.clicked.connect(self.add_task)

        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.prio_combo)
        input_layout.addWidget(self.add_btn)
        self.content_layout.addLayout(input_layout)

        # Delete Category Button
        self.del_cat_btn = QPushButton("このカテゴリを削除")
        self.del_cat_btn.setStyleSheet("color: #e74c3c; background: transparent; border: none; padding: 10px;")
        self.del_cat_btn.clicked.connect(self.deleted.emit)
        self.content_layout.addWidget(self.del_cat_btn, 0, Qt.AlignRight)

        self.main_layout.addWidget(self.content_widget)

        self.header.mousePressEvent = self.toggle_expand
        self.update_tasks()
        self.apply_expand_state()

    def toggle_expand(self, event):
        self.is_expanded = not self.is_expanded
        self.cat_data["open"] = self.is_expanded
        self.apply_expand_state()
        self.changed.emit()

    def apply_expand_state(self):
        self.content_widget.setVisible(self.is_expanded)
        if not self.is_expanded:
            self.header.setStyleSheet(self.header.styleSheet().replace("border-top-left-radius: 8px; border-top-right-radius: 8px;", "border-radius: 8px;"))
        else:
            self.header.setStyleSheet(self.header.styleSheet().replace("border-radius: 8px;", "border-top-left-radius: 8px; border-top-right-radius: 8px;"))

    def update_tasks(self):
        # Clear existing
        while self.tasks_container.count():
            item = self.tasks_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        items = self.cat_data.get("items", [])
        total = len(items)
        done = sum(1 for i in items if i.get("checked"))
        percent = int((done / total * 100)) if total > 0 else 0

        self.progress_label.setText(f"{done}/{total} ({percent}%)")
        self.progress_bar.setValue(percent)

        for i, task in enumerate(items):
            tw = TaskWidget(task)
            tw.changed.connect(self.on_task_changed)
            tw.deleted.connect(lambda idx=i: self.delete_task(idx))
            self.tasks_container.addWidget(tw)

    def add_task(self):
        text = self.task_input.text().strip()
        if text:
            task = {
                "text": text,
                "checked": False,
                "added": datetime.now().strftime("%Y/%m/%d %H:%M"),
                "priority": self.prio_combo.currentText()
            }
            self.cat_data["items"].append(task)
            self.task_input.clear()
            self.update_tasks()
            self.changed.emit()

    def delete_task(self, idx):
        if 0 <= idx < len(self.cat_data["items"]):
            self.cat_data["items"].pop(idx)
            self.update_tasks()
            self.changed.emit()

    def on_task_changed(self):
        self.update_tasks()
        self.changed.emit()

class ToDoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChainFlow ToDo")
        
        # --- Icon Settings ---
        icon_path = ""
        if getattr(sys, 'frozen', False):
            # sys._MEIPASS logic for PyInstaller
            bundle_dir = sys._MEIPASS
            icon_path = os.path.join(bundle_dir, "app_icon.ico")
        else:
            # Local dev path
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        # ---------------------
        
        self.resize(1100, 850)
        
        self.model = ToDoModel(os.path.join(os.path.dirname(__file__), "todo_data.json"))
        self.setup_ui()
        self.apply_theme()
        self.render_categories()

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_dark_title_bar()

    def changeEvent(self, event):
        # v21.1: Re-apply dark title bar on state changes to prevent theme breakage
        if event.type() in [QEvent.WindowStateChange, QEvent.ActivationChange]:
            self.apply_dark_title_bar()
        super().changeEvent(event)

    def apply_dark_title_bar(self):
        try:
            import ctypes
            hwnd = self.winId()
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(int(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
        except Exception: pass

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.layout = QVBoxLayout(central)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("ChainFlow ToDo")
        title.setStyleSheet("font-size: 24pt; font-weight: bold; color: #ccc;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.copy_btn = QPushButton("MarkdownでCopy")
        self.copy_btn.setFixedSize(150, 40)
        self.copy_btn.setStyleSheet("background: #9b59b6; color: white; border-radius: 6px; font-weight: bold;")
        self.copy_btn.clicked.connect(self.export_to_markdown)
        header_layout.addWidget(self.copy_btn)
        
        self.layout.addLayout(header_layout)

        # Scroll Area for Categories
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll)

        # Add Category Area
        add_cat_layout = QHBoxLayout()
        self.cat_input = QLineEdit()
        self.cat_input.setPlaceholderText("新しいカテゴリ名を入力...")
        self.cat_input.setStyleSheet("background: #3c3c3c; color: #ccc; border: 1px solid #444; padding: 10px; border-radius: 6px;")
        self.cat_input.returnPressed.connect(self.add_category)
        
        self.add_cat_btn = QPushButton("＋ 新しいカテゴリを追加")
        self.add_cat_btn.setFixedSize(220, 40)
        self.add_cat_btn.setStyleSheet("background: #2ecc71; color: white; border-radius: 6px; font-weight: bold;")
        self.add_cat_btn.clicked.connect(self.add_category)
        
        add_cat_layout.addWidget(self.cat_input)
        add_cat_layout.addWidget(self.add_cat_btn)
        self.layout.addLayout(add_cat_layout)

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QWidget { font-family: 'Segoe UI', 'Meiryo', sans-serif; color: #cccccc; }
            
            /* ScrollArea fixes */
            QScrollArea { background-color: #121212; border: none; }
            QScrollArea QWidget { background-color: #121212; }
            QScrollArea > QWidget > QWidget { background-color: #121212; }
            
            /* Category Card Background Fix */
            QFrame#CategoryOuter { background-color: #252526; }
            
            /* Input Styles */
            QLineEdit { 
                background: #1e1e1e; color: #eee; border: 1px solid #333; 
                padding: 10px; border-radius: 6px; 
            }
            QLineEdit:focus { border-color: #153b93; background: #252526; }

            /* ScrollBar customization: Accent Rounded (v16.0 style) */
            QScrollBar:vertical {
                border: none;
                background: #121212;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #153b93;
                min-height: 30px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover { background: #3a62bd; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
            
            QScrollBar:horizontal {
                border: none; background: #121212; height: 12px; margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #153b93; min-width: 30px; border-radius: 6px; margin: 2px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

            /* QMessageBox Dark Theme */
            QMessageBox { background-color: #252526; color: #cccccc; border: 1px solid #444; }
            QMessageBox QLabel { color: #cccccc; font-size: 11pt; }
            QMessageBox QPushButton { 
                background-color: #0e639c; color: #ffffff; 
                border: none; border-radius: 4px; 
                padding: 6px 20px; min-width: 80px; font-weight: bold;
            }
            QMessageBox QPushButton:hover { background-color: #1177bb; }
        """)

    def render_categories(self):
        # Clear existing
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self.scroll_content.setObjectName("ScrollContent")

        for i, cat in enumerate(self.model.data):
            cw = CategoryWidget(cat)
            cw.changed.connect(self.model.save)
            cw.deleted.connect(lambda idx=i: self.delete_category(idx))
            self.scroll_layout.addWidget(cw)

    def add_category(self):
        name = self.cat_input.text().strip()
        if name:
            self.model.add_category(name)
            self.cat_input.clear()
            self.render_categories()

    def delete_category(self, idx):
        cat_name = self.model.data[idx]["name"]
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("削除確認")
        msg_box.setText(f"カテゴリ「{cat_name}」を削除しますか？")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setIcon(QMessageBox.Question)
        
        # テーマとタイトルバーを適用
        self.apply_dark_title_bar_to_widget(msg_box)
        
        reply = msg_box.exec()
        if reply == QMessageBox.Yes:
            self.model.delete_category(idx)
            self.render_categories()

    def apply_dark_title_bar_to_widget(self, widget):
        """指定したウィジェットのタイトルバーをダークにする"""
        try:
            import ctypes
            hwnd = widget.winId()
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(int(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
        except Exception: pass

    def export_to_markdown(self):
        now_str = datetime.now().strftime("%Y/%m/%d %H:%M")
        md = f"# バックアップ\n_エクスポート日時: {now_str}_\n\n"
        
        for cat in self.model.data:
            md += f"## {cat['name']}\n\n"
            for item in cat.get("items", []):
                mark = "[x]" if item.get("checked") else "[ ]"
                time = f" _({item.get('added', '不明')})_"
                md += f"- {mark} {item.get('text', '')}{time}\n"
            md += "\n"
            
        app = QApplication.instance()
        cb = app.clipboard()
        cb.setText(md)
        
        notify = QMessageBox(self)
        notify.setWindowTitle("完了")
        notify.setText("Markdown形式でクリップボードにコピーしました。")
        notify.setIcon(QMessageBox.Information)
        self.apply_dark_title_bar_to_widget(notify)
        notify.exec()

def main():
    # Windows Taskbar Icon Fix
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChainFlow.ToDo.v21")
    except ImportError:
        pass

    app = QApplication(sys.argv)
    
    window = ToDoWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
