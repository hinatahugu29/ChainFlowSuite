from PySide6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from app.ui.components.pdf_thumbnail import PDFThumbnail
from app.core.pdf_handler import PDFHandler

class TimelineListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        
        # Context Menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Style (Copied from previous inline style for consistency)
        self.setStyleSheet("""
            QListWidget {
                background-color: #222;
                border: 1px solid #333;
            }
            QListWidget::item {
                background-color: transparent;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: transparent;
                border: 1px solid #3498db;
            }
        """)
        
        self.setFlow(QListWidget.LeftToRight)
        self.setViewMode(QListWidget.IconMode)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.Adjust)
        self.setSpacing(5)
        
        self.zoom_level = 1.0
        self.base_width = 160
        self.base_height = 200
        self.setGridSize(QSize(self.base_width, self.base_height))
        
        # Movement and Drag & Drop
        self.setMovement(QListWidget.Snap) 
        self.setUniformItemSizes(True)
        
        # Connect signals
        self.itemSelectionChanged.connect(self.handle_selection_changed)
        self.itemClicked.connect(self.handle_item_clicked)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_level *= 1.1
            else:
                self.zoom_level *= 0.9
            
            self.zoom_level = max(0.4, min(4.0, self.zoom_level))
            self.apply_zoom()
            event.accept()
        else:
            super().wheelEvent(event)

    def apply_zoom(self):
        """Scale thumbnails based on manual zoom level."""
        new_width = int(self.base_width * self.zoom_level)
        new_height = int(self.base_height * self.zoom_level)
        
        new_size = QSize(new_width, new_height)
        self.setGridSize(new_size)
        
        for i in range(self.count()):
            item = self.item(i)
            item.setSizeHint(new_size)
            widget = self.itemWidget(item)
            if widget and hasattr(widget, 'resize_thumbnail'):
                widget.resize_thumbnail(new_width - 10, new_height - 10)

    def resizeEvent(self, event):
        """Keep default resize behavior (don't force scale thumbnails)."""
        super().resizeEvent(event)

    sync_selection_requested = Signal(str, int)
    content_changed = Signal()

    def handle_item_clicked(self, item):
        """Handle direct click on item (even if already selected)."""
        self._sync_item(item)

    def handle_selection_changed(self):
        items = self.selectedItems()
        if not items:
            return
            
        item = self.currentItem() 
        if not item:
            item = items[0]
            
        self._sync_item(item)

    def _sync_item(self, item):
        data = item.data(Qt.UserRole)
        # print(f"DEBUG: Syncing Item: {data}") 
        if data and isinstance(data, dict):
            file_path = data.get("file_path")
            page_num = data.get("page_num")
            if file_path and page_num is not None:
                self.sync_selection_requested.emit(file_path, page_num)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-chainflow-itemlist"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-chainflow-itemlist"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-chainflow-itemlist"):
            import json
            try:
                data_raw = event.mimeData().data("application/x-chainflow-itemlist")
                items_data = json.loads(data_raw.data().decode())
                
                # Determine drop position
                drop_pos = event.position().toPoint()
                drop_index = self.indexAt(drop_pos)
                drop_row = drop_index.row() if drop_index.isValid() else self.count()
                
                # Add items with immediate size hints
                self.setUpdatesEnabled(False)
                for i, data in enumerate(items_data):
                    new_item = QListWidgetItem()
                    new_item.setData(Qt.UserRole, data)
                    new_item.setSizeHint(self.gridSize())
                    self.insertItem(drop_row + i, new_item)
                
                event.acceptProposedAction()
                self.refresh_thumbnails()
                self.setUpdatesEnabled(True)
            except Exception as e:
                print(f"Error handling bulk drop: {e}")
                self.setUpdatesEnabled(True)
        else:
            super().dropEvent(event)
            self.refresh_thumbnails()
            
        self.content_changed.emit()

    def refresh_thumbnails(self):
        """Populate widgets for items that don't have them yet."""
        handler_cache = {}
        # Disable updates during widget attachment to prevent layout jitter
        self.setUpdatesEnabled(False)
        
        try:
            for i in range(self.count()):
                item = self.item(i)
                if self.itemWidget(item):
                    continue
                    
                data = item.data(Qt.UserRole)
                if data and isinstance(data, dict):
                    file_path = data.get("file_path")
                    page_num = data.get("page_num")
                    
                    if file_path and page_num is not None:
                        if file_path not in handler_cache:
                            handler = PDFHandler()
                            if handler.load_pdf(file_path):
                                handler_cache[file_path] = handler
                            else:
                                handler_cache[file_path] = None
                        
                        handler = handler_cache[file_path]
                        if handler:
                            pixmap = handler.get_page_pixmap(page_num, width=600)
                            if pixmap:
                                widget = PDFThumbnail(page_num + 1, pixmap, file_path=file_path)
                                item.setSizeHint(self.gridSize())
                                self.setItemWidget(item, widget)
        finally:
            for h in handler_cache.values():
                if h: h.close()
            self.setUpdatesEnabled(True)
            
        # Hard refresh of geometry
        self.updateGeometries()
        self.doItemsLayout()
        # Final safety pass after a tiny delay
        QTimer.singleShot(1, self.doItemsLayout)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            self.remove_selected_items()
        elif event.key() == Qt.Key_Space:
            self.preview_current_item()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_D:
            self.duplicate_selected_items()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.itemAt(event.pos()):
            self.preview_current_item()
        else:
            super().mouseDoubleClickEvent(event)

    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            return

        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction

        menu = QMenu(self)
        
        action_preview = QAction("Preview (Space)", self)
        action_preview.triggered.connect(self.preview_current_item)
        menu.addAction(action_preview)
        
        menu.addSeparator()

        action_rotate_right = QAction("Rotate Right 90°", self)
        action_rotate_right.triggered.connect(lambda: self.rotate_selected_items(90))
        menu.addAction(action_rotate_right)

        action_rotate_left = QAction("Rotate Left 90°", self)
        action_rotate_left.triggered.connect(lambda: self.rotate_selected_items(-90))
        menu.addAction(action_rotate_left)
        
        menu.addSeparator()

        action_duplicate = QAction("Duplicate (Ctrl+D)", self)
        action_duplicate.triggered.connect(self.duplicate_selected_items)
        menu.addAction(action_duplicate)
        
        action_reverse = QAction("Reverse Order", self)
        action_reverse.triggered.connect(self.reverse_selected_items)
        menu.addAction(action_reverse)
        
        menu.addSeparator()

        action_remove = QAction("Remove (Delete)", self)
        action_remove.triggered.connect(self.remove_selected_items)
        menu.addAction(action_remove)

        menu.exec(self.mapToGlobal(pos))

    def remove_selected_items(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))
        self.content_changed.emit()

    def duplicate_selected_items(self):
        # We need to be careful with duplication order to be intuitive
        selected_rows = sorted([self.row(item) for item in self.selectedItems()])
        
        # We iterate in reverse to insert without messing up indices of earlier insertions
        # But actually, users usually expect duplication right after the item.
        # Let's process one by one
        
        # To avoid infinite loop if we selected the new items, we capture data first
        items_to_dup = []
        for row in selected_rows:
            item = self.item(row)
            data = item.data(Qt.UserRole)
            items_to_dup.append((row, data))
            
        # Insert duplicates
        offset = 1 
        for row, data in items_to_dup:
            new_item = QListWidgetItem()
            new_item.setData(Qt.UserRole, data)
            # Need to copy rotation if it exists
            # (Rotation is stored in data, so it's copied)
            
            insert_pos = row + offset
            self.insertItem(insert_pos, new_item)
            
            # Restore widget/thumbnail
            # We can reuse refresh_thumbnails logic or just do it here for speed
            self.refresh_single_item(new_item)
            
            offset += 1
        self.content_changed.emit()

    def reverse_selected_items(self):
        selected_items = self.selectedItems()
        if len(selected_items) < 2:
            return
            
        rows = sorted([self.row(item) for item in selected_items])
        
        # We need to reorder these items in the list.
        # Easiest way: take them all out, then insert them back in reverse order at the starting index.
        
        # Extract data & widgets (or just data, widgets will be recreated)
        extracted_data = []
        for item in selected_items:
            extracted_data.append(item.data(Qt.UserRole))
        
        # Reverse the data
        extracted_data.reverse()
        
        # Remove old items (from back to front to preserve indices)
        for row in reversed(rows):
            self.takeItem(row)
            
        # Insert new items at the starting position
        start_row = rows[0]
        for i, data in enumerate(extracted_data):
            new_item = QListWidgetItem()
            new_item.setData(Qt.UserRole, data)
            self.insertItem(start_row + i, new_item)
            self.refresh_single_item(new_item)
            
        # Reselect them? Maybe.
        self.content_changed.emit()
        
    def rotate_selected_items(self, angle):
        """
        Rotate selected items by angle (90 or -90).
        Update Qt.UserRole data 'rotation' and refresh thumbnail.
        """
        for item in self.selectedItems():
            data = item.data(Qt.UserRole)
            if not data: 
                continue
                
            current_rotation = data.get("rotation", 0)
            new_rotation = (current_rotation + angle) % 360
            data["rotation"] = new_rotation
            item.setData(Qt.UserRole, data)
            
            self.refresh_single_item(item)
        self.content_changed.emit()

    def refresh_single_item(self, item):
        """Helper to refresh just one item's thumbnail (e.g. after rotation)"""
        data = item.data(Qt.UserRole)
        if not data: 
            return

        file_path = data.get("file_path")
        page_num = data.get("page_num")
        rotation = data.get("rotation", 0)
        
        if file_path:
            handler = PDFHandler()
            if handler.load_pdf(file_path):
                # High resolution for better visual quality when zoomed
                pixmap = handler.get_page_pixmap(page_num, width=320 if "left_pane" in str(self.parent_pane) else 600)
                if pixmap:
                    # Apply rotation to pixmap if needed
                    if rotation != 0:
                        from PySide6.QtGui import QTransform
                        transform = QTransform().rotate(rotation)
                        pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                    
                    widget = PDFThumbnail(page_num + 1, pixmap, file_path=file_path)
                    widget.resize_thumbnail(self.gridSize().width() - 10, self.gridSize().height() - 10)
                    item.setSizeHint(self.gridSize())
                    self.setItemWidget(item, widget)
            handler.close()

    def preview_current_item(self):
        item = self.currentItem()
        if not item: return
        
        data = item.data(Qt.UserRole)
        if not data: return
        
        file_path = data.get("file_path")
        page_num = data.get("page_num")
        rotation = data.get("rotation", 0)
        
        if file_path:
            self.show_preview_dialog(file_path, page_num, rotation)

    def show_preview_dialog(self, file_path, page_num, rotation):
        from app.ui.components.preview_dialog import PreviewDialog
        dialog = PreviewDialog(self, file_path, page_num, rotation)
        dialog.exec()
