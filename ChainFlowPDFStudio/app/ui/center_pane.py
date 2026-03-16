from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QHBoxLayout, QFrame, QLabel
from PySide6.QtCore import Qt, Signal
from app.ui.components.timeline_row import TimelineRow

class CenterPane(QWidget):
    jobs_updated = Signal() # Signal to notify when jobs structure changes
    sync_requested = Signal(str, int)
    used_pages_changed = Signal(list)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Header / Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #2b2b2b; border-bottom: 1px solid #3c3c3c;")
        toolbar.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(toolbar)
        
        title = QLabel("Timeline Editor")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #ddd; margin-left: 10px;")
        toolbar_layout.addWidget(title)
        
        toolbar_layout.addStretch()
        
        self.add_row_btn = QPushButton("+ Add Job Track")
        self.add_row_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; 
                color: white; 
                padding: 6px 12px; 
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.add_row_btn.clicked.connect(self.add_new_row)
        toolbar_layout.addWidget(self.add_row_btn)
        
        self.layout.addWidget(toolbar)

        # Scroll Area for Rows
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #1e1e1e; border: none;")
        
        # Container for Rows
        self.row_container = QWidget()
        self.row_layout = QVBoxLayout(self.row_container)
        self.row_layout.setContentsMargins(10, 10, 10, 10)
        self.row_layout.setSpacing(10)
        self.row_layout.setAlignment(Qt.AlignTop) # Align rows to top
        
        self.scroll_area.setWidget(self.row_container)
        self.layout.addWidget(self.scroll_area)
        
        self.rows = []
        self.row_counter = 0
        
        # Add initial row
        self.add_new_row()

    def update_used_pages(self):
        """Collect and emit all used pages."""
        used_pages = []
        for row in self.rows:
            # We need to access items in each row's timeline list
            count = row.timeline_list.count()
            for i in range(count):
                item = row.timeline_list.item(i)
                data = item.data(Qt.UserRole)
                if data:
                    file_path = data.get("file_path")
                    page_num = data.get("page_num")
                    if file_path and page_num is not None:
                        used_pages.append((file_path, page_num))
        
        self.used_pages_changed.emit(used_pages)

    def add_new_row(self):
        self.row_counter += 1
        row = TimelineRow(self.row_counter)
        row.delete_btn.clicked.connect(lambda: self.remove_row(row))
        
        # Connect state change signal
        row.state_changed.connect(self.jobs_updated.emit)
        row.state_changed.connect(self.update_used_pages) # Trigger update on any change (add/remove items)
        row.sync_requested.connect(self.sync_requested.emit)
        
        self.rows.append(row)
        self.row_layout.addWidget(row)
        
        self.jobs_updated.emit() # Notify addition
        self.update_used_pages()

    def remove_row(self, row):
        if row in self.rows:
            self.row_layout.removeWidget(row)
            row.deleteLater()
            self.rows.remove(row)
            self.jobs_updated.emit() # Notify removal
            self.update_used_pages()
