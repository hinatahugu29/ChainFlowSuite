from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QScrollArea, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QTransform, QWheelEvent, QKeyEvent, QAction
from app.core.pdf_handler import PDFHandler

class PreviewDialog(QDialog):
    def __init__(self, parent, file_path, page_num, rotation=0):
        super().__init__(parent)
        self.file_path = file_path
        self.page_num = page_num
        self.rotation = rotation
        self.scale_factor = 1.0
        self.base_scale = 3.0 # Load at higher resolution for better zoom quality
        self.base_pixmap = None
        
        self.setWindowTitle(f"Preview: {file_path} - Page {page_num+1}")
        self.resize(1000, 900)
        
        self.layout = QVBoxLayout(self)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False) 
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #555;") # Lighter bg to see if label exists
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True) 
        
        self.scroll_area.setWidget(self.image_label)
        self.layout.addWidget(self.scroll_area)
        
        # Initial scale setup
        self.base_scale = 3.0 
        self.scale_factor = 2.0 / self.base_scale # Equivalent to old 2.0x view
        
        self.load_base_image()
        
        # Apply theme immediately (force window handle creation)
        self.winId() 
        self._apply_theme()

    def _apply_theme(self):
        try:
            from app.ui.utils import apply_dark_title_bar
            apply_dark_title_bar(self)
        except Exception:
            pass
        
    def load_base_image(self):
        handler = PDFHandler()
        if handler.load_pdf(self.file_path):
            # Render once at high resolution
            pixmap = handler.get_page_pixmap(self.page_num, scale=self.base_scale)
            if pixmap:
                if self.rotation != 0:
                     transform = QTransform().rotate(self.rotation)
                     pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                self.base_pixmap = pixmap
                self.image_label.setPixmap(self.base_pixmap)
                self.image_label.resize(self.image_label.pixmap().size() * self.scale_factor)
            else:
                self.image_label.setText("Failed to render page.")
        else:
            self.image_label.setText(f"Failed to load PDF: {self.file_path}")
        handler.close()

    def update_display(self):
        if not self.base_pixmap:
            return
            
        base_size = self.base_pixmap.size()
        new_width = base_size.width() * self.scale_factor
        new_height = base_size.height() * self.scale_factor
        
        self.image_label.resize(int(new_width), int(new_height))
        # self.image_label.adjustSize() # Do NOT call this with setScaledContents(True)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal: 
             if event.modifiers() == Qt.ControlModifier:
                self.zoom_in()
        elif event.key() == Qt.Key_Minus:
             if event.modifiers() == Qt.ControlModifier:
                self.zoom_out()
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def zoom_in(self):
        self.scale_factor *= 1.1
        self.update_display()

    def zoom_out(self):
        self.scale_factor *= 0.9
        self.update_display()
