import fitz
from PySide6.QtCore import QObject, Signal

class PDFDocumentManager(QObject):
    documentAdded = Signal(str, object) # file_path, doc (fitz.Document)
    documentReady = Signal(str, object)

    def __init__(self):
        super().__init__()
        self.documents = {} # {file_path: fitz.Document}

    def load_document(self, file_path):
        if file_path in self.documents:
            return self.documents[file_path]
        
        try:
            doc = fitz.open(file_path)
            self.documents[file_path] = doc
            self.documentAdded.emit(file_path, doc)
            self.documentReady.emit(file_path, doc)
            return doc
        except Exception as e:
            print(f"Error loading PDF with fitz: {e}")
            return None
