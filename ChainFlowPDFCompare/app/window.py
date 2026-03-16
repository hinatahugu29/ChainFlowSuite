from PySide6.QtWidgets import QMainWindow, QFileDialog, QToolBar, QDockWidget, QApplication, QLabel
from PySide6.QtCore import Qt, QPointF, QEvent
from PySide6.QtGui import QIcon
import ctypes
import os
import sys
from .container import MultiViewContainer
from .document import PDFDocumentManager
from .sidebar import ThumbnailSidebar

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def apply_dark_title_bar(window):
    """
    Applies Windows dark title bar using ctypes.
    """
    try:
        hwnd = window.winId()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(int(hwnd)),
            ctypes.c_int(DWMWA_USE_IMMERSIVE_DARK_MODE),
            ctypes.byref(value),
            ctypes.sizeof(value)
        )
    except Exception as e:
        print(f"Failed to apply dark title bar: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChainFlow PDF Compare")
        self.resize(1200, 800)
        self.setAcceptDrops(True) # Enable Drag & Drop
        
        self.apply_app_icon()
        
        self.doc_manager = PDFDocumentManager()
        self.container = MultiViewContainer()
        self.sidebar = ThumbnailSidebar(self)
        
        self.setCentralWidget(self.container)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
        
        # ZEN Mode State
        self.is_zen_mode = False
        
        self.setup_ui()
        self.apply_theme()
        self.sidebar.connect_signals()
        
        # Library & View assignment
        self.doc_manager.documentAdded.connect(self.sidebar.add_document)
        self.sidebar.documentRequestedForActiveView.connect(self.set_pdf_to_active_view)
        
        # Handle internal drops onto views
        self.container.pageDropped.connect(self.handle_view_drop)
        
        # Sync Active View with Sidebar
        self.active_view_changed(self.container.get_active_view()) # Initial sync
        
        # Connect container's active view switch to sidebar
        # We need a signal from MultiViewContainer when active view changes
        self.container.activeViewChanged.connect(self.active_view_changed)

        # Pop-out Window Management
        self.popout_windows = []
        self.container.popOutRequested.connect(self.handle_pop_out)

    def set_pdf_to_active_view(self, doc):
        active_view = self.container.get_active_view()
        if active_view:
            path = ""
            for p, d in self.doc_manager.documents.items():
                if d == doc:
                    path = p
                    break
            active_view.set_document(doc, path)
            self.sidebar.set_active_view(active_view)

    def handle_view_drop(self, view, file_path, page_index):
        doc = self.doc_manager.load_document(file_path)
        view.set_document(doc, file_path)
        nav = view.pdf_view.pageNavigator()
        nav.jump(page_index, QPointF(), nav.currentZoom())
        self.sidebar.set_active_view(view)

    def handle_pop_out(self, view):
        file_path = view.current_doc_path
        page_index = view.pdf_view.pageNavigator().currentPage()

        workspace = WorkspaceWindow(self)
        workspace.setStyleSheet(self.styleSheet())
        
        if file_path:
            workspace.handle_view_drop(workspace.container.views[0], file_path, page_index)
        
        workspace.show()
        self.popout_windows.append(workspace)

    def apply_app_icon(self):
        # v21.1: Standardized icon detection
        icon_path = resource_path("app_icon.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            QApplication.setWindowIcon(icon)

    def setup_ui(self):
        # Menu
        menu = self.menuBar().addMenu("File")
        act_open = menu.addAction("Open PDF")
        act_open.triggered.connect(self.open_file)
        act_exit = menu.addAction("Exit")
        act_exit.triggered.connect(self.close)

        view_menu = self.menuBar().addMenu("View")
        act_toggle_sidebar = self.sidebar.toggleViewAction()
        act_toggle_sidebar.setText("Show Library")
        view_menu.addAction(act_toggle_sidebar)
        
        view_menu.addSeparator()
        act_zen = view_menu.addAction("ZEN Mode (F11)")
        act_zen.triggered.connect(self.toggle_zen_mode)
        
        # Main Toolbar
        toolbar = QToolBar("Layout")
        self.addToolBar(toolbar)
        
        for m, label in [("1", "1 View"), ("2H", "2 Views (H)"), ("2V", "2 Views (V)"), ("4", "4 Views")]:
            act = toolbar.addAction(label)
            act.triggered.connect(lambda checked=False, mode=m: self.container.set_layout_mode(mode))
        
        toolbar.addSeparator()

        act_reset = toolbar.addAction("Reset Sizes")
        act_reset.triggered.connect(self.container.reset_layout)
        
        toolbar.addSeparator()
        
        # Sync Scroll Toggle
        self.act_sync = toolbar.addAction("Sync Scroll")
        self.act_sync.setCheckable(True)
        self.act_sync.triggered.connect(self.container.set_sync_enabled)

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #cccccc; }
            QDockWidget { color: #cccccc; }
            QDockWidget::title { background-color: #2d2d2d; padding: 4px; }
            QToolBar { background-color: #2d2d2d; border-bottom: 1px solid #444; }
            QToolBar::separator { background-color: #444; width: 1px; margin: 4px; }
            QMenuBar { background-color: #2d2d2d; color: #cccccc; }
            QMenuBar::item:selected { background-color: #3e3e3e; }
            QMenu { background-color: #252526; color: #cccccc; border: 1px solid #454545; }
            QMenu::item:selected { background-color: #094771; }
            
            QListView { background-color: #252526; color: #cccccc; border: none; }
            QListView::item:hover { background-color: #2a2d2e; }
            QListView::item:selected { background-color: #094771; color: #ffffff; }
            
            QToolButton { color: #eeeeee; background-color: transparent; border: 1px solid transparent; padding: 3px; border-radius: 3px; }
            QToolButton:hover { background-color: #454545; border: 1px solid #555; }
            QToolButton:pressed { background-color: #153b93; }
            QLabel { color: #eeeeee; }

            QScrollBar:vertical {
                border: none;
                background: #252525;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #153b93;
                min-height: 30px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover { background: #3a62bd; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
            
            QScrollBar:horizontal {
                border: none;
                background: #252525;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #153b93;
                min-width: 30px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover { background: #3a62bd; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }
        """)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)

    def changeEvent(self, event):
        # v21.1: Re-apply dark title bar on state changes
        if event.type() in [QEvent.WindowStateChange, QEvent.ActivationChange]:
            apply_dark_title_bar(self)
        super().changeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.toggle_zen_mode()
        else:
            super().keyPressEvent(event)

    def toggle_zen_mode(self):
        self.is_zen_mode = not self.is_zen_mode
        self.menuBar().setVisible(not self.is_zen_mode)
        self.sidebar.setVisible(not self.is_zen_mode and not self.sidebar.isFloating())
        
        for toolbar in self.findChildren(QToolBar):
            toolbar.setVisible(not self.is_zen_mode)

        if self.is_zen_mode:
            self.showFullScreen()
        else:
            self.showNormal()

        for view in self.container.views:
            view.set_zen_mode(self.is_zen_mode)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if path:
            self.doc_manager.load_document(path)

    def load_initial_target(self, path):
        """Handle path passed from command line"""
        if not path or not os.path.exists(path):
            return
            
        path = os.path.abspath(path)
        if os.path.isfile(path) and path.lower().endswith(".pdf"):
            doc = self.doc_manager.load_document(path)
            # Automatically set to the first view
            if doc and self.container.views:
                self.container.views[0].set_document(doc, path)
        elif os.path.isdir(path):
            # Folder target: maybe in the future we crawl for PDFs, 
            # for now we just accept it as the context.
            pass

    def active_view_changed(self, view):
        self.sidebar.set_active_view(view)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        loaded_any = False
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".pdf"):
                self.doc_manager.load_document(file_path)
                loaded_any = True
        if loaded_any:
            event.acceptProposedAction()

class WorkspaceWindow(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window 
        self.setWindowTitle("ChainFlow PDF Compare - Workspace")
        self.resize(1000, 700)
        
        self.container = MultiViewContainer()
        self.setCentralWidget(self.container)
        
        self.container.activeViewChanged.connect(self.main_window.active_view_changed)
        self.container.pageDropped.connect(self.handle_view_drop)
        self.container.popOutRequested.connect(self.main_window.handle_pop_out)
        
        # ZEN Mode State
        self.is_zen_mode = False
        
        self.setup_ui()
        apply_dark_title_bar(self)
        
        # Use parent window icon if available
        if main_window:
            self.setWindowIcon(main_window.windowIcon())
        else:
            icon_path = resource_path("app_icon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))

    def setup_ui(self):
        toolbar = QToolBar("Layout")
        self.addToolBar(toolbar)
        
        for mode, label in [("1", "1 V"), ("2H", "2 H"), ("2V", "2 V"), ("4", "4 Vs")]:
            act = toolbar.addAction(label)
            act.triggered.connect(lambda checked=False, m=mode: self.container.set_layout_mode(m))

        toolbar.addSeparator()
        act_reset = toolbar.addAction("Reset Sizes")
        act_reset.triggered.connect(self.container.reset_layout)

    def handle_view_drop(self, view, file_path, page_index):
        doc = self.main_window.doc_manager.load_document(file_path)
        view.set_document(doc, file_path)
        nav = view.pdf_view.pageNavigator()
        nav.jump(page_index, QPointF(), nav.currentZoom())
        self.main_window.sidebar.set_active_view(view)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.toggle_zen_mode()
        else:
            super().keyPressEvent(event)

    def toggle_zen_mode(self):
        self.is_zen_mode = not self.is_zen_mode
        
        # Hide Toolbars
        for toolbar in self.findChildren(QToolBar):
            toolbar.setVisible(not self.is_zen_mode)

        if self.is_zen_mode:
            self.showFullScreen()
        else:
            self.showNormal()

        # Update each view's internal state (hide/show internal buttons)
        for view in self.container.views:
            view.set_zen_mode(self.is_zen_mode)

    def changeEvent(self, event):
        # Apply dark title bar on state changes
        if event.type() in [QEvent.WindowStateChange, QEvent.ActivationChange]:
            apply_dark_title_bar(self)
        super().changeEvent(event)
