from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QLabel, QStyle, QApplication, QMainWindow, QScrollArea
from PySide6.QtCore import Qt, QPointF, QEvent, Signal, QSize
from PySide6.QtGui import QCursor, QPixmap, QImage
import os
import fitz  # PyMuPDF

class FitzPdfPageNavigator(QWidget):
    """v21.1: Navigator proxy for FitzPdfView"""
    currentPageChanged = Signal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self._p = parent

    def currentPage(self):
        return self._p._current_page

    def jump(self, page, p, zoom):
        if not self._p._doc: return
        if 0 <= page < len(self._p._doc):
            self._p._current_page = page
            self._p.render_current_page()
            self.currentPageChanged.emit(page)

    def currentZoom(self):
        return self._p._zoom

class FitzPdfView(QScrollArea):
    """v21.1: Replaces QPdfView with fitz-based rendering to show annotations"""
    clicked = Signal()
    zoomFactorChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #1e1e1e; border: none;")
        
        self.container = QLabel()
        self.container.setAlignment(Qt.AlignCenter)
        self.setWidget(self.container)
        
        self._doc = None
        self._current_page = 0
        self._zoom = 1.0
        self._panning = False
        self._last_mouse_pos = None
        self._nav_proxy = FitzPdfPageNavigator(self)

    def setDocument(self, doc):
        self._doc = doc # fitz.Document
        self._current_page = 0
        self.show_page(0)

    def document(self):
        return self._doc

    def show_page(self, index):
        if not self._doc: return
        if 0 <= index < len(self._doc):
            self._current_page = index
            self.render_current_page()

    def render_current_page(self):
        if not self._doc: return
        page = self._doc[self._current_page]
        
        # Scaling: Ensure we get a sharp image for the current zoom
        mat = fitz.Matrix(self._zoom, self._zoom)
        # alpha=False ensures a white background by default in fitz
        pix = page.get_pixmap(matrix=mat, annots=True, alpha=False)
        
        # Convert to QImage (Format_RGB888 for 3-channel data)
        fmt = QImage.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        
        # Create QPixmap and display
        pixmap = QPixmap.fromImage(qimg)
        self.container.setPixmap(pixmap)
        self.container.setFixedSize(pixmap.size())

    def pageNavigator(self):
        return self._nav_proxy

    def setZoomMode(self, mode): pass # Placeholder
    def setZoomFactor(self, factor):
        self._zoom = max(0.1, min(factor, 5.0)) # Clamp zoom
        self.render_current_page()
        self.zoomFactorChanged.emit(self._zoom)

    def zoomFactor(self): return self._zoom

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.setZoomFactor(self.zoomFactor() * zoom_factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit()
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._last_mouse_pos:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class IndividualPdfView(QWidget):
    activeChanged = Signal(bool)
    clicked = Signal()
    internalPageDropped = Signal(str, int) # file_path, page_index
    popOutRequested = Signal(object) # self

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True) # Ensure clicks are caught
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2) # Margin for active border
        self.layout.setSpacing(0)
        
        self.is_active = False
        self.is_zen_mode = False
        self.current_doc_path = ""
        
        self.setAcceptDrops(True)
        
        # Toolbar
        self.toolbar = QToolBar()
        self.layout.addWidget(self.toolbar)
        
        self.pdf_view = FitzPdfView()
        self.pdf_view.clicked.connect(self.clicked)
        self.layout.addWidget(self.pdf_view)
        
        self._setup_toolbar()
        self.update_style()

    def set_active(self, active):
        self.is_active = active
        self.update_style()
        self.activeChanged.emit(active)

    def set_zen_mode(self, zen_enabled):
        self.is_zen_mode = zen_enabled
        self.update_style()
        self.toolbar.setVisible(not zen_enabled)

    def update_style(self):
        border_width = "2px" if not self.is_zen_mode else "1px"
        active_color = "#007acc" # Bright accent blue
        inactive_color = "#333333" if not self.is_zen_mode else "#2d2d2d"
        
        if self.is_active:
            self.setStyleSheet(f"IndividualPdfView {{ border: {border_width} solid {active_color}; }}")
            toolbar_bg = "#094771" # Darker accent blue for toolbar
            text_color = "#ffffff"
        else:
            self.setStyleSheet(f"IndividualPdfView {{ border: {border_width} solid {inactive_color}; }}")
            toolbar_bg = "#2d2d2d"
            text_color = "#eeeeee"
        
        self.toolbar.setStyleSheet(f"""
            QToolBar {{ background-color: {toolbar_bg}; border-bottom: 1px solid #444; }}
            QToolButton {{ color: {text_color}; font-size: 11px; font-family: 'Segoe UI'; }}
            QToolButton:hover {{ background-color: #454545; }}
            QLabel {{ color: {text_color}; font-family: 'Segoe UI'; font-size: 11px; margin-left: 5px; font-weight: bold; }}
        """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-chainflow-pdf-path"):
            event.acceptProposedAction()
        elif event.mimeData().hasUrls():
            # For external files
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasFormat("application/x-chainflow-pdf-path"):
            path = mime.data("application/x-chainflow-pdf-path").data().decode('utf-8')
            page = int(mime.data("application/x-chainflow-pdf-page").data().decode('utf-8'))
            self.internalPageDropped.emit(path, page)
            self.clicked.emit() # Mark as active
            event.acceptProposedAction()
        elif mime.hasUrls():
            # Forward to parent or handle if we want individual file drops
            # For now, let's keep it simple: top-level window handles file drops initially,
            # or we could implement it here to target a specific window.
            # Let's emit a signal so MainWindow can handle it for THIS view.
            for url in mime.urls():
                path = url.toLocalFile()
                if path.lower().endswith(".pdf"):
                    # We can use a special logic if needed, but for now just emit
                    self.internalPageDropped.emit(path, 0)
                    break
            self.clicked.emit()
            event.acceptProposedAction()
        
    def _setup_toolbar(self):
        # Icons (using standard icons for MVP)
        style = self.style()
        icon_prev = style.standardIcon(QStyle.StandardPixmap.SP_ArrowLeft)
        icon_next = style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight)
        
        # Navigation
        self.act_prev = self.toolbar.addAction(icon_prev, "Prev")
        self.act_next = self.toolbar.addAction(icon_next, "Next")
        
        self.toolbar.addSeparator()
        
        # Zoom
        self.act_zoom_in = self.toolbar.addAction("In")
        self.act_zoom_out = self.toolbar.addAction("Out")
        self.act_fit_width = self.toolbar.addAction("Fit Width")
        
        self.toolbar.addSeparator()

        self.lbl_page = QLabel("Page: 0/0")
        self.toolbar.addWidget(self.lbl_page)
        
        self.toolbar.addSeparator()
        
        # Pop Out
        self.act_pop = self.toolbar.addAction("Pop Out")
        self.act_pop.setToolTip("Detach this view to a separate window")
        self.act_pop.triggered.connect(lambda: self.popOutRequested.emit(self))
        
        # Connections
        self.act_prev.triggered.connect(lambda: self.navigate(-1))
        self.act_next.triggered.connect(lambda: self.navigate(1))
        self.act_zoom_in.triggered.connect(lambda: self.zoom(1.2))
        self.act_zoom_out.triggered.connect(lambda: self.zoom(1/1.2))
        self.act_fit_width.triggered.connect(self.fit_width)
        
        # Update label when page changes
        self.pdf_view.pageNavigator().currentPageChanged.connect(self.update_page_label)

    def set_document(self, document, path: str = ""):
        self.pdf_view.setDocument(document)
        self.current_doc_path = path
        self.update_page_label()

    def navigate(self, offset):
        if not self.pdf_view.document(): return
        nav = self.pdf_view.pageNavigator()
        target = nav.currentPage() + offset
        if 0 <= target < len(self.pdf_view.document()):
            nav.jump(target, QPointF(), nav.currentZoom())

    def update_page_label(self):
        doc = self.pdf_view.document()
        if doc:
            current = self.pdf_view.pageNavigator().currentPage() + 1
            total = len(doc)
            self.lbl_page.setText(f"Page: {current}/{total}")
        else:
            self.lbl_page.setText("No PDF")

    def zoom(self, factor):
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() * factor)
        
    def fit_width(self):
        if not self.pdf_view.document(): return
        page = self.pdf_view.document()[self.pdf_view._current_page]
        w = self.pdf_view.viewport().width() - 30
        self.pdf_view.setZoomFactor(w / page.rect.width)
