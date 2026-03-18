import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QLabel, QSplitter, QWidget, QPlainTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QPixmap
from app.utils.theme import apply_dark_title_bar, get_common_stylesheet

class CheatSheetDialog(QDialog):
    insert_requested = Signal(str) # Emits the raw content to insert

    def __init__(self, snippet_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cheat Sheet Gallery")
        self.setMinimumSize(700, 500)
        self.snippet_manager = snippet_manager
        
        self.setup_ui()
        self.load_snippets()

    def setup_ui(self):
        self.setStyleSheet(get_common_stylesheet())
        layout = QVBoxLayout(self)

        # Top Bar: Search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search snippets by title or tag...")
        self.search_input.textChanged.connect(self.filter_snippets)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Main Area
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Grid of Snippets
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(200, 150))
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setSpacing(10)
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: #1E1E1E; border: 1px solid #333; }
            QListWidget::item { background-color: #2D2D30; border-radius: 4px; padding: 5px; color: #D4D4D4; }
            QListWidget::item:selected { background-color: #0E639C; color: white; }
        """)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.itemDoubleClicked.connect(self._on_insert_clicked)
        splitter.addWidget(self.list_widget)

        # Right: Details & Actions
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        self.lbl_title = QLabel("Select a snippet...")
        self.lbl_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #FFFFFF;")
        self.lbl_title.setWordWrap(True)
        details_layout.addWidget(self.lbl_title)
        
        self.lbl_tags = QLabel("")
        self.lbl_tags.setStyleSheet("color: #0E639C;")
        details_layout.addWidget(self.lbl_tags)
        
        details_layout.addSpacing(10)
        lbl_raw = QLabel("Raw Code / Content:")
        lbl_raw.setStyleSheet("font-weight: bold; color: #8F8F8F;")
        details_layout.addWidget(lbl_raw)
        
        self.preview_text = QPlainTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                border: 1px solid #3E3E42;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        details_layout.addWidget(self.preview_text)
        
        details_layout.addStretch()
        
        self.btn_insert = QPushButton("エディタに挿入 (Insert)")
        self.btn_insert.setMinimumHeight(40)
        self.btn_insert.setStyleSheet("""
            QPushButton { background-color: #0E639C; color: white; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #1177BB; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.btn_insert.setEnabled(False)
        self.btn_insert.clicked.connect(self._on_insert_clicked)

        
        self.btn_delete = QPushButton("🗑️ 削除 (Delete)")
        self.btn_delete.setMinimumHeight(30)
        self.btn_delete.setStyleSheet("""
            QPushButton { background-color: #3E3E42; color: #D4D4D4; border: 1px solid #4F4F4F; border-radius: 4px; font-size: 10px; }
            QPushButton:hover { background-color: #A03D3D; color: white; border: 1px solid #D16969; }
            QPushButton:disabled { color: #555; background-color: #2D2D30; border: 1px solid #333; }
        """)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        
        btn_action_layout = QHBoxLayout()
        btn_action_layout.addWidget(self.btn_delete)
        btn_action_layout.addSpacing(10)
        btn_action_layout.addWidget(self.btn_insert, 2) # Insert is primary
        
        details_layout.addLayout(btn_action_layout)
        
        splitter.addWidget(details_widget)
        splitter.setSizes([500, 200]) # Initial widths
        
        layout.addWidget(splitter)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)

    def load_snippets(self, filter_text=""):
        self.list_widget.clear()
        snippets = self.snippet_manager.get_all_snippets()
        
        filter_text = filter_text.lower()
        
        for snippet in snippets:
            # Filtering
            title = snippet.get("title", "").lower()
            tags = " ".join(snippet.get("tags", [])).lower()
            if filter_text and filter_text not in title and filter_text not in tags:
                continue

            # Item creation
            item = QListWidgetItem()
            item.setText(snippet.get("title", "Untitled"))
            # Store ID for retrieval
            item.setData(Qt.UserRole, snippet.get("id")) 
            
            # Load Thumbnail
            thumb_file = snippet.get("thumbnail")
            if thumb_file:
                thumb_path = os.path.join(self.snippet_manager.thumbnail_dir, thumb_file)
                if os.path.exists(thumb_path):
                    icon = QIcon(thumb_path)
                    item.setIcon(icon)
            
            self.list_widget.addItem(item)

    def filter_snippets(self, text):
        self.load_snippets(text)

    def _on_selection_changed(self):
        items = self.list_widget.selectedItems()
        if not items:
            self.lbl_title.setText("Select a snippet...")
            self.lbl_tags.setText("")
            self.preview_text.clear()
            self.btn_insert.setEnabled(False)
            return

        snippet_id = items[0].data(Qt.UserRole)
        snippet = self.snippet_manager.get_snippet(snippet_id)
        if snippet:
            self.lbl_title.setText(snippet.get("title", "Untitled"))
            tags = snippet.get("tags", [])
            self.preview_text.setPlainText(snippet.get("content", ""))
            self.btn_insert.setEnabled(True)
            self.btn_delete.setEnabled(True)

    def _on_delete_clicked(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
            
        snippet_id = items[0].data(Qt.UserRole)
        title = items[0].text()
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete '{title}'?\nThis will also remove the thumbnail file.",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.snippet_manager.delete_snippet(snippet_id):
                self.load_snippets() # Refresh list
                # Reset details
                self.lbl_title.setText("Deleted.")
                self.lbl_tags.setText("")
                self.preview_text.clear()
                self.btn_insert.setEnabled(False)
                self.btn_delete.setEnabled(False)

    def _on_insert_clicked(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
            
        snippet_id = items[0].data(Qt.UserRole)
        snippet = self.snippet_manager.get_snippet(snippet_id)
        if snippet:
            self.insert_requested.emit(snippet.get("content", ""))
            self.accept() # Close dialog
