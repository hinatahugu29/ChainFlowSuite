import fitz
from PySide6.QtWidgets import QDockWidget, QListView, QWidget, QVBoxLayout
from PySide6.QtCore import QAbstractListModel, Qt, QSize, QModelIndex, QPointF, Signal, QMimeData
from PySide6.QtGui import QIcon, QImage, QPixmap, QDrag
class PdfPageModel(QAbstractListModel):
    def __init__(self, document=None, doc_path=""):
        super().__init__()
        self._document = document # fitz.Document
        self._doc_path = doc_path
        self._page_count = len(self._document) if self._document else 0

    def set_document(self, document, path=""):
        self.beginResetModel()
        self._document = document
        self._doc_path = path
        self._page_count = len(self._document) if self._document else 0
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return self._page_count

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not self._document:
            return None

        if role == Qt.DisplayRole:
            return f"Page {index.row() + 1}"
        
        if role == Qt.DecorationRole:
            # Render thumbnail with PyMuPDF
            page = self._document[index.row()]
            
            # Target size
            target_w, target_h = 100, 140
            zoom = min(target_w / page.rect.width, target_h / page.rect.height)
            mat = fitz.Matrix(zoom, zoom)
            
            # alpha=False for white background
            pix = page.get_pixmap(matrix=mat, annots=True, alpha=False)
            
            # Convert to QImage (RGB888)
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            
            # Create a white-padded thumbnail
            thumbnail = QPixmap(target_w, target_h)
            thumbnail.fill(Qt.white)
            
            from PySide6.QtGui import QPainter
            painter = QPainter(thumbnail)
            offset_x = (target_w - pix.width) // 2
            offset_y = (target_h - pix.height) // 2
            painter.drawImage(offset_x, offset_y, qimg)
            painter.end()
            
            return QIcon(thumbnail)

        return None

class DraggableThumbnailListView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            super().mouseMoveEvent(event)
            return
            
        index = self.currentIndex()
        if not index.isValid():
            super().mouseMoveEvent(event)
            return

        model = self.model()
        if not model or not model._doc_path:
            super().mouseMoveEvent(event)
            return

        drag = QDrag(self)
        mime = QMimeData()
        
        # Internal custom drag data
        mime.setData("application/x-chainflow-pdf-path", model._doc_path.encode('utf-8'))
        mime.setData("application/x-chainflow-pdf-page", str(index.row()).encode('utf-8'))
        
        # Also set as text for general compatibility
        mime.setText(f"PDF_PAGE:{model._doc_path}:{index.row()}")
        
        drag.setMimeData(mime)
        
        # Set thumbnail as drag pixmap
        pixmap = index.data(Qt.DecorationRole)
        if isinstance(pixmap, QIcon):
            pixmap = pixmap.pixmap(self.iconSize())
        if pixmap:
            drag.setPixmap(pixmap)
            
        drag.exec_(Qt.CopyAction)

class ThumbnailSidebar(QDockWidget):
    # Signals
    documentRequestedForActiveView = Signal(object) # doc

    def __init__(self, parent=None):
        super().__init__("Library", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 1. Stock List (Upper)
        from PySide6.QtWidgets import QLabel, QHBoxLayout, QPushButton
        stock_header = QHBoxLayout()
        stock_header.addWidget(QLabel(" PDF Stock:"))
        stock_header.addStretch()
        
        self.btn_remove = QPushButton("Remove")
        self.btn_remove.setFixedWidth(60)
        self.btn_remove.setStyleSheet("""
            QPushButton { background-color: #3c3c3c; color: #eee; border: 1px solid #555; font-size: 10px; border-radius: 2px; }
            QPushButton:hover { background-color: #d13438; color: white; }
        """)
        self.btn_remove.clicked.connect(self.remove_selected_document)
        stock_header.addWidget(self.btn_remove)
        
        self.layout.addLayout(stock_header)
        self.stock_list = QListView()
        self.stock_list.setFixedHeight(150)
        self.stock_list.setEditTriggers(QListView.NoEditTriggers) # Disable inline editing
        # Use StandardItemModel for the stock list
        from PySide6.QtGui import QStandardItemModel, QStandardItem
        self.stock_model = QStandardItemModel()
        self.stock_list.setModel(self.stock_model)
        self.layout.addWidget(self.stock_list)
        
        # 2. Page Thumbnails (Lower)
        self.layout.addWidget(QLabel(" Pages:"))
        self.list_view = DraggableThumbnailListView()
        self.list_view.setViewMode(QListView.IconMode)
        self.list_view.setIconSize(QSize(100, 140))
        self.list_view.setGridSize(QSize(120, 160))
        self.list_view.setMovement(QListView.Static)
        self.list_view.setResizeMode(QListView.Adjust)
        
        self.model = PdfPageModel()
        self.list_view.setModel(self.model)
        self.layout.addWidget(self.list_view)
        
        self.setWidget(self.container)
        
        self.active_view = None
        self.documents = {} # path: doc
        
        # Internal Connections
        self.stock_list.clicked.connect(self._on_stock_clicked)
        self.stock_list.doubleClicked.connect(self._on_stock_double_clicked)

    def add_document(self, path, doc):
        import os
        self.documents[path] = doc
        from PySide6.QtGui import QStandardItem
        item = QStandardItem(os.path.basename(path))
        item.setData(path, Qt.UserRole)
        self.stock_model.appendRow(item)
        
        # Select if first
        if self.stock_model.rowCount() == 1:
            self.stock_list.setCurrentIndex(self.stock_model.index(0, 0))
            self.model.set_document(doc, path)

    def remove_selected_document(self):
        index = self.stock_list.currentIndex()
        if not index.isValid():
            return
            
        path = index.data(Qt.UserRole)
        # Remove from model
        self.stock_model.removeRow(index.row())
        # Remove from internal dict
        if path in self.documents:
            doc = self.documents.pop(path)
            # If this doc was being previewed in the thumbnails, clear it
            if self.model._document == doc:
                self.model.set_document(None)
                
            # Note: We don't necessarily close the doc here if it's still 
            # assigned to a view, but we remove it from the selectable stock.

    def set_active_view(self, view):
        self.active_view = view
        # Sync thumbnails to active view's document
        if self.active_view:
            doc = self.active_view.pdf_view.document()
            path = self.active_view.current_doc_path # We need to track this in IndividualPdfView
            if doc:
                self.model.set_document(doc, path)
                # Match current page
                page = self.active_view.pdf_view.pageNavigator().currentPage()
                index = self.model.index(page, 0)
                self.list_view.setCurrentIndex(index)

    def connect_signals(self):
        self.list_view.clicked.connect(self._on_thumbnail_clicked)

    def _on_stock_clicked(self, index):
        path = index.data(Qt.UserRole)
        doc = self.documents.get(path)
        if doc:
            self.model.set_document(doc, path)

    def _on_stock_double_clicked(self, index):
        path = index.data(Qt.UserRole)
        doc = self.documents.get(path)
        if doc:
            self.documentRequestedForActiveView.emit(doc)

    def _on_thumbnail_clicked(self, index):
        if self.active_view and self.active_view.pdf_view.document() == self.model._document:
            page = index.row()
            nav = self.active_view.pdf_view.pageNavigator()
            nav.jump(page, QPointF(), nav.currentZoom())
