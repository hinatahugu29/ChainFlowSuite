import fitz  # PyMuPDF
from PySide6.QtGui import QImage, QPixmap

class PDFHandler:
    def __init__(self):
        self.doc = None
        self.file_path = None

    def load_pdf(self, file_path):
        """Load a PDF file."""
        try:
            self.doc = fitz.open(file_path)
            self.file_path = file_path
            return True
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return False

    def get_page_count(self):
        """Return total number of pages."""
        if self.doc:
            return len(self.doc)
        return 0

    def save_pdf(self, output_path, pages_list):
        """
        Create a new PDF from a list of (source_path, page_num).
        pages_list: list of dict {"file_path": str, "page_num": int, "rotation": int}
        """
        try:
            out_doc = fitz.open()
            
            for page_data in pages_list:
                src_path = page_data["file_path"]
                page_num = page_data["page_num"]
                rotation = page_data.get("rotation", 0)
                
                # Check if we need to open a new doc (or use self.doc if matches)
                src_doc = None
                must_close = False
                
                # If current doc matches, use it
                if self.file_path == src_path and self.doc:
                    src_doc = self.doc
                else:
                    try:
                        src_doc = fitz.open(src_path)
                        must_close = True
                    except Exception as e:
                        print(f"Failed to open source: {src_path} - {e}")
                        continue
                
                if src_doc:
                    # Insert the page
                    out_doc.insert_pdf(src_doc, from_page=page_num, to_page=page_num)
                    
                    # Apply rotation if needed
                    if rotation != 0:
                        # The last added page is at index -1
                        last_page = out_doc[-1]
                        # PyMuPDF set_rotation adds to existing rotation
                        last_page.set_rotation(rotation)
                    
                if must_close:
                    src_doc.close()
            
            out_doc.save(output_path)
            out_doc.close()
            return True
            
        except Exception as e:
            print(f"Error saving PDF: {e}")
            return False

    def get_page_pixmap(self, page_num, width=120, scale=None):
        """
        Render a page to a QPixmap.
        page_num: 0-based index
        width: target width for thumbnail (ignored if scale is provided)
        scale: float explicit zoom factor (e.g. 2.0)
        """
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return None

        page = self.doc.load_page(page_num)
        
        # Calculate matrix
        if scale:
            mat = fitz.Matrix(scale, scale)
        else:
            # Calculate zoom factor to match target width
            rect = page.rect
            zoom = width / rect.width
            mat = fitz.Matrix(zoom, zoom)
        
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Convert fitz Pixmap to QImage
        # fitz.Pixmap.samples is a bytes object
        img_format = QImage.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
        
        # Convert QImage to QPixmap
        return QPixmap.fromImage(img)

    def close(self):
        if self.doc:
            self.doc.close()
