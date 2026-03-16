from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QCheckBox
from PySide6.QtCore import Qt, QSize, Signal
from app.ui.components.timeline_list import TimelineListWidget

class ResizeHandle(QFrame):
    """A draggable handle for resizing the TimelineRow vertically."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self.setCursor(Qt.SizeVerCursor)
        self.setStyleSheet("""
            background-color: #444; 
            border-top: 1px solid #555;
            border-bottom-left-radius: 4px;
            border-bottom-right-radius: 4px;
        """)
        self._dragging = False
        self._start_y = 0
        self._start_height = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._start_y = event.globalPos().y()
            self._start_height = self.parent().height()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.globalPos().y() - self._start_y
            new_height = max(230, self._start_height + delta) # Minimum height 230
            self.parent().setFixedHeight(new_height)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()
            
    def enterEvent(self, event):
        self.setStyleSheet("background-color: #3498db; border-top: 1px solid #555; border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;")
        
    def leaveEvent(self, event):
        self.setStyleSheet("background-color: #444; border-top: 1px solid #555; border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;")

class TimelineRow(QFrame):
    state_changed = Signal()

    def __init__(self, row_id, parent=None):
        super().__init__(parent)
        self.row_id = row_id
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(230) # Default height (can be resized)
        self.setStyleSheet("background-color: #2e2e2e; border: 1px solid #444; border-radius: 4px; margin-bottom: 5px;")

        # Use QVBoxLayout for the main frame to stack content and resize handle
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Content Area (Horizontal)
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent; border: none;")
        main_layout = QHBoxLayout(content_widget)
        main_layout.setContentsMargins(5, 5, 5, 0)
        main_layout.setSpacing(5)
        
        outer_layout.addWidget(content_widget)

        # 1. Control Panel (Left)
        # ---------------------------------------------------------
        control_panel = QFrame()
        control_panel.setFixedWidth(200)
        control_panel.setStyleSheet("background-color: #383838; border: none;")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)

        # Export Checkbox
        self.active_check = QCheckBox("Enable Export")
        self.active_check.setChecked(True) # Default to active
        self.active_check.setStyleSheet("color: #ddd; font-weight: bold;")
        self.active_check.toggled.connect(self.emit_state_change)
        control_layout.addWidget(self.active_check)

        # Filename Input
        control_layout.addWidget(QLabel("Filename:"))
        
        # Filename Input Area (Horizontal Layout)
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(2)
        
        self.filename_input = QLineEdit(f"output_{row_id}.pdf")
        self.filename_input.setPlaceholderText("Output Filename")
        self.filename_input.setStyleSheet("padding: 5px; color: #eee; background-color: #555; border: 1px solid #666;")
        self.filename_input.textChanged.connect(self.emit_state_change)
        input_row.addWidget(self.filename_input)
        
        # Timestamp Button
        self.ts_btn = QPushButton("🕒")
        self.ts_btn.setToolTip("Insert Timestamp")
        self.ts_btn.setFixedWidth(40) # Increased width for better visibility
        self.ts_btn.setFixedHeight(28) 
        self.ts_btn.setStyleSheet("""
            QPushButton {
                background-color: #555; 
                color: #ddd; 
                border: 1px solid #666;
                font-size: 16px; /* Slightly larger for emoji clarity */
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        self.ts_btn.clicked.connect(self.insert_timestamp)
        input_row.addWidget(self.ts_btn)
        
        control_layout.addLayout(input_row)

        # Page Count Label
        self.page_count_label = QLabel("0 pages")
        self.page_count_label.setStyleSheet("color: #aaa;")
        control_layout.addWidget(self.page_count_label)
        
        control_layout.addStretch()

        # Delete Row Button
        self.delete_btn = QPushButton("Remove Job")
        self.delete_btn.setStyleSheet("background-color: #c0392b; color: white; padding: 5px;")
        control_layout.addWidget(self.delete_btn)

        main_layout.addWidget(control_panel)

        # 2. Timeline Area (Right - Horizontal Scroll)
        # ---------------------------------------------------------
        self.timeline_list = TimelineListWidget()
        # Ensure height fits rows (approx 190px for thumbnails + margins)
        # self.timeline_list.setFixedHeight(210) 

        main_layout.addWidget(self.timeline_list)
        
        # Connect model update (simple version)
        self.timeline_list.model().rowsInserted.connect(self.update_page_count)
        self.timeline_list.model().rowsRemoved.connect(self.update_page_count)
        
        # Connect explicit content changed signal (covers drop, duplicate, etc.)
        self.timeline_list.content_changed.connect(self.update_page_count)
        
        # Relay sync signal
        self.timeline_list.sync_selection_requested.connect(self.sync_requested.emit)

        # Add Resize Handle at the bottom
        resize_handle = ResizeHandle(self)
        outer_layout.addWidget(resize_handle)

    sync_requested = Signal(str, int)

    def update_page_count(self):
        count = self.timeline_list.count()
        self.page_count_label.setText(f"{count} pages")
        self.emit_state_change()

    def emit_state_change(self):
        self.state_changed.emit()

    def get_job_data(self):
        """Collect data for export."""
        pages = []
        for i in range(self.timeline_list.count()):
            item = self.timeline_list.item(i)
            data = item.data(Qt.UserRole)
            if data:
                pages.append(data)
                
        filename = self.filename_input.text().strip()
        if not filename:
            filename = f"output_{self.row_id}.pdf"
        if not filename.endswith(".pdf"):
            filename += ".pdf"
            
        return {
            "filename": filename,
            "pages": pages,
            "active": self.active_check.isChecked()
        }

    def insert_timestamp(self):
        """Append timestamp to filename."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_text = self.filename_input.text().strip()
        
        # Determine how to append
        if not current_text:
            new_text = f"output_{timestamp}.pdf"
        elif ".pdf" in current_text.lower():
             # Insert before extension
             base, ext = current_text.rsplit('.', 1)
             new_text = f"{base}_{timestamp}.{ext}"
        else:
            new_text = f"{current_text}_{timestamp}"
            
        self.filename_input.setText(new_text)
