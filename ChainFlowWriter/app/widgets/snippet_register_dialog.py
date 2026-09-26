from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QTextEdit, QPushButton)
from PySide6.QtCore import Qt
from app.utils.theme import apply_dark_title_bar, get_common_stylesheet

class SnippetRegisterDialog(QDialog):
    def __init__(self, raw_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save as Snippet")
        self.raw_content = raw_content
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(get_common_stylesheet())
        layout = QVBoxLayout(self)

        # Title Input
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. 2-Column Image Layout")
        layout.addWidget(self.title_input)

        # Tags Input
        layout.addWidget(QLabel("Tags (comma separated):"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("e.g. layout, image, utility")
        layout.addWidget(self.tags_input)

        # Content Preview (Read Only)
        layout.addWidget(QLabel("Content:"))
        self.content_preview = QTextEdit()
        self.content_preview.setPlainText(self.raw_content)
        self.content_preview.setReadOnly(True)
        # Apply editor styling for consistency
        self.content_preview.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: Consolas, monospace;
            }
        """)
        layout.addWidget(self.content_preview)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Save Snippet")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)

    def get_data(self):
        # Process tags into a clean list
        tags_str = self.tags_input.text()
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        
        return {
            "title": self.title_input.text().strip(),
            "tags": tags,
            "content": self.raw_content
        }
