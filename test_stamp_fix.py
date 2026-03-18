import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtCore import QUrl, QMarginsF, QTimer

app = QApplication(sys.argv)
page = QWebEnginePage()

# Margin is 25mm. Stamp is right: 10mm.
# Expected: 10mm from right edge.
# Without fix: 25mm (margin) + 10mm (css) = 35mm from edge.
# With fix (margin-right: -25mm): 35mm - 25mm = 10mm from edge.

html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { size: A4; margin: 0; }
        html, body { margin: 0; padding: 0; width: 100%; height: auto; }
        .paper { 
            width: 100%; height: 1000px; padding: 0; margin: 0; 
            display: block; position: relative;
        }
        .stamp {
            position: absolute;
            right: 10mm;
            top: 10mm;
            width: 20mm;
            height: 20mm;
            background: rgba(255, 0, 0, 0.5);
            border: 2px solid red;
            z-index: 100;
        }
        /* Proposed Fix */
        .stamp {
            margin-right: -25mm !important;
            margin-top: -25mm !important;
        }
    </style>
</head>
<body>
    <div class="paper">
        <div class="stamp">STAMP</div>
        <p>Content at top left of content area.</p>
    </div>
</body>
</html>
"""

def on_finished(ok):
    if ok:
        layout = QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait, QMarginsF(25, 25, 25, 25), QPageLayout.Unit.Millimeter)
        page.printToPdf("test_stamp_fix.pdf", layout)
        QTimer.singleShot(2000, app.quit)

page.loadFinished.connect(on_finished)
page.setHtml(html, QUrl("file:///"))
app.exec()
