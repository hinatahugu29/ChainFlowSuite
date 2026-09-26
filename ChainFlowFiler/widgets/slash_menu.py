
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListWidget, 
                               QListWidgetItem, QGraphicsOpacityEffect, QApplication)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, Signal, QRect, QEvent
from PySide6.QtGui import QColor, QFont, QKeyEvent

class SlashMenu(QWidget):
    """
    v16.0: Command Palette (Slash Menu)
    Overlay widget for executing commands via keyboard.
    """
    command_selected = Signal(str) # Emits command ID

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Frameless, Translucent, Tool
        # Using Popup or Tool to stay on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating) # Don't steal focus initially (we handle focus manually)
        
        self.resize(600, 400)
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Container (for styling)
        self.container = QWidget()
        self.container.setObjectName("Container")
        self.container.setStyleSheet("""
            QWidget#Container {
                background-color: #252526;
                border: 1px solid #454545;
                border-radius: 8px;
            }
        """)
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        
        # Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type a command...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #cccccc;
                border: none;
                border-bottom: 1px solid #454545;
                padding: 12px;
                font-size: 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QLineEdit:focus {
                background-color: #3e3e3e;
            }
        """)
        self.search_box.textChanged.connect(self.filter_commands)
        self.search_box.installEventFilter(self) # For Key Navigation
        
        # Command List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #2d2d2d;
            }
            QListWidget::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
        """)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        
        self.container_layout.addWidget(self.search_box)
        self.container_layout.addWidget(self.list_widget)
        
        self.main_layout.addWidget(self.container)
        
        # Animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.finished.connect(self._on_anim_finished)
        
        # Command Registry
        # Format: {"id": "cmd_id", "label": "Label", "desc": "Description"}
        self.commands = []
        
    def set_commands(self, commands):
        self.commands = commands
        self.filter_commands("")
        
    def filter_commands(self, text):
        self.list_widget.clear()
        text = text.lower()
        
        for cmd in self.commands:
            label = cmd.get("label", "")
            if text in label.lower():
                item = QListWidgetItem(f"{label}")
                # Use UserRole to store ID
                item.setData(Qt.UserRole, cmd.get("id"))
                item.setToolTip(cmd.get("desc", ""))
                self.list_widget.addItem(item)
                
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def eventFilter(self, obj, event):
        if obj == self.search_box and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Down:
                idx = self.list_widget.currentRow()
                if idx < self.list_widget.count() - 1:
                    self.list_widget.setCurrentRow(idx + 1)
                return True
            elif key == Qt.Key_Up:
                idx = self.list_widget.currentRow()
                if idx > 0:
                    self.list_widget.setCurrentRow(idx - 1)
                return True
            elif key == Qt.Key_Enter or key == Qt.Key_Return:
                self.execute_current()
                return True
            elif key == Qt.Key_Escape:
                self.fade_out()
                return True
                
        return super().eventFilter(obj, event)

    def execute_current(self):
        item = self.list_widget.currentItem()
        if item:
            cmd_id = item.data(Qt.UserRole)
            self.command_selected.emit(cmd_id)
            self.fade_out()

    def on_item_clicked(self, item):
        self.execute_current()

    def popup(self, parent_geo=None):
        if self.isVisible(): 
            self.activateWindow()
            self.search_box.setFocus()
            return
        
        # Center on parent
        if parent_geo:
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            # Minimal offset from top (VSCode style)
            y = parent_geo.y() + 50 
            self.move(x, y)
            
        self.show()
        self.activateWindow() # Ensure it grabs keyboard focus
        self.raise_()         # Bring to front
        self.search_box.setFocus()
        self.search_box.clear() # Reset search
        
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def fade_out(self):
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.start()
        # Return focus to parent window? handled by close logic potentially

    def _on_anim_finished(self):
        if self.anim.endValue() == 0:
            self.hide()
