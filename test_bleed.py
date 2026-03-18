import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtCore import QUrl, QMarginsF, QTimer

app = QApplication(sys.argv)
page = QWebEnginePage()

# Test Scenario: 
# 1. Set QPageLayout margins to 0 (to avoid clipping).
# 2. Set @page margins in CSS (to achieve consistent margins on all pages).
# 3. Place a stamp that overlaps the margin.

html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { 
            size: A4; 
            margin: 25mm 15mm; /* Important: Defining margins here */
        }
        body { margin: 0; padding: 0; }
        .content {
            background: #f0f0f0;
            height: 1500px; /* Two pages */
            position: relative;
        }
        .stamp {
            position: absolute;
            right: -10mm; /* Overlap into the margin */
            top: 20mm;
            width: 30mm;
            height: 30mm;
            background: rgba(255, 0, 0, 0.5);
            border: 2px solid red;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div class="content">
        <h1>Page 1 Content</h1>
        <div class="stamp">STAMP (Should bleed)</div>
        <div style="margin-top: 1000px;">
            <h1>Page 2 Content</h1>
        </div>
    </div>
</body>
</html>
"""

def on_finished(ok):
    if ok:
        # Pass 0 margins to QPageLayout
        layout = QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait, QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
        page.printToPdf("test_bleed.pdf", layout)
        QTimer.singleShot(2000, app.quit)

page.loadFinished.connect(on_finished)
page.setHtml(html, QUrl("file:///"))
app.exec()
