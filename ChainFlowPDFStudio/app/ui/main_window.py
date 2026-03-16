from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt, QTimer, QEvent
from app.ui.left_pane import LeftPane
from app.ui.center_pane import CenterPane
from app.ui.right_pane import RightPane

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Py PDF STUDIO")
        self.resize(1400, 900)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter setup
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Initialize Panes
        self.left_pane = LeftPane()
        self.center_pane = CenterPane()
        self.right_pane = RightPane(self) # Pass self reference
        
        # Add widgets to splitter
        self.splitter.addWidget(self.left_pane)
        self.splitter.addWidget(self.center_pane)
        self.splitter.addWidget(self.right_pane)
        
        # Connect Sync Signal (Center -> Left)
        self.center_pane.sync_requested.connect(self.left_pane.highlight_thumbnail)
        
        # Connect Used Pages Signal (Center -> Left)
        self.center_pane.used_pages_changed.connect(self.left_pane.update_used_overlays)
        
        # Set initial sizes (ratio approx 1:2:1)
        self.splitter.setSizes([300, 800, 300])
        
        # Add splitter to layout
        main_layout.addWidget(self.splitter)

    def showEvent(self, event):
        super().showEvent(event)
        # v21.1: Apply immediately after super() ensures HWND is ready
        self._apply_title_bar_theme()
        # Backup: re-apply on next event loop cycle to catch any late repaints
        QTimer.singleShot(0, self._apply_title_bar_theme)

    def changeEvent(self, event):
        # v21.1 Theme Permanence fix - Removed ActivationChange to prevent focus loops
        if event.type() == QEvent.WindowStateChange:
            self._apply_title_bar_theme()
        super().changeEvent(event)

    def _apply_title_bar_theme(self):
        try:
            from app.ui.utils import apply_dark_title_bar
            apply_dark_title_bar(self)
        except Exception as e:
            print(f"Failed to apply dark title bar: {e}")
