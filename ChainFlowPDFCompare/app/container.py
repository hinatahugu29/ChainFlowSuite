from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QSplitter
from PySide6.QtCore import Qt, Signal, QPointF
from .view import IndividualPdfView

class MultiViewContainer(QWidget):
    activeViewChanged = Signal(object)
    pageDropped = Signal(object, str, int) # view, path, page_index
    popOutRequested = Signal(object) # view

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create 4 independent views
        self.views = [IndividualPdfView() for _ in range(4)]
        
        # Setup active view tracking
        self.active_view = self.views[0]
        self.active_view.set_active(True)
        
        for view in self.views:
            # Connect the view's clicked signal to a slot that sets it as active
            view.clicked.connect(lambda v=view: self.set_active_view(v))
            # Also connect the internal PDF view click if needed, 
            # but we bridged it in IndividualPdfView
            view.pdf_view.clicked.connect(lambda v=view: self.set_active_view(v))
            
            # Pop Out Handling
            view.popOutRequested.connect(self.popOutRequested.emit)
            
            # Drop Handling
            view.internalPageDropped.connect(lambda p, idx, v=view: self.pageDropped.emit(v, p, idx))
            
            # Sync Scroll connections
            view.pdf_view.pageNavigator().currentPageChanged.connect(lambda _, v=view: self._on_view_page_changed(v))
            view.pdf_view.zoomFactorChanged.connect(lambda _, v=view: self._on_view_zoom_changed(v))

        # Keep track of the current layout widget to remove it properly
        self.current_layout_widget = None
        
        # Keep track of active splitters for resetting
        self.active_splitters = []
        
        # Default to single view
        self.set_layout_mode("1")
        
        # Sync Scroll State
        self.is_sync_enabled = False

    def set_sync_enabled(self, enabled):
        self.is_sync_enabled = enabled

    def _on_view_page_changed(self, source_view):
        if not self.is_sync_enabled:
            return
            
        nav_src = source_view.pdf_view.pageNavigator()
        page = nav_src.currentPage()
        
        for view in self.views:
            if view != source_view and view.pdf_view.document():
                nav_dst = view.pdf_view.pageNavigator()
                if page < len(view.pdf_view.document()) and nav_dst.currentPage() != page:
                    # Block signals to prevent infinite recursion
                    nav_dst.blockSignals(True)
                    nav_dst.jump(page, QPointF(), nav_dst.currentZoom())
                    nav_dst.blockSignals(False)

    def _on_view_zoom_changed(self, source_view):
        if not self.is_sync_enabled:
            return
            
        zoom = source_view.pdf_view.zoomFactor()
        for view in self.views:
            if view != source_view and view.pdf_view.zoomFactor() != zoom:
                view.pdf_view.blockSignals(True)
                view.pdf_view.setZoomFactor(zoom)
                view.pdf_view.blockSignals(False)

    def set_active_view(self, view):
        if self.active_view == view:
            return
            
        if self.active_view:
            self.active_view.set_active(False)
            
        self.active_view = view
        self.active_view.set_active(True)
        self.activeViewChanged.emit(view)

    def get_active_view(self):
        return self.active_view

    def set_document(self, document):
        for view in self.views:
            view.set_document(document)

    def set_layout_mode(self, mode):
        self.current_mode = mode
        # Clear existing layout content
        if self.current_layout_widget:
            self.main_layout.removeWidget(self.current_layout_widget)
            # Reparent views to self to prevent deletion when container is destroyed
            for view in self.views:
                view.setParent(self)
                view.hide()
            
            self.current_layout_widget.deleteLater()
            self.current_layout_widget = None
        
        self.active_splitters = []
        self.current_layout_widget = QWidget()
        
        if mode == "1":
            layout = QVBoxLayout(self.current_layout_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.views[0])
            self.views[0].show()
            
        elif mode == "2H":
            layout = QVBoxLayout(self.current_layout_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            splitter = QSplitter(Qt.Horizontal)
            splitter.addWidget(self.views[0])
            splitter.addWidget(self.views[1])
            layout.addWidget(splitter)
            self.active_splitters.append(splitter)
            self.views[0].show()
            self.views[1].show()
            
        elif mode == "2V":
            layout = QVBoxLayout(self.current_layout_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            splitter = QSplitter(Qt.Vertical)
            splitter.addWidget(self.views[0])
            splitter.addWidget(self.views[1])
            layout.addWidget(splitter)
            self.active_splitters.append(splitter)
            self.views[0].show()
            self.views[1].show()
            
        elif mode == "4":
            layout = QVBoxLayout(self.current_layout_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Vertical Splitter (Main)
            main_splitter = QSplitter(Qt.Vertical)
            
            # Top Splitter (Horizontal)
            top_splitter = QSplitter(Qt.Horizontal)
            top_splitter.addWidget(self.views[0])
            top_splitter.addWidget(self.views[1])
            
            # Bottom Splitter (Horizontal)
            bottom_splitter = QSplitter(Qt.Horizontal)
            bottom_splitter.addWidget(self.views[2])
            bottom_splitter.addWidget(self.views[3])
            
            main_splitter.addWidget(top_splitter)
            main_splitter.addWidget(bottom_splitter)
            
            layout.addWidget(main_splitter)
            
            self.active_splitters.extend([main_splitter, top_splitter, bottom_splitter])
            
            for v in self.views:
                v.show()

        self.main_layout.addWidget(self.current_layout_widget)
        
        # Auto-reset layout to equal sizes initially
        self.reset_layout()

    def reset_layout(self):
        """Reset all active splitters to equal sizes"""
        for splitter in self.active_splitters:
            count = splitter.count()
            if count > 0:
                # Set equal sizes
                # Note: setSizes takes a list of integers. 
                # Absolute values don't matter as much as their ratio, 
                # but large enough numbers ensure smooth distribution.
                splitter.setSizes([1000] * count)
