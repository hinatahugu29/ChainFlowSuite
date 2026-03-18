import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtCore import QUrl, QMarginsF, QTimer

app = QApplication(sys.argv)
page = QWebEnginePage()

# Goals:
# 1. 0 QPageLayout margins.
# 2. CSS margins via padding and break-height.
# 3. Stamp that can bleed into "margin" area.

html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { size: A4; margin: 0; }
        body { margin: 0; padding: 0; }
        .paper {
            width: 210mm;
            min-height: 297mm;
            position: relative;
            padding-left: 20mm;   /* Left margin */
            padding-right: 20mm;  /* Right margin */
            padding-top: 20mm;    /* Top margin for Page 1 */
            box-sizing: border-box;
            background: #eee;
        }
        .synced-print-break {
            page-break-before: always;
            height: 20mm; /* Top margin for Page 2+ */
            background: yellow; /* Visible for test */
        }
        .stamp {
            position: absolute;
            right: 5mm; /* Bleeds into the 20mm margin */
            top: 10mm;  /* Bleeds into the 20mm margin */
            width: 30mm;
            height: 30mm;
            background: rgba(255, 0, 0, 0.5);
            border: 2px solid red;
        }
    </style>
</head>
<body>
    <div class="paper">
        <div class="stamp">STAMP</div>
        <h1>Page 1</h1>
        <p>I am inside the 20mm margin.</p>
        
        <div class="synced-print-break"></div>
        
        <h1>Page 2</h1>
        <p>I should also be 20mm from top and 20mm from left.</p>
    </div>
</body>
</html>
"""

def on_finished(ok):
    if ok:
        layout = QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait, QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
        page.printToPdf("test_full_fidelity.pdf", layout)
        QTimer.singleShot(2000, app.quit)

page.loadFinished.connect(on_finished)
page.setHtml(html, QUrl("file:///"))
app.exec()
