from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QListWidget, 
                             QListWidgetItem, QFileDialog, QLabel, QAbstractItemView, 
                             QFrame, QHBoxLayout, QScrollArea, QSizePolicy)
from PySide6.QtCore import Qt, QSize, QMimeData, Signal, QTimer
from PySide6.QtGui import QDrag, QPixmap, QIcon
import json
import os
from app.core.pdf_handler import PDFHandler
from app.ui.components.pdf_thumbnail import PDFThumbnail

class FileHeaderWidget(QFrame):
    """Draggable and clickable header for a PDF file group."""
    toggled = Signal(bool)

    def __init__(self, file_path, page_count, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.page_count = page_count
        self.collapsed = False
        
        self.setObjectName("FileHeader")
        self.setFixedHeight(32) # Strictly fixed height for title bar
        self.setStyleSheet("""
            QFrame#FileHeader {
                background-color: #383838;
                border-top: 1px solid #444;
                border-bottom: 1px solid #222;
            }
            QFrame#FileHeader:hover {
                background-color: #444;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0) # No vertical margins
        layout.setSpacing(5)
        
        # Collapse Icon
        self.icon_label = QLabel("▼")
        self.icon_label.setStyleSheet("color: #aaa; font-size: 10px;")
        layout.addWidget(self.icon_label)
        
        # File Name
        self.name_label = QLabel(os.path.basename(file_path))
        self.name_label.setStyleSheet("color: #eee; font-weight: bold;")
        layout.addWidget(self.name_label, 1)
        
        # Page Count
        self.count_label = QLabel(f"({page_count}p)")
        self.count_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.count_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if it was a click (not a drag)
            if (event.pos() - self.drag_start_pos).manhattanLength() < 5:
                self.toggle_collapsed()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < 10:
            return
            
        # Start Bulk Drag
        drag = QDrag(self)
        mime = QMimeData()
        
        # Create data for all pages
        pages_data = []
        for i in range(self.page_count):
            pages_data.append({
                "file_path": self.file_path,
                "page_num": i
            })
            
        mime.setData("application/x-chainflow-itemlist", json.dumps(pages_data).encode())
        drag.setMimeData(mime)
        
        # Simple ghost image
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        drag.exec(Qt.CopyAction)

    def toggle_collapsed(self):
        self.collapsed = not self.collapsed
        self.icon_label.setText("▶" if self.collapsed else "▼")
        self.toggled.emit(self.collapsed)

class FileGroupWidget(QWidget):
    """Combines a Header and a Grid for a single PDF file."""
    def __init__(self, file_path, pages_data, parent_pane=None):
        super().__init__()
        self.file_path = file_path
        self.parent_pane = parent_pane
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.header = FileHeaderWidget(file_path, len(pages_data))
        self.header.toggled.connect(self.set_collapsed)
        layout.addWidget(self.header)
        
        self.list_widget = LibraryListWidget(parent_pane)
        self.list_widget.setFixedHeight(0) # Initially updated
        layout.addWidget(self.list_widget)
        
        # Populate
        self.add_pages(pages_data)
        self.list_widget.adjust_height()

    def add_pages(self, pages_data):
        for data in pages_data:
            pixmap = data["pixmap"]
            page_idx = data["page_idx"]
            
            item = QListWidgetItem()
            item.setSizeHint(QSize(150, 190))
            item.setToolTip(self.file_path)
            item.setData(Qt.UserRole, {
                "file_path": self.file_path,
                "page_num": page_idx
            })
            self.list_widget.addItem(item)
            
            widget = PDFThumbnail(page_idx + 1, pixmap, file_path=self.file_path)
            self.list_widget.setItemWidget(item, widget)

    def set_collapsed(self, collapsed):
        self.list_widget.setVisible(not collapsed)
        # Flush the height change to parent scroll area
        self.list_widget.adjust_height()
        self.updateGeometry() # Tell parent layout we changed size
        
    def update_list_height(self):
        # Deprecated: LibraryListWidget handles its own height via adjust_height()
        self.list_widget.adjust_height()

class LibraryListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_pane = parent # LeftPane or Main
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setViewMode(QListWidget.IconMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setSpacing(10)
        self.setGridSize(QSize(160, 200))
        self.setUniformItemSizes(True)
        self.setMovement(QListWidget.Static) # Ensure items stick to top-left flow
        self.setFlow(QListWidget.LeftToRight)
        self.setWrapping(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(False) # Content doesn't accept drops in this mode
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Scroll handle by parent
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
        """)
        
        self.zoom_level = 1.0
        self.base_width = 160
        self.base_height = 200
        self.itemSelectionChanged.connect(self.update_selection_visuals)

    def update_selection_visuals(self):
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget and hasattr(widget, 'set_active'):
                widget.set_active(item.isSelected())

    def apply_zoom(self, zoom_level):
        self.zoom_level = zoom_level
        new_width = int(self.base_width * self.zoom_level)
        new_height = int(self.base_height * self.zoom_level)
        
        self.setGridSize(QSize(new_width, new_height))
        for i in range(self.count()):
            item = self.item(i)
            item.setSizeHint(QSize(new_width - 10, new_height - 10))
            widget = self.itemWidget(item)
            if widget and hasattr(widget, 'resize_thumbnail'):
                widget.resize_thumbnail(new_width - 20, new_height - 20)
        
        self.adjust_height()

    def adjust_height(self):
        """Strictly calculate height based on rows to avoid gaps."""
        if self.count() == 0 or not self.isVisible():
            self.setFixedHeight(1)
            return

        # Ensure layout is up to date
        self.doItemsLayout()
        
        grid_w = self.gridSize().width()
        grid_h = self.gridSize().height()
        
        # Use viewport width for column calculation
        # If width is too small (e.g. before shown), fall back to a reasonable default
        pane_width = self.viewport().width()
        if pane_width < 50: 
            pane_width = self.width()
            
        cols = max(1, pane_width // grid_w)
        rows = (self.count() + cols - 1) // cols
        
        # Exact height calculation
        # gridSize already includes spacing if setSpacing was used, 
        # but IconMode behavior with gridSize and spacing can be tricky.
        # We add a small buffer for safety.
        new_h = rows * grid_h + 10 
        
        self.setFixedHeight(new_h)
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-calculate on width changes
        QTimer.singleShot(10, self.adjust_height)

class LeftPane(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_handler = PDFHandler()
        self.file_groups = [] # List of FileGroupWidget
        self.zoom_level = 1.0
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # File Loader Button
        self.load_btn = QPushButton("Load PDF File")
        self.load_btn.setFixedHeight(40)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; font-weight: bold; font-size: 14px; border: none;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.load_btn.clicked.connect(self.load_pdf)
        self.main_layout.addWidget(self.load_btn)
        
        # Scroll Area for Groups
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #2b2b2b; border: none;")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.addStretch() # Push everything to top
        
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)
        
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        file_paths = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                file_paths.append(file_path)
        if file_paths:
            self.handle_dropped_files(file_paths)
            event.acceptProposedAction()

    def handle_dropped_files(self, file_paths):
        for file_path in file_paths:
            if self.pdf_handler.load_pdf(file_path):
                self.add_file_group(file_path)

    def load_pdf(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open PDF Files", "", "PDF Files (*.pdf)")
        if file_paths:
            self.handle_dropped_files(file_paths)

    def add_file_group(self, file_path):
        total_pages = self.pdf_handler.get_page_count()
        pages_data = []
        
        for i in range(total_pages):
            pixmap = self.pdf_handler.get_page_pixmap(i, width=320)
            if pixmap:
                pages_data.append({"pixmap": pixmap, "page_idx": i})
        
        if pages_data:
            group_widget = FileGroupWidget(file_path, pages_data, self)
            # Apply current zoom immediately
            group_widget.list_widget.apply_zoom(self.zoom_level)
            
            # Insert before the stretch
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, group_widget)
            self.file_groups.append(group_widget)

    def highlight_thumbnail(self, target_path, target_page):
        for group in self.file_groups:
            if group.file_path == target_path:
                # If target is in a collapsed group, we might want to expand it
                if group.header.collapsed:
                    group.header.toggle_collapsed()
                
                # Check all items in this group's list
                lw = group.list_widget
                for i in range(lw.count()):
                    item = lw.item(i)
                    data = item.data(Qt.UserRole)
                    if data and data.get("page_num") == target_page:
                        lw.setCurrentItem(item)
                        # Scroll the parent scroll area, not the list
                        self.scroll_area.ensureWidgetVisible(group)
                        # And slightly ensure item is visible? (lw is fixed height anyway)
                        return

    def update_used_overlays(self, used_pages_list):
        for group in self.file_groups:
            lw = group.list_widget
            for i in range(lw.count()):
                item = lw.item(i)
                data = item.data(Qt.UserRole)
                if not data: continue
                
                f_path = data.get("file_path")
                p_num = data.get("page_num")
                
                is_used = any(u_path == f_path and u_page == p_num for u_path, u_page in used_pages_list)
                
                widget = lw.itemWidget(item)
                if widget and hasattr(widget, 'set_used'):
                    widget.set_used(is_used)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0: self.zoom_level *= 1.1
            else: self.zoom_level *= 0.9
            
            self.zoom_level = max(0.5, min(3.0, self.zoom_level))
            for group in self.file_groups:
                group.list_widget.apply_zoom(self.zoom_level)
            event.accept()
        else:
            super().wheelEvent(event)

