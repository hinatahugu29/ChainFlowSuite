import fitz  # PyMuPDF
from PySide6.QtGui import QImage, QPixmap

class PDFScrapHandler:
    def __init__(self):
        self.doc = None
        self.file_path = None

    def load_pdf(self, file_path):
        try:
            self.doc = fitz.open(file_path)
            self.file_path = file_path
            return True
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return False

    def get_page_count(self):
        return len(self.doc) if self.doc else 0

    def get_page_pixmap(self, page_num, width=800):
        """Render page for preview."""
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return None
        page = self.doc.load_page(page_num)
        zoom = width / page.rect.width
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return self._fitz_to_pixmap(pix)

    def get_clipped_pixmap(self, page_num, rect, dpi=300):
        """
        Clip a specific area of a page at high resolution.
        rect: (x0, y0, x1, y1) in PDF coordinates (points)
        """
        if not self.doc: return None
        page = self.doc.load_page(page_num)
        
        # rect is in PDF points. dpi/72 gives the zoom factor for high quality.
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        # Define clip area in PDF points
        clip_rect = fitz.Rect(rect)
        
        pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
        return self._fitz_to_pixmap(pix)

    def _fitz_to_pixmap(self, pix):
        img_format = QImage.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
        return QPixmap.fromImage(img)

    def close(self):
        if self.doc:
            self.doc.close()
