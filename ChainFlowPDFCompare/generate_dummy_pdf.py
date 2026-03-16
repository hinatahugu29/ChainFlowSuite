from PySide6.QtGui import QPdfWriter, QPainter, QPageSize
from PySide6.QtWidgets import QApplication
import sys

def create_pdf(filename):
    # QPdfWriter needs a QGuiApplication (or QApplication) to function properly in many cases
    app = QApplication(sys.argv)
    
    writer = QPdfWriter(filename)
    writer.setCreator("PDF Viewer Test Script")
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    
    painter = QPainter(writer)
    
    font = painter.font()
    font.setPointSize(20)
    painter.setFont(font)

    for i in range(10):
        if i > 0:
            writer.newPage()
        painter.drawText(200, 200, f"This is Page {i+1}")
        painter.drawText(200, 400, "Multi-View PDF Viewer Test")
        painter.drawRect(100, 100, 4000, 4000) # Draw a box to check scrolling
        painter.drawText(100, 100, "Top Left")
        painter.drawText(4000, 4000, "Bottom Right")
    
    painter.end()
    print(f"Created {filename}")

if __name__ == "__main__":
    create_pdf("dummy.pdf")
