from PySide6.QtCore import QObject, Slot, QMimeData
from PySide6.QtWidgets import QApplication

class SniperBridge(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    @Slot(str)
    def receive_text(self, text):
        self.main_window._block_clipboard_signal = True # 内部コピー時は監視を一時停止
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.main_window.add_extracted_text(text, is_manual=False)
        finally:
            self.main_window._block_clipboard_signal = False

    @Slot(str)
    def receive_html(self, html):
        """Style SnipeモードからのHTML受信"""
        self.main_window._block_clipboard_signal = True
        try:
            clipboard = QApplication.clipboard()
            mime = QMimeData()
            mime.setHtml(html)
            mime.setText(html)  # プレーンテキストとしても貼付可能
            clipboard.setMimeData(mime)
            self.main_window.add_extracted_html(html)
        finally:
            self.main_window._block_clipboard_signal = False
